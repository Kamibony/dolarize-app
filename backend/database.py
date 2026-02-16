import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import firestore as google_firestore
from typing import List, Dict, Any, Optional
import os
import datetime

# Configuration
max_followups = 3

class FirestoreClient:
    def __init__(self, service_account_path: Optional[str] = None):
        """
        Initializes the Firestore client.

        Args:
            service_account_path: Path to the service account JSON key.
                                  If None, it uses the application default credentials.
        """
        if not firebase_admin._apps:
            if service_account_path and os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
            else:
                # Use Application Default Credentials (ADC)
                firebase_admin.initialize_app()

        self.db = firestore.client()

    def save_user(self, user_data: Dict[str, Any]) -> str:
        """
        Saves or updates a user profile in the 'usuarios' collection.

        Expected user_data format:
        {
            "id": "uid_z_firebase_auth",
            "nome": "João Silva",
            "telefone": "+5511999999999",
            "data_criacao": "2026-02-13T14:30:00Z",
            "nivel_acesso": "Nível 1 - Curioso",
            "classificacao_lead": "B - Em maturação",
            "dor_principal": "Busca proteção patrimonial",
            "tags": ["quer_renda", "inseguro_com_corretora"]
        }
        """
        user_id = user_data.get("id")
        if not user_id:
            raise ValueError("User ID is required in user_data")

        doc_ref = self.db.collection("usuarios").document(user_id)
        doc_ref.set(user_data, merge=True)
        return user_id

    def update_user_interaction(self, user_id: str, reset_followup_count: bool = False, increment_followup_count: bool = False) -> None:
        """
        Updates the last_interaction_timestamp for a user.
        Optionally resets or increments the follow_up_count.
        """
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        update_data = {"last_interaction_timestamp": timestamp}

        if reset_followup_count:
            update_data["follow_up_count"] = 0
        elif increment_followup_count:
            update_data["follow_up_count"] = google_firestore.Increment(1)

        self.db.collection("usuarios").document(user_id).set(
            update_data, merge=True
        )

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a user profile by ID."""
        doc_ref = self.db.collection("usuarios").document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None

    def save_chat_interaction(self, interaction_data: Dict[str, Any]) -> str:
        """
        Saves a chat interaction in the 'interacoes_chat' collection.

        Expected interaction_data format:
        {
            "id_usuario": "uid_z_firebase_auth",
            "timestamp": "2026-02-13T14:35:00Z",
            "origem": "web_chat",
            "mensagens": [
                {"role": "user", "content": "É difícil investir em dólar?"},
                {"role": "agent", "content": "Não é difícil. É diferente."}
            ],
            "analise_emocional": "Ansioso",
            "precisa_intervencao_humana": false
        }
        """
        # We allow Firestore to generate the ID for the interaction document
        update_time, doc_ref = self.db.collection("interacoes_chat").add(interaction_data)
        return doc_ref.id

    def get_chat_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves the chat history for a specific user, ordered by timestamp descending."""
        query = (
            self.db.collection("interacoes_chat")
            .where(field_path="id_usuario", op_string="==", value=user_id)
            .order_by("timestamp", direction=google_firestore.Query.DESCENDING)
            .limit(limit)
        )
        docs = query.stream()
        return [doc.to_dict() for doc in docs]

    def save_lesson_progress(self, progress_data: Dict[str, Any]) -> None:
        """
        Saves or updates lesson progress in 'progresso_aulas'.

        Expected progress_data format:
        {
            "id_usuario": "uid_z_firebase_auth",
            "modulo": "Módulo 1",
            "aula": "1.3: Segurança da conta",
            "status": "concluido",
            "resultado_quiz_pontuacao": 80,
            "recomendacao_ai": "Revisar passo do Google Authenticator"
        }
        """
        user_id = progress_data.get("id_usuario")
        modulo = progress_data.get("modulo")
        aula = progress_data.get("aula")

        if not all([user_id, modulo, aula]):
            raise ValueError("id_usuario, modulo, and aula are required for lesson progress")

        collection_ref = self.db.collection("progresso_aulas")
        query = (
            collection_ref
            .where(field_path="id_usuario", op_string="==", value=user_id)
            .where(field_path="modulo", op_string="==", value=modulo)
            .where(field_path="aula", op_string="==", value=aula)
        )
        docs = list(query.stream())

        if docs:
            # Update existing
            doc_ref = docs[0].reference
            doc_ref.set(progress_data, merge=True)
        else:
            # Create new
            collection_ref.add(progress_data)

    def get_lesson_progress(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieves all lesson progress for a user."""
        query = self.db.collection("progresso_aulas").where(field_path="id_usuario", op_string="==", value=user_id)
        docs = query.stream()
        return [doc.to_dict() for doc in docs]

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Retrieves all user profiles."""
        docs = self.db.collection("usuarios").stream()
        users = []
        for doc in docs:
            user = doc.to_dict()
            user["id"] = doc.id
            users.append(user)
        return users

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Calculates and returns the aggregated dashboard statistics.
        """
        users = self.get_all_users()
        total_leads = len(users)

        distribution = {"A": 0, "B": 0, "C": 0}

        for user in users:
            classification = user.get("classificacao_lead", "")
            if isinstance(classification, str):
                if classification.startswith("A"):
                    distribution["A"] += 1
                elif classification.startswith("B"):
                    distribution["B"] += 1
                elif classification.startswith("C"):
                    distribution["C"] += 1
                # If unclassified or other, we might count it as C or separately
                # defaulting to ignoring for distribution if not A/B/C

        conversion_rate_a = (distribution["A"] / total_leads * 100) if total_leads > 0 else 0.0

        return {
            "total_leads": total_leads,
            "conversion_rate_a": round(conversion_rate_a, 1),
            "funnel_distribution": distribution
        }

    def get_users_needing_followup(self, hours_inactive: int = 24) -> List[Dict[str, Any]]:
        """
        Retrieves users who have not interacted within the last 'hours_inactive' hours,
        are not yet fully converted, and have not exceeded the max follow-up count.
        """
        cutoff_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours_inactive)
        cutoff_iso = cutoff_time.isoformat()

        # Query users where last_interaction_timestamp < cutoff_iso
        query = (
            self.db.collection("usuarios")
            .where(field_path="last_interaction_timestamp", op_string="<", value=cutoff_iso)
        )

        docs = query.stream()
        users = []
        for doc in docs:
            user_data = doc.to_dict()
            user_data["id"] = doc.id

            # Anti-Spam Check: Filter by follow_up_count
            follow_up_count = user_data.get("follow_up_count", 0)
            if follow_up_count < max_followups:
                users.append(user_data)

        return users

    def add_knowledge_file(self, file_data: Dict[str, Any]) -> str:
        """
        Saves a knowledge base file record.
        """
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        file_data["created_at"] = timestamp

        update_time, doc_ref = self.db.collection("knowledge_base").add(file_data)
        return doc_ref.id

    def get_knowledge_files(self) -> List[Dict[str, Any]]:
        """Retrieves all active knowledge base files."""
        docs = self.db.collection("knowledge_base").order_by("created_at", direction=google_firestore.Query.DESCENDING).stream()
        files = []
        for doc in docs:
            f = doc.to_dict()
            f["id"] = doc.id
            files.append(f)
        return files

    def delete_knowledge_file(self, file_id: str) -> None:
        """Deletes a knowledge base file record."""
        self.db.collection("knowledge_base").document(file_id).delete()

    def get_knowledge_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single knowledge base file record."""
        doc = self.db.collection("knowledge_base").document(file_id).get()
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None
