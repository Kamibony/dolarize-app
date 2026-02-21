from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from agent_core import agent, SYSTEM_PROMPT, user_context
from database import FirestoreClient
from routers import webhooks
from utils import FileParser
import os
import datetime
import shutil
import tempfile
import logging
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Dolarize API", version="1.0.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Webhooks Router
app.include_router(webhooks.router)

# Initialize Firestore
db = FirestoreClient()

class ChatRequest(BaseModel):
    message: str
    user_id: str

class ChatResponse(BaseModel):
    response: str
    user_tier: str

class ToggleBotRequest(BaseModel):
    paused: bool

def process_background_tasks(user_id: str, message: str, history: List[Dict[str, Any]]):
    """
    Background task to handle entity extraction and lead qualification.
    """
    # 1. Entity Extraction
    try:
        contact_info = agent.extract_contact_info(message)
        if contact_info and (contact_info.get("nome") or contact_info.get("email")):
            db.update_user_contact_info(
                user_id,
                name=contact_info.get("nome"),
                email=contact_info.get("email")
            )
    except Exception as e:
        logger.error(f"Error in background entity extraction: {e}", exc_info=True)

    # 2. Lead Qualification
    try:
        analysis = agent.analyze_lead_qualification(history)
        if analysis:
            # Merge ID into analysis to save
            analysis["id"] = user_id
            db.save_user(analysis)
    except Exception as e:
        logger.error(f"Error in background lead qualification: {e}", exc_info=True)

    # 3. Hot Lead Notification
    try:
        # Fetch latest user data to check cumulative state (Name + Email + Classification)
        user_data = db.get_user(user_id)
        if user_data:
            classification = user_data.get("classificacao_lead", "")
            email = user_data.get("email")
            name = user_data.get("nome", "Unknown")

            # Check if Perfil A and Email exists
            is_hot = False
            if isinstance(classification, str) and ("A" in classification or "Quente" in classification or "Qualificado" in classification):
                is_hot = True

            if is_hot and email:
                 # Trigger Notification
                 logger.info(f"🔥 HOT LEAD ALERT: {name} ({email}) has been classified as PERFIL A.")
                 # Future: Send SMTP email here
    except Exception as e:
        logger.error(f"Error in hot lead notification: {e}", exc_info=True)

