import os
import sys
import logging
import google.generativeai as genai
from typing import List, Dict, Optional, Any
from database import FirestoreClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the Base System Prompt for "André Digital"
SYSTEM_PROMPT = """
1. IDENTIDADE E MISSÃO (CAP. 5)
Você é o "André Digital", a Extensão Oficial da Autoridade e do Método Dólarize 2.0.
Sua missão: Conduzir com clareza, segurança e estrutura. Regular a ansiedade do aluno/lead. Proteger a sequência de aprendizado.
Você NÃO é um assistente genérico. Você é um Mentor Estruturador.

2. PERSONALIDADE E TOM DE VOZ (CAP. 5)
- Tom: Calmo, didático, direto, seguro e objetivo.
- Estilo: Frases curtas. Sem emojis exagerados. Sem promessas vazias.
- Postura: Autoridade tranquila. "Conduzir mais. Explicar menos."
- Mantra: "Segurança não é promessa. Segurança é estrutura."

3. LIMITES ABSOLUTOS (HARD RULES - O QUE VOCÊ NUNCA FAZ)
- JAMAIS dê opinião sobre preço de ativos ou faça previsões de mercado (ex: "o dólar vai subir?").
- JAMAIS incentive "trade", day-trade ou operações de curto prazo.
- JAMAIS negocie o valor do método ou ofereça descontos/atalhos.
- JAMAIS encerre uma resposta sem um PRÓXIMO PASSO claro (uma pergunta ou ação).
- JAMAIS prometa lucro ou retorno financeiro garantido.

4. ÁRVORE DE DECISÃO INTERNA (CAP. 7 - SIGA ESTA ORDEM)
Ao receber uma mensagem, classifique a intenção e aplique a lógica:

   A. BLOQUEIO (RISCO/TRADE/PREVISÃO):
      Se o usuário pedir previsão, dica de trade ou atalho:
      -> Bloqueie imediatamente. Eduque sobre o método.
      -> Ex: "O Dólarize não faz previsões. Ensinamos estrutura para você não depender de notícias."

   B. SUPORTE TÉCNICO / TRAVAMENTO:
      Se o usuário relatar erro, problema de acesso ou "travamento":
      -> Peça detalhes ou um print. Acalme.
      -> Ex: "Para te ajudar, me envie um print do erro. Vamos resolver isso juntos."

   C. ALUNO (DÚVIDA / ANSIEDADE):
      Se for aluno com dúvida ou ansiedade:
      -> Valide a dúvida, reforce que o processo vence a pressa, e instrua.
      -> Redirecione para a aula específica se for algo técnico avançado.

   D. LEAD (INTERESSE / QUALIFICAÇÃO - CAP. 8):
      Se demonstrar interesse no método ou perguntar preço:
      -> NÃO FALAR PREÇO AINDA.
      -> INICIAR QUALIFICAÇÃO (Fazer uma pergunta por vez):
         1. Dor: "O que mais te incomoda hoje no seu financeiro?"
         2. Maturidade: "Você já investe ou está começando do zero?"
         3. Compromisso: "Você busca informação solta ou um método estruturado?"
      -> Só avance para oferta após entender o momento dele.

   E. FALLBACK (NÃO ENTENDEU):
      -> Faça uma pergunta de condução para esclarecer.
      -> Ex: "Não entendi bem. Você se refere à proteção ou aos investimentos?"

5. ESTRUTURA DE RESPOSTA OBRIGATÓRIA (CAP. 6)
Todas as suas respostas devem seguir este template de 4 camadas:
1. VALIDAÇÃO BREVE: Acolha a mensagem ("Entendi sua dúvida...", "Faz sentido...").
2. REFORÇO DE MÉTODO: Lembre que a estrutura vem antes do risco ("No Dólarize, priorizamos a base...").
3. INSTRUÇÃO/DIREÇÃO: A resposta objetiva ou a recusa educada.
4. PRÓXIMO PASSO: A pergunta ou ação final para manter a condução ("Vamos começar por...?", "Me diga...").

6. BASE DE CONHECIMENTO (DYNAMIC RAG)
- Baseie suas respostas técnicas EXCLUSIVAMENTE nos arquivos de documentos fornecidos.
- Se a resposta não estiver nos documentos, declare que precisa verificar a informação e não alucine.
- Use as informações dos arquivos para enriquecer suas explicações, mantendo sempre o tom do André Digital.

7. EXEMPLOS DE COMPORTAMENTO
- Usuário: "Qual a próxima cripto que vai explodir?"
  André Digital: "Entendo sua busca por oportunidade. Mas o Dólarize não trabalha com apostas ou previsões. Ensinamos a construir patrimônio sólido. Você busca aventura ou estrutura?"

- Usuário: "Quanto custa o curso?"
  André Digital: "O investimento varia conforme o acompanhamento que você precisa. Antes de falar de valores, preciso entender seu momento. Hoje, você já tem alguma reserva em dólar ou vai começar do zero?"
"""

