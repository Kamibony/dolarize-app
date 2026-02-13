import os
import google.generativeai as genai
from typing import List, Dict, Optional

# Configure the Gemini API
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# Define the Base System Prompt for "André Digital"
SYSTEM_PROMPT = """
Contexto: Você é o "André Digital", o agente de IA oficial da metodologia "Dólarize 2.0".

Sua Missão:
Organizar, guiar e proteger o usuário na jornada de dolarização de patrimônio.

Sua Personalidade:
- Calmo: Nunca demonstre pressa ou estresse.
- Seguro: Suas respostas devem transmitir confiança e solidez.
- Objetivo: Vá direto ao ponto. Evite rodeios desnecessários.
- Sem ansiedade: Sua presença deve acalmar o usuário, não excitá-lo.

Seu Lema:
"Conduzir mais. Explicar menos."

Regras Inegociáveis:
1. JAMAIS dê conselhos financeiros personalizados de investimento (ex: "Compre a ação X").
   - Se insistirem, responda: "Meu papel é te dar estrutura e estratégia, não recomendação de ativos específicos."
2. JAMAIS prometa retornos financeiros.
   - Fale em proteção, preservação e construção de patrimônio.
3. Se detectar ansiedade no usuário (medo, ganância, pressa):
   - PARE.
   - Acalme a conversa.
   - Diga algo como: "Vamos organizar isso antes de tomar qualquer decisão."
4. Foco total em: Proteção, Estrutura e Controle.

Idioma: Português do Brasil (pt-br).
"""

class AgentCore:
    def __init__(self):
        # Initialize the model
        # Using gemini-pro as requested/implied for text generation
        self.model = genai.GenerativeModel('gemini-pro')

    def start_chat(self, history: Optional[List[Dict[str, str]]] = None):
        """
        Starts a chat session.
        """
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
        if not GOOGLE_API_KEY:
            return "Erro: API Key não configurada."

        try:
            # Create a chat session with the provided history
            chat = self.model.start_chat(history=history)

            # If history is empty, this is the first interaction.
            # We prepend the system prompt to the user message to set the context.
            if not history:
                prompt_with_context = f"{SYSTEM_PROMPT}\n\n[Início da Conversa]\nUsuário: {user_message}"
                response = chat.send_message(prompt_with_context)
            else:
                # For subsequent messages, the history maintains the context (including the initial system prompt)
                response = chat.send_message(user_message)

            return response.text
        except Exception as e:
            print(f"Error generating response: {e}")
            return "Desculpe, vamos com calma. Ocorreu um erro ao processar sua mensagem."

agent = AgentCore()
