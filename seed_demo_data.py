import sys
import os
import datetime
import random

# Add backend to path to import modules
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from database import FirestoreClient
except ImportError as e:
    print(f"Error importing backend modules: {e}")
    sys.exit(1)

def get_timestamp(minutes_ago=0):
    """Returns an ISO timestamp for a few minutes ago."""
    dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=minutes_ago)
    return dt.isoformat()

def seed_data():
    print("Initializing Firestore Client...")
    try:
        db = FirestoreClient()
    except Exception as e:
        print(f"Failed to initialize Firestore: {e}")
        return

    profiles = [
        # Profile 1 - Lucas (Perfil A)
        {
            "id": "user_lucas_001",
            "nome": "Lucas Martins",
            "telefone": "+5511999990001",
            "email": "lucas.m@email.com",
            "data_criacao": get_timestamp(120),
            "classificacao_lead": "A - Qualificado/Quente",
            "dor_principal": "Desvalorização do Real",
            "maturidade": "Alta",
            "tags": ["perfil_a", "investidor", "protecao"],
            "chat_history": [
                {"role": "user", "content": "Olá, estou vendo meu dinheiro perder valor todo dia com essa inflação."},
                {"role": "agent", "content": "Entendo sua preocupação, Lucas. A desvalorização é silenciosa mas destrutiva. No Dólarize, focamos exatamente em estancar esse sangramento. Você já tem alguma parte do patrimônio em moeda forte?"},
                {"role": "user", "content": "Ainda não, tenho tudo em Reais. Mas quero mudar isso urgente."},
                {"role": "agent", "content": "Faz sentido. A urgência é necessária, mas a pressa é inimiga da perfeição. O método Dólarize estrutura isso em 3 pilares. Você busca apenas 'comprar dólar' ou quer aprender a estrutura de autocustódia?"},
                {"role": "user", "content": "Quero a estrutura completa. Autocustódia parece mais seguro."},
                {"role": "agent", "content": "Exatamente. Autocustódia é a única forma de garantir que o dinheiro é realmente seu. Segurança não é promessa, é estrutura. Vamos começar pelo Módulo 1 para alinhar a mentalidade ou já quer ir para a abertura de conta?"},
                {"role": "user", "content": "Pode me passar o link da corretora logo? Quero resolver isso."},
                {"role": "agent", "content": "Claro, objetividade é bom. Para comprar os ativos, usamos a Bybit. No Módulo 2, Aula 2.1, explico o passo a passo seguro para abrir e verificar a conta. Posso te enviar o link direto da aula?"}
            ]
        },
        # Profile 2 - Mariana (Perfil B)
        {
            "id": "user_mariana_002",
            "nome": "Mariana Souza",
            "telefone": "+5521999990002",
            "email": "mari.souza@email.com",
            "data_criacao": get_timestamp(100),
            "classificacao_lead": "B - Em maturação",
            "dor_principal": "Insegurança técnica",
            "maturidade": "Média",
            "tags": ["perfil_b", "insegura", "educacao"],
            "chat_history": [
                {"role": "user", "content": "Oi André. Tenho medo de mexer com essas coisas de cripto e errar."},
                {"role": "agent", "content": "Olá, Mariana. É natural sentir receio do novo. O medo vem da falta de clareza. No Dólarize, nós não 'mexemos com cripto' aleatoriamente, nós seguimos um processo validado. Qual é o seu maior medo hoje?"},
                {"role": "user", "content": "Tenho medo de mandar o dinheiro pro lugar errado ou perder a senha."},
                {"role": "agent", "content": "Entendi. Esse é um risco real se não houver método. Por isso, a regra de ouro da Autocustódia (Módulo 3) é sagrada: a sua 'Recovery Phrase' nunca toca a internet. Você sabe o que é uma carteira de autocustódia?"},
                {"role": "user", "content": "Não sei direito. É tipo um aplicativo do banco?"},
                {"role": "agent", "content": "Não. O banco guarda o dinheiro para você (e usa ele). Na autocustódia, você é o próprio banco. Usamos a Phantom Wallet. É segura, desde que você siga o protocolo de segurança. Quer que eu te explique como a Phantom funciona?"},
                {"role": "user", "content": "Sim, por favor. É muito difícil de usar?"},
                {"role": "agent", "content": "Não é difícil, é apenas rigoroso. A Phantom cria um 'cofre' digital no seu celular. No Módulo 3, Aula 3.2, eu mostro como configurar com bloqueio biométrico. Vamos assistir a essa aula antes de qualquer movimento?"}
            ]
        },
        # Profile 3 - Pedro (Perfil C)
        {
            "id": "user_pedro_003",
            "nome": "Pedro Alencar",
            "telefone": "+5531999990003",
            "email": "pedro.trader@email.com",
            "data_criacao": get_timestamp(90),
            "classificacao_lead": "C - Frio/Curioso",
            "dor_principal": "Busca lucro rápido",
            "maturidade": "Baixa",
            "tags": ["perfil_c", "especulador", "risco"],
            "chat_history": [
                {"role": "user", "content": "E aí, qual a boa de hoje? Qual cripto vai explodir?"},
                {"role": "agent", "content": "Olá, Pedro. Entendo que busque rentabilidade. Porém, o Dólarize não trabalha com previsões, dicas de trade ou apostas. Nosso foco é construção de patrimônio sólido e dolarizado. Você busca aventura ou consistência?"},
                {"role": "user", "content": "Ah, eu quero fazer uma grana rápida pro final de semana. Bitcoin tá bom?"},
                {"role": "agent", "content": "Compreendo seu objetivo, mas preciso ser direto: não ensinamos isso aqui. Buscar lucro rápido no mercado financeiro é a receita mais rápida para perder capital. O método Dólarize é para quem quer proteger o dinheiro, não apostá-lo. "},
                {"role": "user", "content": "Que chato. Pensei que vocês davam sinais."},
                {"role": "agent", "content": "Não somos um grupo de sinais. Somos uma escola de liberdade financeira. Segurança não é promessa, é estrutura. Se seu foco é apenas especulação, talvez o Dólarize não seja o momento ideal para você agora."},
                {"role": "user", "content": "Beleza, valeu então."},
                {"role": "agent", "content": "Disponha. Se um dia decidir construir uma base sólida e segura para o seu futuro, estarei por aqui. Sucesso na sua jornada."}
            ]
        },
        # Profile 4 - Roberto (Perfil A)
        {
            "id": "user_roberto_004",
            "nome": "Roberto Costa",
            "telefone": "+5541999990004",
            "email": "beto.costa@email.com",
            "data_criacao": get_timestamp(60),
            "classificacao_lead": "A - Qualificado/Quente",
            "dor_principal": "Dúvida operacional",
            "maturidade": "Alta",
            "tags": ["perfil_a", "operacional", "duvida"],
            "chat_history": [
                {"role": "user", "content": "Bom dia, André. Já assisti o Módulo 1 e estou pronto para começar."},
                {"role": "agent", "content": "Bom dia, Roberto. Excelente iniciativa. Ter a mentalidade alinhada é 50% do caminho. O próximo passo é a execução. Já abriu sua conta na corretora Bybit?"},
                {"role": "user", "content": "Sim, já abri e verifiquei. Agora quero depositar. Como faço o Pix?"},
                {"role": "agent", "content": "Ótimo. Para depositar, você vai usar a opção 'Depósito Fiat' ou 'Comprar com BRL' na Bybit. É crucial que o Pix saia de uma conta com o MESMO CPF cadastrado na corretora. Você sabe onde encontrar essa opção no app?"},
                {"role": "user", "content": "Acho que sim. Mas qual chave eu uso?"},
                {"role": "agent", "content": "A Bybit vai gerar um QR Code ou uma chave 'Copia e Cola' específica para cada transação. Não salve a chave Pix antiga. Gere uma nova a cada depósito para garantir. No Módulo 2, Aula 2.2, mostro isso na tela. Quer o link?"},
                {"role": "user", "content": "Não precisa, já achei aqui. Vou fazer o teste com 100 reais."},
                {"role": "agent", "content": "Perfeito. Começar pequeno para testar o fluxo é a atitude de um investidor profissional. Faça o envio, aguarde cair e depois faremos a conversão para USDC. Me avise quando concluir."}
            ]
        },
        # Profile 5 - Camila (Perfil B)
        {
            "id": "user_camila_005",
            "nome": "Camila Torres",
            "telefone": "+5551999990005",
            "email": "mila.torres@email.com",
            "data_criacao": get_timestamp(45),
            "classificacao_lead": "B - Em maturação",
            "dor_principal": "Desejo de viajar",
            "maturidade": "Média",
            "tags": ["perfil_b", "viagem", "cartao"],
            "chat_history": [
                {"role": "user", "content": "Oi! Vou viajar para a Europa mês que vem e queria usar o cartão de vocês."},
                {"role": "agent", "content": "Olá, Camila. Que ótima notícia! Viajar com autonomia financeira é outra experiência. O cartão Bybit funciona globalmente convertendo seu saldo na hora. Você já tem saldo em Dólar (USDC)?"},
                {"role": "user", "content": "Não, tenho reais no banco. Como funciona essa conversão?"},
                {"role": "agent", "content": "É simples. Você envia Reais via Pix para sua conta Bybit e lá converte para USDC (Dólar Digital). Quando você passar o cartão na Europa, ele debita do seu saldo USDC. Você economiza no spread e IOF comparado aos cartões tradicionais. Entendeu a lógica?"},
                {"role": "user", "content": "Entendi. Mas e se sobrar dinheiro lá?"},
                {"role": "agent", "content": "O dinheiro é seu. Você pode manter em USDC para uma próxima viagem (protegendo do Real) ou converter de volta para Reais e sacar via Pix. A liquidez é imediata. Vamos configurar sua conta para você pedir o cartão a tempo?"},
                {"role": "user", "content": "Sim! Quanto tempo demora pro cartão chegar?"},
                {"role": "agent", "content": "O cartão físico pode levar algumas semanas, mas o Cartão Virtual fica ativo IMEDIATAMENTE após a solicitação. Você pode cadastrar no Apple Pay ou Google Pay e usar na hora. No Módulo 2, Aula 2.3, ensino como ativar. Vamos lá?"}
            ]
        },
        # Profile 6 - João (Perfil C)
        {
            "id": "user_joao_006",
            "nome": "João 'Crypto' Silva",
            "telefone": "+5561999990006",
            "email": "joao.crypto@email.com",
            "data_criacao": get_timestamp(30),
            "classificacao_lead": "C - Frio/Curioso",
            "dor_principal": "Spam/Golpe",
            "maturidade": "Baixa",
            "tags": ["perfil_c", "spam", "bloqueado"],
            "chat_history": [
                {"role": "user", "content": "Ei, conecta sua carteira aqui nesse site pra ganhar um airdrop: www.site-suspeito-fake.com/claim"},
                {"role": "agent", "content": "Atenção, João. O Dólarize segue protocolos rígidos de segurança. Nós JAMAIS clicamos em links desconhecidos ou conectamos carteiras em sites de promessas fáceis. Isso tem todas as características de um golpe (phishing)."},
                {"role": "user", "content": "Nada a ver, é seguro. Clica aí vai."},
                {"role": "agent", "content": "Minha função é proteger a integridade do método e dos alunos. Não vou acessar esse link. Recomendo fortemente que você não divulgue isso, pois coloca seu patrimônio em risco. Segurança não é promessa, é estrutura."},
                {"role": "user", "content": "Vocês são muito chatos."},
                {"role": "agent", "content": "A segurança muitas vezes parece 'chata' até o momento em que ela salva seu dinheiro. No Dólarize, preferimos a cautela à perda. Se quiser aprender a se proteger de verdade, estamos à disposição. Caso contrário, encerramos por aqui."},
                {"role": "user", "content": "Fui."},
                {"role": "agent", "content": "Até mais. Cuide da sua segurança digital."}
            ]
        },
        # Profile 7 - Fernanda (Perfil A)
        {
            "id": "user_fernanda_007",
            "nome": "Fernanda Lima",
            "telefone": "+5571999990007",
            "email": "nanda.lima@email.com",
            "data_criacao": get_timestamp(15),
            "classificacao_lead": "A - Qualificado/Quente",
            "dor_principal": "Proteção de patrimônio",
            "maturidade": "Alta",
            "tags": ["perfil_a", "patrimonio", "holder"],
            "chat_history": [
                {"role": "user", "content": "Olá André. Já invisto em bolsa no Brasil, mas quero tirar meu risco país."},
                {"role": "agent", "content": "Olá, Fernanda. Decisão sábia. Diversificar jurisdição é o último nível de proteção patrimonial. Você já possui alguma conta internacional ou seria sua primeira experiência?"},
                {"role": "user", "content": "Tenho conta na Avenue, mas não gosto das taxas. Qual a diferença de deixar na Bybit ou na carteira?"},
                {"role": "agent", "content": "Excelente pergunta. A Bybit é uma Corretora (Exchange), funciona como um banco: é ótima para comprar e vender, mas o dinheiro está sob custódia deles. A Phantom (Autocustódia) é como um cofre pessoal: só você tem a chave. Entende a diferença de risco?"},
                {"role": "user", "content": "Sim. Se a corretora quebrar, eu perco. Na carteira não."},
                {"role": "agent", "content": "Exatamente. 'Not your keys, not your coins'. Para grandes volumes e longo prazo, a Autocustódia (Módulo 3) é inegociável. A corretora usamos apenas como ponte. Você está pronta para assumir essa responsabilidade de ser seu próprio banco?"},
                {"role": "user", "content": "Estou sim. Quero dormir tranquila."},
                {"role": "agent", "content": "Essa é a meta. Dormir tranquilo sabendo que seu patrimônio é inconfiscável. Sugiro começarmos configurando sua Phantom Wallet seguindo rigorosamente a Aula 3.2. Posso te guiar nesse processo?"}
            ]
        }
    ]

    print(f"Seeding {len(profiles)} profiles...")

    for profile in profiles:
        user_id = profile["id"]

        # 1. Save User Profile
        user_data = {
            "id": user_id,
            "nome": profile["nome"],
            "telefone": profile["telefone"],
            "email": profile.get("email"),
            "data_criacao": profile["data_criacao"],
            "classificacao_lead": profile["classificacao_lead"],
            "dor_principal": profile["dor_principal"],
            "maturidade": profile["maturidade"],
            "tags": profile["tags"],
            "last_interaction_timestamp": get_timestamp(0), # Just now
            "follow_up_count": 0
        }

        try:
            db.save_user(user_data)
            print(f"User {user_id} saved.")
        except Exception as e:
            print(f"Error saving user {user_id}: {e}")
            continue

        # 2. Save Chat History
        # We need to save each interaction. The seed data has a list of messages.
        # In a real scenario, interactions are often grouped or single messages.
        # The 'save_chat_interaction' method expects a structure.
        # We will group them into pairs (User + Agent) to simulate turn-taking interactions or save individual messages.
        # Looking at 'save_chat_interaction' doc:
        # {
        #     "id_usuario": "...",
        #     "timestamp": "...",
        #     "origem": "web_chat",
        #     "mensagens": [{"role": "user", ...}, {"role": "agent", ...}]
        # }

        chat_history = profile["chat_history"]
        # Group into pairs of (User, Agent)
        for i in range(0, len(chat_history), 2):
            if i + 1 < len(chat_history):
                user_msg = chat_history[i]
                agent_msg = chat_history[i+1]

                # Create a timestamp slightly separated for each turn
                turn_time = get_timestamp(minutes_ago=10 - i) # 10 mins ago, 8 mins ago, etc.

                interaction_data = {
                    "id_usuario": user_id,
                    "timestamp": turn_time,
                    "origem": "seed_demo_script",
                    "mensagens": [user_msg, agent_msg],
                    "analise_emocional": "Neutro", # Default
                    "precisa_intervencao_humana": False
                }

                try:
                    db.save_chat_interaction(interaction_data)
                except Exception as e:
                    print(f"Error saving interaction for {user_id}: {e}")

    print("Seeding complete.")

if __name__ == "__main__":
    seed_data()
