from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from agent_core import agent
from database import FirestoreClient
from routers import webhooks
import os
import datetime
import shutil
import tempfile
import google.generativeai as genai

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

def run_lead_qualification(user_id: str, history: List[Dict[str, Any]]):
    """
    Background task to analyze lead qualification and update user profile.
    """
    try:
        analysis = agent.analyze_lead_qualification(history)
        if analysis:
            # Merge ID into analysis to save
            analysis["id"] = user_id
            db.save_user(analysis)
    except Exception as e:
        print(f"Error in background lead qualification: {e}")

@app.get("/")
async def root():
    return {"message": "Dolarize API is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    try:
        # 1. Fetch history
        raw_history = db.get_chat_history(request.user_id, limit=20)

        # 2. Format history for Gemini
        gemini_history = []
        # Firestore returns most recent first, so reverse to get chronological order
        for interaction in reversed(raw_history):
            if "mensagens" in interaction:
                for msg in interaction["mensagens"]:
                    role = "model" if msg["role"] == "agent" else "user"
                    gemini_history.append({
                        "role": role,
                        "parts": [msg["content"]]
                    })

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

        analysis = agent.analyze_lead_qualification(gemini_history)
        current_classification = ""

        if analysis:
            # Merge ID into analysis to save
            analysis["id"] = request.user_id
            db.save_user(analysis)
            current_classification = analysis.get("classificacao_lead", "")
        else:
            # Fallback to existing user data if analysis fails
            user_data = db.get_user(request.user_id)
            if user_data:
                current_classification = user_data.get("classificacao_lead", "")

        # Determine User Tier
        user_tier = "C" # Default / Welcome
        if isinstance(current_classification, str):
            if "A" in current_classification or "Quente" in current_classification or "Qualificado" in current_classification:
                user_tier = "A"
            elif "B" in current_classification or "Morno" in current_classification:
                user_tier = "B"

        return ChatResponse(response=response_text, user_tier=user_tier)
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class FollowUpRequest(BaseModel):
    hours_inactive: int = 24

@app.post("/admin/trigger-followup")
async def trigger_followup(request: FollowUpRequest):
    """
    Triggers the follow-up engine to re-engage inactive leads.
    """
    try:
        users = db.get_users_needing_followup(hours_inactive=request.hours_inactive)
        processed_count = 0

        for user in users:
            user_id = user.get("id")
            if not user_id:
                continue

            # Generate personalized follow-up
            message = agent.generate_followup_message(user)

            # Save interaction
            interaction = {
                "id_usuario": user_id,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "origem": "follow_up_engine",
                "mensagens": [
                    {"role": "agent", "content": message}
                ],
                "analise_emocional": "Neutro",
                "precisa_intervencao_humana": False
            }
            db.save_chat_interaction(interaction)

            # Update last interaction and increment follow-up count to avoid infinite loop
            db.update_user_interaction(user_id, increment_followup_count=True)

            processed_count += 1

        return {"message": f"Follow-up process completed. Processed {processed_count} users."}
    except Exception as e:
        print(f"Error in follow-up endpoint: {e}")
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
        print(f"Error in stats endpoint: {e}")
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
            # 2. Upload to Gemini
            # Determine mime_type if not provided
            mime_type = file.content_type
            if not mime_type:
                 if suffix.lower() == '.pdf': mime_type = 'application/pdf'
                 elif suffix.lower() in ['.txt', '.md']: mime_type = 'text/plain'
                 elif suffix.lower() == '.csv': mime_type = 'text/csv'
                 else: mime_type = 'application/octet-stream' # Fallback

            # Using genai.upload_file directly
            gemini_file = genai.upload_file(path=tmp_path, mime_type=mime_type, display_name=file.filename)

            # 3. Save metadata to Firestore
            file_data = {
                "name": gemini_file.name, # e.g. "files/..."
                "display_name": gemini_file.display_name,
                "uri": gemini_file.uri,
                "mime_type": gemini_file.mime_type,
                "size_bytes": gemini_file.size_bytes,
                # Store state if possible, though it's an enum usually
                "state": str(gemini_file.state.name) if hasattr(gemini_file.state, 'name') else str(gemini_file.state)
            }

            doc_id = db.add_knowledge_file(file_data, file_type=file_type)

            # 4. Refresh Agent
            agent.refresh_knowledge_base()

            return {"id": doc_id, "file": file_data}

        finally:
            # Cleanup temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception as e:
        print(f"Error uploading file: {e}")
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
                print(f"Warning: Failed to delete file from Gemini (might be already deleted): {e}")

        # 3. Delete from Firestore
        db.delete_knowledge_file(file_id)

        # 4. Refresh Agent
        agent.refresh_knowledge_base()

        return {"message": "File deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