def initialize_genai() -> bool:
    """
    Initializes the Google Generative AI client with robust error handling and telemetry.
    Returns True if initialization was successful, False otherwise.
    """
    raw_key = os.environ.get("GOOGLE_API_KEY")

    if not raw_key:
        logger.error("GOOGLE_API_KEY environment variable is not set.")
        return False

    # Safe Telemetry
    key_length = len(raw_key)
    logger.info(f"Read GOOGLE_API_KEY with length: {key_length}")

    if key_length < 30: # Heuristic: API keys are usually longer
        logger.warning(f"GOOGLE_API_KEY seems suspiciously short ({key_length} chars).")

    # Masking for safe logging
    if key_length > 8:
        masked_key = f"{raw_key[:4]}...{raw_key[-4:]}"
    else:
        masked_key = "***" # Too short to mask safely

    logger.info(f"GOOGLE_API_KEY (masked): {masked_key}")

    # Check for invisible characters
    if any(char in raw_key for char in ['\n', '\r', '\t', ' ']):
        logger.warning("GOOGLE_API_KEY contains whitespace characters. Proceeding to sanitize.")

    # Defensive Sanitization: Remove whitespace AND quotes (single/double), then whitespace again
    sanitized_key = raw_key.strip().strip('"').strip("'").strip()

    if sanitized_key != raw_key:
        logger.info(f"Sanitized GOOGLE_API_KEY. Length changed from {len(raw_key)} to {len(sanitized_key)} (Quotes/Whitespace removed).")

    try:
        genai.configure(api_key=sanitized_key)
        # Verify configuration by listing models (lightweight check) or just assume success if no error
        # Note: list_models might require network and permission, so we might skip it to avoid startup latency/errors
        # relying on the fact that configure() sets the global state.
        logger.info("Google Generative AI configured successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to configure Google Generative AI: {e}")
        return False

# Initialize at module level, capturing success status
is_genai_configured = initialize_genai()

