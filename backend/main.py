from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from agent_core import agent
from database import FirestoreClient
import os
import datetime

app = FastAPI(title="Dolarize API", version="1.0.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Firestore
db = FirestoreClient()

class ChatRequest(BaseModel):
    message: str
    user_id: str

class ChatResponse(BaseModel):
    response: str

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

        # Run analysis in background
        background_tasks.add_task(run_lead_qualification, request.user_id, gemini_history)

        return ChatResponse(response=response_text)
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

@app.get("/admin/users/{user_id}/history", response_model=List[Dict[str, Any]])
async def get_user_history(user_id: str):
    try:
        return db.get_chat_history(user_id, limit=50)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
