from fastapi import APIRouter, Request, HTTPException, Header, BackgroundTasks, Query
from fastapi.responses import PlainTextResponse
from fastapi.concurrency import run_in_threadpool
from typing import Optional, Dict, Any, List
import hmac
import hashlib
import json
import os
import logging
import datetime
from agent_core import agent
from database import FirestoreClient
from services.meta_service import meta_service
import stripe

# Initialize Router
router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize Firestore
# Safe to call multiple times due to check in database.py
db = FirestoreClient()

META_VERIFY_TOKEN = os.environ.get("META_VERIFY_TOKEN")
META_APP_SECRET = os.environ.get("META_APP_SECRET")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")

if STRIPE_API_KEY:
    stripe.api_key = STRIPE_API_KEY

async def verify_signature(request: Request) -> bytes:
    """
    Verifies the X-Hub-Signature-256 header.
    Returns the raw body bytes if verification passes.
    """
    body = await request.body()

    if not META_APP_SECRET:
        logger.warning("META_APP_SECRET not set. Skipping signature verification (INSECURE).")
        return body

    signature_header = request.headers.get("X-Hub-Signature-256")
    if not signature_header:
        # Meta webhooks always include this header.
        raise HTTPException(status_code=403, detail="Missing X-Hub-Signature-256 header")

    # Calculate expected signature
    expected_signature = "sha256=" + hmac.new(
        key=META_APP_SECRET.encode('utf-8'),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature_header, expected_signature):
        logger.error(f"Invalid signature. Expected: {expected_signature}, Got: {signature_header}")
        raise HTTPException(status_code=403, detail="Invalid signature")

    return body

@router.get("/webhook/meta")
async def verify_webhook(
    mode: str = Query(..., alias="hub.mode"),
    token: str = Query(..., alias="hub.verify_token"),
    challenge: str = Query(..., alias="hub.challenge")
):
    """
    Verifies the webhook subscription for Meta.
    Returns the challenge integer as plain text.
    """
    if mode == "subscribe" and token == META_VERIFY_TOKEN:
        logger.info("Webhook verified successfully.")
        return PlainTextResponse(content=challenge)

    logger.warning("Webhook verification failed. Token mismatch.")
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/webhook/meta")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives webhook events from Meta (WhatsApp/Instagram).
    """
    # Verify Signature and get body
    body = await verify_signature(request)

    # Parse Payload
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Delegate to background task
    background_tasks.add_task(process_meta_payload, payload)

    return {"status": "ok"}

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives webhook events from Stripe.
    """
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")

    if not STRIPE_WEBHOOK_SECRET:
        logger.warning("STRIPE_WEBHOOK_SECRET not set. Skipping verification (INSECURE - DEV ONLY).")
        # In prod, raise error
        try:
             event = json.loads(payload)
        except:
             raise HTTPException(status_code=400, detail="Invalid JSON")
    else:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            # Invalid payload
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            raise HTTPException(status_code=400, detail="Invalid signature")

    # Delegate to background task
    background_tasks.add_task(process_stripe_event, event)

    return {"status": "success"}

async def process_stripe_event(event: Dict[str, Any]):
    """
    Processes Stripe events asynchronously.
    """
    try:
        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})

        if event_type == "checkout.session.completed":
            logger.info("Processing checkout.session.completed")

            # Extract customer details
            customer_email = data.get("customer_details", {}).get("email")
            customer_name = data.get("customer_details", {}).get("name")

            # Prioritize client_reference_id (standard) or metadata.user_id (custom)
            client_reference_id = data.get("client_reference_id")
            metadata = data.get("metadata", {})
            user_id = client_reference_id or metadata.get("user_id")

            if customer_email or user_id:
                timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

                # Update logic
                updated = False

                # 1. Try updating by ID if provided (MOST RELIABLE)
                if user_id:
                     user = db.get_user(user_id)
                     if user:
                         db.save_user({
                             "id": user_id,
                             "status": "Aluno",
                             "payment_date": timestamp,
                             "payment_provider": "stripe"
                         })
                         updated = True
                         logger.info(f"User {user_id} upgraded to Aluno via ID.")
                     else:
                         logger.warning(f"Payment received with user_id {user_id} but user not found in DB.")

                # 2. If not updated by ID, try by Email (FALLBACK)
                if not updated and customer_email:
                    updated = db.update_user_status_by_email(
                        email=customer_email,
                        status="Aluno",
                        additional_data={
                            "payment_date": timestamp,
                            "payment_provider": "stripe",
                            "nome": customer_name # Update name if available
                        }
                    )
                    if updated:
                        logger.info(f"User {customer_email} upgraded to Aluno via Email.")
                    else:
                        logger.warning(f"Payment received for {customer_email} but user not found in DB.")
                        # Optional: Create a new user placeholder?
                        # For now, we log it.

    except Exception as e:
        logger.error(f"Error processing Stripe event: {e}", exc_info=True)