class AgentCore:
    def __init__(self):
        self.db = None
        self.model = None

        try:
            self.db = FirestoreClient()
        except Exception as e:
            logger.error(f"Failed to initialize FirestoreClient in AgentCore: {e}")

        if is_genai_configured:
            # Initialize with knowledge base if possible, otherwise default
            self.refresh_knowledge_base()
            if self.model is None:
                 # Fallback if refresh failed completely (shouldn't happen as it has try/except)
                 self.model = genai.GenerativeModel(
                    model_name='gemini-2.5-flash',
                    system_instruction=SYSTEM_PROMPT
                )
        else:
            self.model = None
            logger.error("AgentCore initialized without a valid GenAI configuration.")

    def refresh_knowledge_base(self):
        """
        Refreshes the knowledge base by fetching active files and re-initializing the model.
        """
        if not is_genai_configured:
            return

        active_files = []
        if self.db:
            try:
                # Get list of file records from Firestore
                file_records = self.db.get_knowledge_files()
                for record in file_records:
                    file_name = record.get("name") # This should be the Gemini file name like 'files/xyz'
                    if file_name:
                         # We need to retrieve the actual file object handle from GenAI or pass the name
                         # For system_instruction, passing the file object (retrieved via get_file) is best.
                         try:
                             # Note: get_file returns a File object.
                             # If we do this too often, it might be slow.
                             # Ideally we should cache this or only do it on explicit refresh.
                             file_obj = genai.get_file(file_name)
                             active_files.append(file_obj)
                         except Exception as e:
                             logger.error(f"Error retrieving file {file_name} from Gemini: {e}")
            except Exception as e:
                logger.error(f"Error fetching knowledge files from DB: {e}")

        logger.info(f"Initializing Agent with {len(active_files)} knowledge base files.")

        # Construct system instruction
        # We pass the text prompt first, then the files.
        system_instruction_parts = [SYSTEM_PROMPT]
        system_instruction_parts.extend(active_files)

        try:
            self.model = genai.GenerativeModel(
                model_name='gemini-2.5-flash',
                system_instruction=system_instruction_parts
            )
        except Exception as e:
             logger.error(f"Error initializing GenerativeModel with knowledge base: {e}")
             # Fallback to text only
             self.model = genai.GenerativeModel(
                model_name='gemini-2.5-flash',
                system_instruction=SYSTEM_PROMPT
            )

    def start_chat(self, history: Optional[List[Dict[str, str]]] = None):
        """
        Starts a chat session.
        """
        if self.model is None:
            logger.error("Attempted to start chat without initialized model.")
            raise RuntimeError("AI Model not initialized.")

        if history is None:
            history = []
        return self.model.start_chat(history=history)

    def generate_response(self, user_message: str, history: List[Dict[str, str]] = []) -> str:
        """
        Generates a response from the agent.

        Args:
            user_message: The latest message from the user.
            history: The conversation history (list of dicts with 'role' and 'parts').

        Returns:
            The agent's text response.
        """
        if not is_genai_configured or self.model is None:
            logger.error("generate_response called but GenAI is not configured.")
            return "Erro: O sistema de IA não está disponível no momento (Chave de API inválida ou ausente)."

        try:
            # Create a chat session with the provided history
            chat = self.model.start_chat(history=history)
            response = chat.send_message(user_message)
            return response.text
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Desculpe, vamos com calma. Ocorreu um erro ao processar sua mensagem."

    @staticmethod
    def format_history(raw_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Helper to convert Firestore history to Gemini history format.
        """
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
        return gemini_history

    def analyze_lead_qualification(self, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Analyzes the chat history to extract qualification metrics.
        Returns a dictionary with extracted fields.
        """
        if not is_genai_configured or self.model is None:
            return {}

        analysis_prompt = """
        ANÁLISE DE LEAD - INTERNO
        Com base no histórico da conversa acima, extraia as seguintes informações sobre o usuário:
        1. Dor Principal (O que mais incomoda?)
        2. Maturidade (Iniciante, Já investe, Avançado?)
        3. Compromisso (Busca método ou apenas curiosidade?)
        4. Classificação ("Perfil A (Qualificado/Quente)", "Perfil B (Morno/Em educação)", ou "Perfil C (Frio/Curioso)")

        Responda APENAS em formato JSON:
        {
            "dor_principal": "...",
            "maturidade": "...",
            "compromisso": "...",
            "classificacao_lead": "..."
        }
        Se não houver informação suficiente para algum campo, preencha com null.
        """

        try:
            # We create a new chat just for analysis to not pollute the main context
            # or simply send the whole history as a prompt.
            # Sending history as context is easier.

            # Construct the full prompt
            full_prompt = "Histórico da conversa:\n"
            for msg in history:
                role = "Usuário" if msg["role"] == "user" else "André"
                content = msg["parts"][0] if isinstance(msg["parts"], list) else msg["parts"]
                full_prompt += f"{role}: {content}\n"

            full_prompt += f"\n{analysis_prompt}"

            response = self.model.generate_content(full_prompt)

            # Parse JSON from response
            import json
            import re

            text = response.text
            # Extract JSON block if wrapped in markdown code blocks
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
            else:
                # Try to parse the whole text if no code block
                return json.loads(text)

        except Exception as e:
            logger.error(f"Error analyzing lead: {e}")
            return {}

    def generate_followup_message(self, user_profile: Dict[str, Any]) -> str:
        """
        Generates a follow-up message for a user based on their profile.
        """
        if not is_genai_configured or self.model is None:
            return "Olá! Como estão seus estudos sobre dolarização?"

        name = user_profile.get("nome", "Investidor")
        pain = user_profile.get("dor_principal", "a instabilidade do real")
        maturity = user_profile.get("maturidade", "iniciante")

        prompt = f"""
        Você é André Digital. O usuário {name} não interage há algum tempo.
        Perfil:
        - Dor: {pain}
        - Maturidade: {maturity}

        Gere uma mensagem curta de follow-up (máximo 2 frases) para reengajar este usuário.
        Lembre-se:
        1. Mostre que você lembra da dor dele.
        2. Não seja insistente/chato. Seja um mentor preocupado com o progresso.
        3. Termine com uma pergunta fácil de responder.

        Exemplo: "Olá [Nome], pensando naquela sua dúvida sobre [Dor], conseguiu avançar? O mercado não espera."
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating follow-up: {e}")
            return "Olá! Gostaria de retomar nossa conversa sobre sua proteção patrimonial?"

agent = AgentCore()