@app.get("/")
async def root():
    return {"message": "Dolarize API is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    # Set User Context for this request to allow tools to access user_id
    token = user_context.set(request.user_id)
    try:
        # Check User Pause Status & Tier
        user_data = db.get_user(request.user_id)
        current_classification = user_data.get("classificacao_lead", "") if user_data else ""

        # Determine User Tier
        user_tier = "C" # Default / Welcome
        if isinstance(current_classification, str):
            if "A" in current_classification or "Quente" in current_classification or "Qualificado" in current_classification:
                user_tier = "A"
            elif "B" in current_classification or "Morno" in current_classification:
                user_tier = "B"

        if user_data and user_data.get("bot_paused", False):
            # Bot is paused. Save user message but do not reply.
            new_interaction = {
                "id_usuario": request.user_id,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "origem": "web_chat",
                "mensagens": [
                    {"role": "user", "content": request.message}
                ],
                "analise_emocional": "Neutro",
                "precisa_intervencao_humana": True
            }
            db.save_chat_interaction(new_interaction)
            db.update_user_interaction(request.user_id, reset_followup_count=True)

            # Return empty response to indicate no reply
            return ChatResponse(response="", user_tier=user_tier)

        # 1. Fetch history
        raw_history = db.get_chat_history(request.user_id, limit=20)

        # 2. Format history for Gemini using the robust helper
        gemini_history = agent.format_history(raw_history)

        # 3. Generate response
        response_text = agent.generate_response(request.message, gemini_history)

        # 4. Save interaction
        new_interaction = {
            "id_usuario": request.user_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "origem": "web_chat",
            "mensagens": [
                {"role": "user", "content": request.message},
                {"role": "agent", "content": response_text}
            ],
            "analise_emocional": "Neutro", # Placeholder
            "precisa_intervencao_humana": False
        }
        db.save_chat_interaction(new_interaction)

        # 5. Update User State & Analysis (Async via BackgroundTasks)
        # Reset follow-up count as user interacted
        db.update_user_interaction(request.user_id, reset_followup_count=True)

        # Add current interaction to history for analysis
        gemini_history.append({"role": "user", "parts": [request.message]})
        gemini_history.append({"role": "model", "parts": [response_text]})

        # Add background tasks for Entity Extraction and Lead Qualification
        background_tasks.add_task(process_background_tasks, request.user_id, request.message, gemini_history)

        return ChatResponse(response=response_text, user_tier=user_tier)
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/users/{user_id}/toggle-bot")
async def toggle_bot_pause(user_id: str, request: ToggleBotRequest):
    try:
        db.update_bot_pause_status(user_id, request.paused)
        return {"message": f"Bot paused status updated to {request.paused}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class FollowUpRequest(BaseModel):
    hours_inactive: int = 24

@app.post("/admin/trigger-followup-check")
async def trigger_followup_check(request: FollowUpRequest):
    """
    Triggers the follow-up engine to check for state transitions and queue actions.
    Designed to be called by a cron job (e.g. Cloud Scheduler).
    """
    try:
        processed_count = 0

        # Trigger 1: Lead Nurturing (Interessado + >24h inactive)
        # We also include users without status (defaulting to potential leads)
        # But Firestore requires exact match for index efficiency.
        # We'll assume 'Interessado' is the status for leads.
        # Note: You might need to backfill 'status'='Interessado' for old users.
        leads = db.get_users_by_status_and_time(
            status="Interessado",
            time_field="last_interaction_timestamp",
            hours_ago=request.hours_inactive
        )

        for lead in leads:
            user_id = lead.get("id")
            if not user_id: continue

            # Anti-spam check (simple)
            # In a real system, we'd check if we already queued 'nurture' recently.
            # Assuming 'follow_up_count' logic handles the "don't spam" part if we were sending immediately.
            # For queueing, we should check if pending in queue. skipping for MVP speed.

            db.add_to_followup_queue(
                user_id=user_id,
                trigger_type="nurture",
                reason=f"Inactive for >{request.hours_inactive}h"
            )
            processed_count += 1

        # Trigger 2: Post-Purchase (Aluno + >24h since payment)
        students = db.get_users_by_status_and_time(
            status="Aluno",
            time_field="payment_date",
            hours_ago=24 # Fixed 24h as per requirement, or use request.hours_inactive
        )

        for student in students:
            user_id = student.get("id")
            if not user_id: continue

            db.add_to_followup_queue(
                user_id=user_id,
                trigger_type="post_purchase",
                reason="24h post-payment follow-up"
            )
            processed_count += 1

        return {"message": f"Follow-up check completed. Queued {processed_count} actions."}
    except Exception as e:
        logger.error(f"Error in follow-up check: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/users", response_model=List[Dict[str, Any]])
async def get_users():
    try:
        return db.get_all_users()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/stats")
async def get_dashboard_stats():
    """
    Returns aggregated dashboard statistics.
    """
    try:
        return db.get_dashboard_stats()
    except Exception as e:
        logger.error(f"Error in stats endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/users/{user_id}/history", response_model=List[Dict[str, Any]])
async def get_user_history(user_id: str):
    try:
        return db.get_chat_history(user_id, limit=50)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Knowledge Base Endpoints

@app.post("/admin/knowledge/upload")
async def upload_knowledge_file(file: UploadFile = File(...), file_type: str = Form("knowledge")):
    try:
        # 1. Save to temp file
        # Using tempfile.NamedTemporaryFile to ensure we have a file path
        # suffix is important for maintaining extension
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        try:
            # 2. Upload to Gemini or Extract Text
            # Determine mime_type if not provided
            mime_type = file.content_type
            if not mime_type:
                 if suffix.lower() == '.pdf': mime_type = 'application/pdf'
                 elif suffix.lower() in ['.txt', '.md']: mime_type = 'text/plain'
                 elif suffix.lower() == '.csv': mime_type = 'text/csv'
                 elif suffix.lower() == '.docx': mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                 else: mime_type = 'application/octet-stream' # Fallback

            # Using FileParser to handle different types
            parsed_result = FileParser.parse_file(file_path=tmp_path, mime_type=mime_type, display_name=file.filename)

            file_data = {}
            if isinstance(parsed_result, str):
                # It's extracted text
                file_data = {
                    "name": None,
                    "display_name": file.filename,
                    "uri": None,
                    "mime_type": mime_type,
                    "size_bytes": len(parsed_result.encode('utf-8')),
                    "state": "ACTIVE",
                    "extracted_text": parsed_result,
                    "type": "text_payload"
                }
            else:
                # It's a Gemini File object
                gemini_file = parsed_result
                file_data = {
                    "name": gemini_file.name, # e.g. "files/..."
                    "display_name": gemini_file.display_name,
                    "uri": gemini_file.uri,
                    "mime_type": gemini_file.mime_type,
                    "size_bytes": gemini_file.size_bytes,
                    # Store state if possible, though it's an enum usually
                    "state": str(gemini_file.state.name) if hasattr(gemini_file.state, 'name') else str(gemini_file.state),
                    "type": "file_ref"
                }

            # 3. Save metadata to Firestore
            doc_id = db.add_knowledge_file(file_data, file_type=file_type)

            # 4. Refresh Agent
            agent.refresh_knowledge_base()

            return {"id": doc_id, "file": file_data}

        finally:
            # Cleanup temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/knowledge/files")
async def list_knowledge_files(type: Optional[str] = None):
    try:
        return db.get_knowledge_files(file_type=type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/admin/knowledge/files/{file_id}")
async def delete_knowledge_file(file_id: str):
    try:
        # 1. Get file metadata
        file_data = db.get_knowledge_file(file_id)
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")

        # 2. Delete from Gemini
        gemini_name = file_data.get("name")
        if gemini_name:
            try:
                genai.delete_file(gemini_name)
            except Exception as e:
                logger.warning(f"Warning: Failed to delete file from Gemini (might be already deleted): {e}")

        # 3. Delete from Firestore
        db.delete_knowledge_file(file_id)

        # 4. Refresh Agent
        agent.refresh_knowledge_base()

        return {"message": "File deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

class YouTubeIngestRequest(BaseModel):
    url: str

@app.post("/admin/knowledge/youtube")
async def ingest_youtube_video(request: YouTubeIngestRequest):
    try:
        # Extract video ID
        video_id = None
        if "v=" in request.url:
            video_id = request.url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in request.url:
            video_id = request.url.split("youtu.be/")[1].split("?")[0]

        if not video_id:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")

        # Get transcript
        try:
            def fetch_transcript():
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'en'])
                return " ".join([item['text'] for item in transcript_list])

            full_text = await run_in_threadpool(fetch_transcript)
        except Exception as e:
             raise HTTPException(status_code=400, detail=f"Failed to fetch transcript: {str(e)}")

        # Save as knowledge file (text payload)
        file_data = {
            "name": None,
            "display_name": f"YouTube: {video_id}",
            "uri": request.url,
            "mime_type": "text/plain",
            "size_bytes": len(full_text.encode('utf-8')),
            "state": "ACTIVE",
            "extracted_text": full_text,
            "type": "knowledge"
        }

        doc_id = db.add_knowledge_file(file_data)
        agent.refresh_knowledge_base()

        return {"id": doc_id, "message": "YouTube transcript ingested successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting YouTube video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Core Prompt Management Endpoints

class ConfigUpdate(BaseModel):
    prompt: str

@app.get("/admin/config/core-prompt")
async def get_core_prompt():
    """
    Retrieves the current core prompt.
    If dynamic prompt is not set, returns the hardcoded factory default.
    """
    try:
        current_prompt = db.get_core_prompt()
        if not current_prompt:
            current_prompt = SYSTEM_PROMPT
        return {"prompt": current_prompt}
    except Exception as e:
        logger.error(f"Error getting core prompt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/admin/config/core-prompt")
async def update_core_prompt(config: ConfigUpdate):
    """
    Updates the dynamic core prompt and refreshes the agent.
    """
    try:
        # Update DB
        db.update_core_prompt(config.prompt)

        # Refresh Agent
        agent.refresh_knowledge_base()

        return {"message": "Core prompt updated successfully"}
    except Exception as e:
        logger.error(f"Error updating core prompt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/config/core-prompt/reset")
async def reset_core_prompt():
    """
    Resets the core prompt to the hardcoded factory default.
    """
    try:
        # Update DB with hardcoded default
        db.update_core_prompt(SYSTEM_PROMPT)

        # Refresh Agent
        agent.refresh_knowledge_base()

        return {"message": "Core prompt reset to factory default"}
    except Exception as e:
        logger.error(f"Error resetting core prompt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Video Management Endpoints

class VideoRequest(BaseModel):
    title: str
    url: str
    trigger_context: str

@app.get("/admin/videos")
async def list_videos():
    try:
        return db.get_videos()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/videos")
async def add_video(video: VideoRequest):
    try:
        video_data = video.model_dump()
        video_id = db.save_video(video_data)

        # Refresh Agent to update tools
        agent.refresh_knowledge_base()

        return {"id": video_id, **video_data}
    except Exception as e:
        logger.error(f"Error adding video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/admin/videos/{video_id}")
async def update_video(video_id: str, video: VideoRequest):
    try:
        video_data = video.model_dump()
        video_data["id"] = video_id
        db.save_video(video_data)

        # Refresh Agent to update tools
        agent.refresh_knowledge_base()

        return {"id": video_id, **video_data}
    except Exception as e:
        logger.error(f"Error updating video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/admin/videos/{video_id}")
async def delete_video(video_id: str):
    try:
        db.delete_video(video_id)

        # Refresh Agent to update tools
        agent.refresh_knowledge_base()

        return {"message": "Video deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