async def process_meta_payload(payload: Dict[str, Any]):
    """
    Processes the webhook payload asynchronously.
    """
    try:
        # logger.info(f"Processing payload: {json.dumps(payload, indent=2)}") # Debug logging

        object_type = payload.get("object")
        entry = payload.get("entry", [])

        if not entry:
            return

        for event in entry:
            # WhatsApp Logic
            if object_type == "whatsapp_business_account":
                changes = event.get("changes", [])
                for change in changes:
                    value = change.get("value", {})
                    messages = value.get("messages", [])

                    if not messages:
                        continue

                    for msg in messages:
                        if msg.get("type") != "text":
                            logger.info("Ignoring non-text message (WhatsApp).")
                            continue

                        user_id = msg.get("from") # Phone number
                        text_body = msg.get("text", {}).get("body")

                        if user_id and text_body:
                            await handle_message(user_id, text_body, "whatsapp")

            # Instagram Logic
            elif object_type == "instagram":
                messaging = event.get("messaging", [])
                for msg in messaging:
                    user_id = msg.get("sender", {}).get("id") # IGSID
                    message_obj = msg.get("message", {})
                    text_body = message_obj.get("text")

                    if user_id and text_body:
                         await handle_message(user_id, text_body, "instagram")

            # Generic Page Logic (Messenger or unexpected structure)
            elif object_type == "page":
                 messaging = event.get("messaging", [])
                 for msg in messaging:
                     user_id = msg.get("sender", {}).get("id")
                     message_obj = msg.get("message", {})
                     text_body = message_obj.get("text")

                     if user_id and text_body:
                         await handle_message(user_id, text_body, "facebook_page")

    except Exception as e:
        logger.error(f"Error processing webhook payload: {e}")

async def handle_message(user_id: str, text: str, platform: str):
    """
    Core logic to handle the incoming message.
    """
    try:
        logger.info(f"Handling message from {user_id} on {platform}: {text}")

        # 1. Fetch History
        # We use the user_id (phone or IGSID) as the Firestore document ID.
        # This assumes phone numbers are unique enough (they are) and IGSIDs are unique (they are).
        raw_history = await run_in_threadpool(db.get_chat_history, user_id, limit=20)

        # Convert to Gemini format
        gemini_history = agent.format_history(raw_history)

        # 2. Generate Response
        # Note: 'gemini_history' might be empty for new users.
        # AgentCore handles system prompt injection (via system_instruction or fallback).
        # We run this in a threadpool as it is a blocking sync call.
        response_text = await run_in_threadpool(agent.generate_response, text, gemini_history)

        # 3. Save Interaction (User Message + Agent Response)
        new_interaction = {
            "id_usuario": user_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "origem": platform,
            "mensagens": [
                {"role": "user", "content": text},
                {"role": "agent", "content": response_text}
            ],
            "analise_emocional": "Neutro", # Placeholder
            "precisa_intervencao_humana": False
        }
        await run_in_threadpool(db.save_chat_interaction, new_interaction)

        # 4. Update User Interaction State
        await run_in_threadpool(db.update_user_interaction, user_id, reset_followup_count=True)

        # 5. Send Response via Meta Graph API
        if platform == "whatsapp":
            await meta_service.send_whatsapp_message(user_id, response_text)
        elif platform == "instagram" or platform == "facebook_page":
            await meta_service.send_instagram_message(user_id, response_text)

        # 6. Analyze Lead Qualification (Async)
        # We append the latest interaction to history for analysis
        gemini_history.append({"role": "user", "parts": [text]})
        gemini_history.append({"role": "model", "parts": [response_text]})

        analysis = await run_in_threadpool(agent.analyze_lead_qualification, gemini_history)
        if analysis:
            analysis["id"] = user_id
            # Save user profile (merges with existing)
            await run_in_threadpool(db.save_user, analysis)

    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
