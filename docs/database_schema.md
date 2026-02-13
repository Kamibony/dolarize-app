# Esquema do Banco de Dados (Firestore) - Dólarize App

Este documento descreve a estrutura inicial das coleções do Firebase Firestore para o projeto Dólarize App.

## Visão Geral

O banco de dados utiliza o Firebase Firestore, um banco de dados NoSQL orientado a documentos. A estrutura é projetada para ser escalável e flexível, atendendo aos requisitos da metodologia "Dólarize 2.0".

## Coleções

### 1. `usuarios` (Usuários)

Armazena as informações de perfil dos usuários e seu status na jornada.

**Campos:**

*   `uid` (string): ID único do usuário (gerado pelo Firebase Authentication).
*   `nome` (string): Nome completo do usuário.
*   `email` (string): Endereço de e-mail.
*   `data_cadastro` (timestamp): Data e hora de criação da conta.
*   `status_jornada` (string): O status atual do usuário na metodologia.
    *   Valores possíveis:
        *   `"A-Pronto"`: Usuário pronto para agir/investir.
        *   `"B-Em maturação"`: Usuário em processo de aprendizado e organização.
        *   `"C-Curioso"`: Usuário iniciante ou apenas explorando.
*   `perfil_investidor` (map, opcional): Dados sobre o perfil de risco (Conservador, Moderado, Arrojado).
*   `ultimo_acesso` (timestamp): Data do último login.

### 2. `interacoes_chat` (Interações do Chat)

Registra o histórico de conversas entre o usuário e o agente "André Digital".

**Campos:**

*   `id` (string): ID único da interação (gerado automaticamente).
*   `uid_usuario` (string): Referência ao `uid` do usuário na coleção `usuarios`.
*   `data_inicio` (timestamp): Data e hora do início da conversa.
*   `mensagens` (array de maps): Lista ordenada das mensagens trocadas.
    *   Cada item contém:
        *   `role` (string): "user" (usuário) ou "model" (André Digital).
        *   `conteudo` (string): O texto da mensagem.
        *   `timestamp` (timestamp): Hora exata da mensagem.
*   `resumo` (string, opcional): Um breve resumo do tópico da conversa (gerado por IA posteriormente).
*   `tags` (array de strings, opcional): Tags para categorizar a conversa (ex: "dúvida", "organização", "investimentos").

### 3. `progresso_aulas` (Progresso das Aulas)

Rastreia o progresso do usuário nos módulos educacionais e resultados de quizzes.

**Campos:**

*   `id` (string): ID único do registro de progresso (pode ser composto por `uid_usuario` + `id_modulo` ou gerado automaticamente).
*   `uid_usuario` (string): Referência ao `uid` do usuário.
*   `id_modulo` (string): Identificador do módulo ou curso.
*   `id_aula` (string): Identificador da aula específica.
*   `status` (string): Status de conclusão.
    *   Valores: `"nao_iniciado"`, `"em_andamento"`, `"concluido"`.
*   `percentual_conclusao` (number): 0 a 100.
*   `data_conclusao` (timestamp, opcional): Data de finalização.
*   `notas_quiz` (map, opcional): Resultados de avaliações.
    *   Chave: ID do quiz.
    *   Valor: Nota ou percentual de acerto.

## Notas Adicionais

*   Todos os campos de data devem utilizar o tipo `Timestamp` do Firestore.
*   A segurança das coleções deve ser configurada através das Firebase Security Rules, garantindo que usuários acessem apenas seus próprios dados (exceto admins).
