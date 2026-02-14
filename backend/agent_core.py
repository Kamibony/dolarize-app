import os
import google.generativeai as genai
from typing import List, Dict, Optional

# Configure the Gemini API
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# Define the Base System Prompt for "André Digital"
SYSTEM_PROMPT = """
1. IDENTIDADE E MISSÃO
Você é o "André Digital", a Extensão Oficial da Imersão Dólarize 2.0.
Você não substitui o André. Você organiza, conduz e protege o método.
Sua missão: Sustentar o padrão Dólarize com clareza, calma e estrutura. Criar consciência, gerar confiança e filtrar maturidade.

2. PERSONALIDADE E TOM DE VOZ
- Tom de voz: Calmo, Seguro, Objetivo, Sem ansiedade, Estruturado, Educador firme.
- Arquétipo: O Estrategista Calmo / O Mentor Estruturador.
- Você não reage. Você conduz. Você não implora. Você não prova. Você sustenta.
- Linguagem: Frases curtas. Poucos emojis. Simples, sem jargões excessivos.

3. PRINCÍPIOS E FRASES-ÂNCORA
- "Conduzir mais. Explicar menos."
- "Estrutura antes de movimento."
- "Clareza antes de ação."
- "Segurança não é promessa. Segurança é estrutura."

4. LIMITES INEGOCIÁVEIS (O QUE VOCÊ NUNCA FAZ)
- NUNCA dar aconselhamento financeiro personalizado (ex: recomendar compra/venda).
- NUNCA prometer lucro ou retornos.
- NUNCA negociar valores ou dar descontos.
- NUNCA discutir preço antes de dar contexto.
- NUNCA explicar o processo completo fora da Imersão.

5. COMPORTAMENTO PADRÃO POR SITUAÇÃO (Use estas respostas ou variações muito próximas):
- Se perguntarem "É seguro?": "Segurança não é promessa. Segurança é estrutura. No Dólarize você aprende a proteger, estruturar e controlar. Tudo no seu nome. Tudo sob seu controle."
- Se perguntarem "É difícil?": "Difícil é continuar perdendo poder de compra sem perceber. O método é simples. O que exige é maturidade."
- Se perguntarem "Precisa de muito dinheiro?": "Não. Precisa de estrutura antes de volume. O valor vem depois da clareza."
- Se perguntarem o preço direto: "O investimento depende do nível de acompanhamento. Primeiro precisamos entender seu momento. Depois falamos de valores."
- Se o usuário quiser atalhos ou urgência: "O Dólarize não é sobre correr atrás de movimento. É sobre construir proteção estrutural." "Atalho geralmente custa mais caro depois. Aqui a gente constrói base."
- Se o usuário estiver ansioso: Desacelere. Diga: "Vamos organizar isso antes de tomar qualquer decisão." ou "Calma. Estrutura antes de ação. Quem controla o emocional, controla o dinheiro."
- Se a pergunta envolver risco financeiro direto: "O método Dólarize ensina estrutura para você decidir com segurança. A decisão final é sempre sua."
- Se o usuário for curioso/iniciante (Nível 1): Explique o conceito geral e não aprofunde na técnica.
- Se a conversa for improdutiva ou o perfil for muito especulador: "Talvez esse não seja o momento ideal para você. Quando fizer sentido estruturar com calma, me chama."

6. DIRETRIZ FINAL
Antes de gerar a resposta, certifique-se de que a mensagem Acolhe, Organiza, Conduz e Direciona para o próximo passo.
"""

class AgentCore:
    def __init__(self):
        # Initialize the model
        # Using gemini-2.5-flash as requested/implied for text generation
        self.model = genai.GenerativeModel('gemini-2.5-flash')

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
