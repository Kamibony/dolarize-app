<script>
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { auth, db } from '$lib/firebase';
    import { onAuthStateChanged } from 'firebase/auth';
    import { doc, setDoc, collection, serverTimestamp, updateDoc } from 'firebase/firestore';

    // ══════════════════════════════════════════════════════
    //  DATA
    // ══════════════════════════════════════════════════════
    const QUESTIONS = [
        {id:1,block:1,blockLabel:"CONSCIÊNCIA PATRIMONIAL", text:"Você sabe exatamente quanto vale seu patrimônio total hoje — em reais e em dólar?", opts:[ {l:"A",t:"Tenho uma ideia vaga, mas nunca parei para calcular direito.",p:1}, {l:"B",t:"Já fiz esse cálculo alguma vez, mas não acompanho com regularidade.",p:2}, {l:"C",t:"Conheço meu patrimônio e o reviso periodicamente.",p:3}, {l:"D",t:"Tenho clareza total: sei o valor, a alocação e a exposição cambial em tempo real.",p:4}, ]},
        {id:2,block:1,blockLabel:"CONSCIÊNCIA PATRIMONIAL", text:"Quanto do seu patrimônio está protegido contra a desvalorização do real?", opts:[ {l:"A",t:"Nada. Tudo está em reais.",p:1}, {l:"B",t:"Uma parte pequena, mas não foi uma decisão estratégica.",p:2}, {l:"C",t:"Tenho uma parcela relevante em dólar ou ativos dolarizados.",p:3}, {l:"D",t:"A maior parte do meu patrimônio está dolarizada por estratégia consciente.",p:4}, ]},
        {id:3,block:1,blockLabel:"CONSCIÊNCIA PATRIMONIAL", text:"Você recebe R$ 80.000 inesperados. O que acontece nos próximos 7 dias?", opts:[ {l:"A",t:"Fico feliz, mas acaba indo para a conta corrente sem destino claro.",p:1}, {l:"B",t:"Penso em investir, mas demoro para decidir e acaba no Tesouro por comodidade.",p:2}, {l:"C",t:"Sei exatamente para onde vai: já tenho critérios definidos de alocação.",p:3}, {l:"D",t:"Executo a decisão em menos de 48h seguindo meu método e registro o movimento.",p:4}, ]},
        {id:4,block:1,blockLabel:"CONSCIÊNCIA PATRIMONIAL", text:"Quando foi a última vez que você revisou sua carteira com intenção real?", opts:[ {l:"A",t:"Faz meses — ou talvez mais de um ano.",p:1}, {l:"B",t:"Faço isso quando algo me preocupa no mercado.",p:2}, {l:"C",t:"Tenho uma rotina mensal ou trimestral de revisão.",p:3}, {l:"D",t:"Reviso semanalmente e registro insights após cada análise.",p:4}, ]},
        {id:5,block:2,blockLabel:"DECISÃO & DISCIPLINA", text:"Como você costuma tomar decisões financeiras importantes?", opts:[ {l:"A",t:"Espero indicações de amigos, grupos ou redes sociais.",p:1}, {l:"B",t:"Pesquiso bastante, mas demoro para agir — o medo de errar paralisa.",p:2}, {l:"C",t:"Tenho critérios próprios e me sinto seguro para decidir sozinho.",p:3}, {l:"D",t:"Decido com clareza, executo sem hesitar e aprendo com cada movimento.",p:4}, ]},
        {id:6,block:2,blockLabel:"DECISÃO & DISCIPLINA", text:"Em momentos de queda acentuada no mercado, qual é sua reação mais honesta?", opts:[ {l:"A",t:"Fico ansioso, acompanho o tempo todo e considero vender tudo.",p:1}, {l:"B",t:"Fico desconfortável, mas tento me manter. Nem sempre consigo.",p:2}, {l:"C",t:"Mantenho a estratégia. Queda não muda meu plano de longo prazo.",p:3}, {l:"D",t:"Vejo oportunidade. Queda é hora de agir com critério, não de recuar.",p:4}, ]},
        {id:7,block:2,blockLabel:"DECISÃO & DISCIPLINA", text:"Você tem um método próprio de investimento — ou segue o que parece funcionar no momento?", opts:[ {l:"A",t:"Não tenho método. Vou tentando conforme vejo oportunidades.",p:1}, {l:"B",t:"Tenho alguns princípios, mas não são muito consistentes.",p:2}, {l:"C",t:"Tenho um método que sigo com disciplina na maior parte do tempo.",p:3}, {l:"D",t:"Meu método é sólido, testado e já sobreviveu a ciclos ruins.",p:4}, ]},
        {id:8,block:2,blockLabel:"DECISÃO & DISCIPLINA", text:"Com que frequência você age diferente do seu plano por pressão externa?", opts:[ {l:"A",t:"Com frequência — é difícil ignorar o que todo mundo está fazendo.",p:1}, {l:"B",t:"Às vezes me deixo influenciar, mesmo sabendo que não deveria.",p:2}, {l:"C",t:"Raramente. Aprendi a filtrar ruído com o tempo.",p:3}, {l:"D",t:"Nunca. Meu plano é mais forte do que qualquer narrativa do momento.",p:4}, ]},
        {id:9,block:3,blockLabel:"PROTEÇÃO & RISCO", text:"Quanto do seu patrimônio você seria capaz de perder sem comprometer seu estilo de vida?", opts:[ {l:"A",t:"Qualquer perda relevante mudaria minha vida — não tenho gordura.",p:1}, {l:"B",t:"Tenho alguma reserva, mas insuficiente para um cenário adverso real.",p:2}, {l:"C",t:"Tenho reservas sólidas. Uma perda de 30% não comprometeria nada.",p:3}, {l:"D",t:"Minha estrutura foi desenhada para sobreviver a crises severas sem dano real.",p:4}, ]},
        {id:10,block:3,blockLabel:"PROTEÇÃO & RISCO", text:"Alguém cuida do seu dinheiro sem que você entenda completamente o que está sendo feito?", opts:[ {l:"A",t:"Sim — deleguei tudo. Não sei bem o que está acontecendo.",p:1}, {l:"B",t:"Tenho um gestor, mas raramente reviso o que ele faz.",p:2}, {l:"C",t:"Delego parte, mas entendo o que está sendo feito e monitoro.",p:3}, {l:"D",t:"Nada é delegado sem critério claro e sem minha compreensão total.",p:4}, ]},
        {id:11,block:3,blockLabel:"PROTEÇÃO & RISCO", text:"Sua renda depende exclusivamente do seu esforço direto — se você parar, o dinheiro para?", opts:[ {l:"A",t:"Sim. Tudo que tenho vem do meu trabalho ativo.",p:1}, {l:"B",t:"Tenho alguns investimentos, mas ainda dependem muito do meu esforço.",p:2}, {l:"C",t:"Já construí fontes de renda que funcionam sem minha presença diária.",p:3}, {l:"D",t:"Tenho múltiplos fluxos de renda passiva em dólar que operam sem mim.",p:4}, ]},
        {id:12,block:3,blockLabel:"PROTEÇÃO & RISCO", text:"Em caso de crise cambial severa — real caindo 40% em 6 meses — o que acontece com seu patrimônio?", opts:[ {l:"A",t:"Sofreria muito. Estou totalmente exposto ao real.",p:1}, {l:"B",t:"Sentiria bastante. Tenho proteção insuficiente para um cenário assim.",p:2}, {l:"C",t:"Ficaria confortável. Boa parte do meu patrimônio está dolarizado.",p:3}, {l:"D",t:"Prosperaria. Crise cambial para mim é acelerador patrimonial.",p:4}, ]},
        {id:13,block:4,blockLabel:"VISÃO & LEGADO", text:"Você pensa no seu patrimônio como algo que vai além da sua própria vida?", opts:[ {l:"A",t:"Não muito. Ainda estou focado em construir o básico para mim.",p:1}, {l:"B",t:"Já penso nisso, mas não tomei nenhuma ação concreta ainda.",p:2}, {l:"C",t:"Tenho planejamento de sucessão em andamento.",p:3}, {l:"D",t:"Minhas decisões de hoje já contemplam as próximas gerações de forma estruturada.",p:4}, ]},
        {id:14,block:4,blockLabel:"VISÃO & LEGADO", text:"Seus filhos ou herdeiros sabem o que fazer com o patrimônio que você está construindo?", opts:[ {l:"A",t:"Não. Esse assunto nunca foi discutido em família.",p:1}, {l:"B",t:"Vagamente. Já tocamos no assunto, mas sem estrutura.",p:2}, {l:"C",t:"Eles têm consciência geral, mas falta documentação e educação formal.",p:3}, {l:"D",t:"Há um plano claro, documentado, e eles participam ativamente da visão.",p:4}, ]},
        {id:15,block:4,blockLabel:"VISÃO & LEGADO", text:"O que te motiva mais quando pensa no seu patrimônio?", opts:[ {l:"A",t:"Ter segurança básica e não passar aperto.",p:1}, {l:"B",t:"Construir uma reserva confortável para minha aposentadoria.",p:2}, {l:"C",t:"Criar liberdade financeira e geográfica para mim e minha família.",p:3}, {l:"D",t:"Construir um legado que continue gerando prosperidade após mim.",p:4}, ]},
    ];

    /** @type {Record<number, string>} */
    const BLOCK_MSG = {
        1:"Boa. Você está desenvolvendo clareza real sobre o seu patrimônio. Continue.",
        2:"Excelente. Você está mapeando sua capacidade de decisão com honestidade.",
        3:"Importante. Poucos investidores fazem essas perguntas com essa profundidade.",
    };

    const LEVELS = [
        {id:1,name:"SOBREVIVENTE",arch:"O Sobrevivente",range:[15,26], color:"#9CA3AF",medal:"🔘",pct:"Top 80%", identity:"Você ainda está descobrindo seu patrimônio. A clareza está chegando.", desc:"Você possui recursos, mas eles ainda não estão organizados para trabalhar por você. O primeiro passo é a consciência — e você já está aqui.", strengths:["Capacidade de trabalho e geração de renda","Disposição genuína para aprender","Primeiros movimentos de consciência financeira"], gap:"Falta clareza e registro. Sem saber o que você tem, é impossível proteger ou multiplicar.", next:"Registre hoje o valor total do seu patrimônio em USDC. Esse é o primeiro ato de soberania financeira.", daily:"Registrar patrimônio atual (valor total em USDC hoje)", stage:"A PORTA — Decisão consciente. Ruptura com o sistema antigo.", cta:"Você está na porta. É hora de abri-la."},
        {id:2,name:"ACUMULADOR",arch:"O Acumulador",range:[27,36], color:"#60A5FA",medal:"🔵",pct:"Top 60%", identity:"Você já toma decisões. Falta consistência e método.", desc:"Você tem consciência patrimonial e já investe, mas suas decisões ainda são reativas. O mercado ou as emoções ainda influenciam mais do que deveriam.", strengths:["Consciência patrimonial em desenvolvimento","Já executa decisões de investimento","Alguma proteção construída"], gap:"Decisões inconsistentes e exposição cambial ainda alta. Um ciclo ruim pode apagar anos de construção.", next:"Defina seu critério de alocação em dólar e execute pelo menos uma decisão do método esta semana.", daily:"Executar 1 decisão do método: aporte, rebalanceamento ou hold consciente", stage:"O COFRE — Posse. Soberania. Silêncio.", cta:"Você está construindo o cofre. Falta colocar o que importa dentro dele."},
        {id:3,name:"CONSTRUTOR",arch:"O Construtor",range:[37,46], color:"#A78BFA",medal:"🟣",pct:"Top 35%", identity:"Você constrói com método. Está no caminho certo.", desc:"Você tem disciplina, método e consistência. Seu patrimônio cresce de forma estruturada. O próximo nível exige que você passe de construtor para protetor.", strengths:["Disciplina e consistência comprovadas","Método próprio consolidado","Crescimento patrimonial estruturado"], gap:"Proteção insuficiente para ciclos adversos. Você constrói bem, mas ainda pode perder muito em uma crise.", next:"Revise sua exposição ao risco hoje e identifique qual parcela do patrimônio ainda está vulnerável.", daily:"Revisar carteira e registrar 1 insight do dia", stage:"O OLHAR — Consciência emocional. Leitura do coletivo.", cta:"Você desenvolveu o olhar. Agora use-o para proteger o que construiu."},
        {id:4,name:"GUARDIÃO",arch:"O Guardião",range:[47,54], color:"#FCD34D",medal:"🟡",pct:"Top 15%", identity:"Você protege com inteligência. Está entre os melhores.", desc:"Você não apenas constrói — você protege. Suas decisões contemplam riscos que a maioria dos investidores ignora. Seu patrimônio sobrevive a crises.", strengths:["Proteção patrimonial sólida","Controle emocional em cenários adversos","Delegação com critério e supervisão ativa"], gap:"Visão de legado ainda em desenvolvimento. Você protege para você — mas e para as próximas gerações?", next:"Inicie uma conversa com sua família sobre o plano patrimonial. Legado começa com consciência compartilhada.", daily:"Verificar exposição ao risco e confirmar que nada foi delegado sem critério", stage:"O FLUXO — Execução viva. Renda estrutural.", cta:"Você vive no fluxo. É hora de torná-lo permanente."},
        {id:5,name:"PATRIARCA",arch:"O Patriarca",range:[55,60], color:"#34D399",medal:"🟢",pct:"Top 3%", identity:"Você pensa em gerações. Está no nível mais alto.", desc:"Você transcendeu a acumulação. Seu patrimônio é uma estrutura viva que protege e prospera além de você. Você toma decisões pensando nas próximas décadas.", strengths:["Visão de legado estruturada e documentada","Múltiplos fluxos de renda passiva em dólar","Família integrada ao planejamento patrimonial"], gap:"O desafio agora é escala, influência e transmissão de conhecimento para a próxima geração.", next:"Documente uma decisão hoje que protege o patrimônio das próximas gerações e compartilhe com seus herdeiros.", daily:"Registrar 1 decisão que protege o patrimônio das próximas gerações", stage:"DÓLARIZE 2.0 — O sistema está montado.", cta:"Você é o sistema. O Dólarize foi feito para quem chegou até aqui."},
    ];

    // ══════════════════════════════════════════════════════
    //  STATE
    // ══════════════════════════════════════════════════════
    let activeScreen = 's-intro'; // 's-intro', 's-quiz', 's-capture', 's-result'
    let version = 'viral';
    let currentQ = 0;
    /** @type {number[]} */
    let answers = [];
    /** @type {number | null} */
    let selected = null;
    let bridging = false;
    let bridgeMessage = '';

    // Captura variables
    let userName = '';
    let userPhone = '';

    // Firebase Auth State
    /** @type {any} */
    let currentUser = null;

    onMount(() => {
        const unsubscribe = onAuthStateChanged(auth, (user) => {
            currentUser = user;
            if (currentUser && currentUser.displayName) {
                userName = currentUser.displayName;
            }
        });
        return () => unsubscribe();
    });

    // ══════════════════════════════════════════════════════
    //  HELPERS
    // ══════════════════════════════════════════════════════
    /** @param {number} total */
    function getLevel(total) {
        return LEVELS.find(l => total >= l.range[0] && total <= l.range[1]) || LEVELS[0];
    }

    /** @param {number} total */
    function getScore100(total) {
        return Math.round((total / (QUESTIONS.length * 4)) * 100);
    }

    /** @param {string} v */
    function setVersion(v) {
        version = v;
    }

    function startQuiz() {
        currentQ = 0;
        answers = [];
        selected = null;
        bridging = false;
        activeScreen = 's-quiz';
    }

    // ══════════════════════════════════════════════════════
    //  QUIZ LOGIC
    // ══════════════════════════════════════════════════════
    $: q = QUESTIONS[currentQ];
    $: progress = (currentQ / QUESTIONS.length) * 100;
    $: isLast = currentQ === QUESTIONS.length - 1;

    /** @param {number} pts */
    function selectOpt(pts) {
        selected = pts;
    }

    function nextQ() {
        if (selected === null) return;
        answers[currentQ] = selected;

        if (isLast) {
            activeScreen = 's-capture';
            return;
        }

        const cur = QUESTIONS[currentQ];
        const nxt = QUESTIONS[currentQ + 1];
        const blockChange = cur.block !== nxt.block;

        currentQ++;
        selected = answers[currentQ] !== undefined ? answers[currentQ] : null;

        if (blockChange && BLOCK_MSG[cur.block]) {
            bridgeMessage = BLOCK_MSG[cur.block];
            bridging = true;
            setTimeout(() => {
                bridging = false;
            }, 2200);
        }
    }

    function prevQ() {
        if (currentQ === 0) {
            activeScreen = 's-intro';
            return;
        }
        currentQ--;
        selected = answers[currentQ] !== undefined ? answers[currentQ] : null;
    }

    // ══════════════════════════════════════════════════════
    //  RESULT LOGIC
    // ══════════════════════════════════════════════════════
    let resultTotal = 0;
    /** @type {any} */
    let resultLevel = null;
    let resultScore100 = 0;
    /** @type {any} */
    let resultNextLevel = null;
    let resultPtsToNext = 0;

    async function showResult() {
        resultTotal = answers.reduce((s, a) => s + a, 0);
        resultLevel = getLevel(resultTotal);
        resultScore100 = getScore100(resultTotal);
        resultNextLevel = LEVELS.find(l => l.id === resultLevel.id + 1);
        resultPtsToNext = resultNextLevel ? resultNextLevel.range[0] - resultTotal : 0;

        activeScreen = 's-result';
        window.scrollTo({ top: 0, behavior: 'smooth' });

        // Save to Firestore if user is authenticated
        if (currentUser) {
            try {
                const diagnosticId = Date.now().toString(); // Use timestamp as ID
                const diagnosticRef = doc(collection(db, `users/${currentUser.uid}/diagnostics`), diagnosticId);

                /** @type {Record<string, any>} */
                const answersRecord = {};
                QUESTIONS.forEach((question, index) => {
                     answersRecord[`q${question.id}`] = answers[index];
                });

                await setDoc(diagnosticRef, {
                    diagnosticId: diagnosticId,
                    answers: answersRecord,
                    resultArchetype: version === 'viral' ? resultLevel.arch : `Nível ${resultLevel.id}`,
                    totalScore: resultTotal,
                    takenAt: serverTimestamp()
                });

                // Update user's current archetype
                const userRef = doc(db, 'users', currentUser.uid);
                await updateDoc(userRef, {
                    currentArchetype: version === 'viral' ? resultLevel.arch : `Nível ${resultLevel.id}`,
                    updatedAt: serverTimestamp()
                });

            } catch (e) {
                console.error("Error saving diagnostic:", e);
            }
        }
    }

    function restart() {
        version = version; // Keep version
        currentQ = 0;
        answers = [];
        selected = null;
        bridging = false;
        userName = '';
        userPhone = '';
        activeScreen = 's-intro';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
</script>

<svelte:head>
    <title>Diagnóstico Patrimonial — Dólarize</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
</svelte:head>

<div class="wrap">
    {#if activeScreen === 's-intro'}
    <!-- ══════════ INTRO ══════════ -->
    <div class="screen active">
        <div class="intro-hero">
            <div class="eyebrow">Diagnóstico Patrimonial Premium</div>
            <div class="logo">DÓLARIZE</div>
            <div class="logo-sub">MÉTODO · 2.0</div>
            <h1 class="hero-headline">Em qual nível de evolução patrimonial você está?</h1>
            <p class="hero-sub">15 perguntas. 5 minutos. Um diagnóstico honesto que poucos investidores têm coragem de fazer consigo mesmos.</p>
            <div class="divider-gold"></div>
            <div class="stats-row">
                <div><span class="stat-num">15</span><span class="stat-label">Perguntas</span></div>
                <div><span class="stat-num">5</span><span class="stat-label">Níveis</span></div>
                <div><span class="stat-num">&lt;5min</span><span class="stat-label">Duração</span></div>
            </div>
            <div class="toggle-wrap">
                <button class="toggle-btn {version === 'viral' ? 'on' : ''}" on:click={() => setVersion('viral')}>
                    Versão Arquetipal
                    <span>Arquétipos · Score 0–100 · Medalhas</span>
                </button>
                <button class="toggle-btn {version === 'dolarize' ? 'on' : ''}" on:click={() => setVersion('dolarize')}>
                    Versão Dólarize
                    <span>USDC · Proteção Cambial · Legado</span>
                </button>
            </div>
            <button class="btn btn-gold" on:click={startQuiz}>Iniciar meu diagnóstico →</button>
            <p style="margin-top:18px;font-size:13px;color:var(--text-dim)">Sem respostas certas ou erradas. Apenas a sua verdade.</p>
        </div>
    </div>
    {/if}

    {#if activeScreen === 's-quiz'}
    <!-- ══════════ QUIZ ══════════ -->
    <div class="screen active">
        <div class="progress-wrap">
            <div class="progress-top">
                <span class="block-label">{q.blockLabel}</span>
                <span class="q-counter">{currentQ + 1} / {QUESTIONS.length}</span>
            </div>
            <div class="bar-track"><div class="bar-fill" style="width: {progress}%"></div></div>
        </div>

        {#if bridging}
        <div class="block-bridge">
            <p class="bridge-text">{bridgeMessage}</p>
        </div>
        {/if}

        <div class="q-card" style={bridging ? 'opacity: 0.3;' : ''}>
            {#key currentQ}
                <div class="q-num">Pergunta {currentQ + 1}</div>
                <div class="q-text">{q.text}</div>
                <div class="opts">
                    {#each q.opts as o}
                        <button class="opt {selected === o.p ? 'sel' : ''}" on:click={() => selectOpt(o.p)}>
                            <span class="opt-lbl">{o.l}</span><span>{o.t}</span>
                        </button>
                    {/each}
                </div>
            {/key}
        </div>

        <div class="nav-btns">
            <button class="btn btn-ghost" on:click={prevQ}>← Voltar</button>
            <button class="btn btn-gold" disabled={selected === null || bridging} on:click={nextQ}>
                {isLast ? 'Ver meu resultado →' : 'Próxima →'}
            </button>
        </div>
    </div>
    {/if}

    {#if activeScreen === 's-capture'}
    <!-- ══════════ CAPTURE ══════════ -->
    <div class="screen active">
        <div class="capture-card">
            <span class="capture-icon">🔐</span>
            <div class="capture-title">Seu diagnóstico está pronto</div>
            <p class="capture-sub">Você respondeu com honestidade. Deixe seu nome para personalizar seu resultado e acompanhar sua evolução.</p>
            <input class="field" bind:value={userName} type="text" placeholder="Seu primeiro nome" />
            <input class="field" bind:value={userPhone} type="text" placeholder="WhatsApp (opcional)" />
            <button class="btn btn-gold btn-block" style="margin-top:4px" on:click={showResult}>Revelar meu nível de evolução →</button>
            <button class="btn btn-ghost btn-block" style="margin-top:10px" on:click={showResult}>Continuar sem identificar</button>
        </div>
    </div>
    {/if}

    {#if activeScreen === 's-result'}
    <!-- ══════════ RESULT ══════════ -->
    <div class="screen active">
        <!-- hero -->
        <div class="result-hero">
            <span class="result-medal">{resultLevel.medal}</span>
            <div class="result-lv-label">SEU NÍVEL DE EVOLUÇÃO PATRIMONIAL</div>
            <div class="result-lv-name" style="color: {resultLevel.color}">
                {version === 'viral' ? resultLevel.arch : `Nível ${resultLevel.id} — ${resultLevel.name}`}
            </div>
            {#if userName}
                <div class="result-greeting">{userName}, bem-vindo à sua realidade.</div>
            {/if}
            <div class="score-box">
                {#if version === 'viral'}
                    <div><span class="sc-num">{resultScore100}</span><span class="sc-lbl">Score / 100</span></div>
                    <div class="sc-sep"></div>
                    <div><span class="sc-num" style="font-size:24px">{resultLevel.pct}</span><span class="sc-lbl">Percentil</span></div>
                    <div class="sc-sep"></div>
                    <div><span class="sc-num">{resultLevel.id}</span><span class="sc-lbl">de 5 Níveis</span></div>
                {:else}
                    <div><span class="sc-num">{resultTotal}</span><span class="sc-lbl">Pontos</span></div>
                    <div class="sc-sep"></div>
                    <div><span class="sc-num">Nível {resultLevel.id}</span><span class="sc-lbl">de 5</span></div>
                {/if}
            </div>
            {#if resultNextLevel}
                <p class="gap-note">Você está a <strong>{resultPtsToNext} pontos</strong> do próximo nível — {version === 'viral' ? resultNextLevel.arch : resultNextLevel.name}</p>
            {/if}
        </div>

        <!-- identity -->
        <div class="r-panel">
            <div class="r-eye">SUA IDENTIDADE ATUAL</div>
            <div class="r-title" style="color: {resultLevel.color}">{resultLevel.identity}</div>
            <p class="r-body">{resultLevel.desc}</p>
            {#if version !== 'viral'}
                <div class="usdc-pill">⬤ USDC · Proteção Cambial · Patrimônio Global</div>
            {/if}
        </div>

        <!-- strengths -->
        <div class="r-panel">
            <div class="r-eye">SUAS FORÇAS</div>
            <ul class="str-list">
                {#each resultLevel.strengths as strength}
                    <li class="str-item"><span class="dot"></span>{strength}</li>
                {/each}
            </ul>
        </div>

        <!-- gap -->
        <div class="r-panel">
            <div class="r-eye">SEU PRINCIPAL GARGALO</div>
            <div class="gap-box"><p class="gap-txt">{resultLevel.gap}</p></div>
        </div>

        <!-- next step -->
        <div class="r-panel">
            <div class="r-eye">PRÓXIMO PASSO</div>
            <div class="next-box"><p class="next-txt">{resultLevel.next}</p></div>
            <div class="daily-box" style="margin-top:10px">
                <div class="daily-lbl">AÇÃO MÍNIMA DIÁRIA</div>
                <p class="daily-txt">{resultLevel.daily}</p>
            </div>
            {#if version !== 'viral'}
                <div class="stage-box">
                    <div class="stage-lbl">ESTÁGIO DÓLARIZE 2.0</div>
                    <div class="stage-txt">{resultLevel.stage}</div>
                </div>
            {/if}
        </div>

        <!-- ladder -->
        {#if version === 'viral'}
        <div class="r-panel">
            <div class="r-eye">MAPA DE EVOLUÇÃO</div>
            {#each LEVELS as l, i}
                <div class="evo-row">
                    <span class="evo-icon">{l.medal}</span>
                    <span class="evo-name" style="color: {l.id === resultLevel.id ? l.color : 'var(--text-md)'}">
                        {l.arch}{l.id === resultLevel.id ? ' ← você' : ''}
                    </span>
                    <div class="evo-track">
                        <div class="evo-fill" style="width: {l.id <= resultLevel.id ? [20,40,60,80,100][i] : 0}%; background: linear-gradient(90deg, {l.color}88, {l.color})"></div>
                    </div>
                    <span class="evo-pct">{l.pct}</span>
                </div>
            {/each}
        </div>
        {/if}

        <div class="transform-section">
            <div class="transform-quote">
                "Você não sobe de nível quando acumula <em>mais dinheiro.</em><br>
                Você sobe de nível quando muda sua <em>identidade.</em>"
            </div>
            <p class="transform-body">O comportamento vem antes do patrimônio. Cada nível representa uma forma diferente de ser — não apenas de ter. Investidores de alto nível tomam decisões melhores por hábito, porque o seu dinheiro não descansa: ele trabalha, protege e se multiplica enquanto eles vivem.</p>
        </div>

        <div class="cta-section">
            <div class="cta-pre">{resultLevel.cta}</div>
            <div class="cta-h">
                {#if resultNextLevel}
                    Avance para {version === 'viral' ? resultNextLevel.arch : `o Nível ${resultNextLevel.id} — ${resultNextLevel.name}`}
                {:else}
                    Você chegou ao topo. É hora de expandir o legado.
                {/if}
            </div>
            <div class="cta-sub">Descubra como o método Dólarize pode acelerar sua evolução patrimonial.</div>
            <button class="btn-cta" on:click={() => goto('/focus-board')}>Quero evoluir agora →</button>
            <button class="restart-btn" on:click={restart}>Refazer o diagnóstico</button>
        </div>
    </div>
    {/if}
</div>

<style>
:global(body) {
  --bg:        #080C18;
  --panel:     #0D1225;
  --panel2:    #111830;
  --border:    #1C2840;
  --border2:   #253352;
  --gold:      #C9A227;
  --gold-lt:   #E8C84A;
  --gold-dim:  #7A611A;
  --teal:      #0DC8C8;
  --teal-dim:  #0A7A7A;
  --text:      #D8DCE8;
  --text-md:   #8A96B0;
  --text-dim:  #3A4560;
  --white:     #F0F2F8;
  --red:       #EF4444;
  --green:     #10B981;

  font-family:'Inter',sans-serif;
  background: radial-gradient(ellipse 120% 80% at 15% 10%, rgba(13,200,200,.05) 0%, transparent 55%),
              radial-gradient(ellipse 100% 70% at 85% 85%, rgba(201,162,39,.06) 0%, transparent 55%),
              var(--bg);
  color: var(--text);
  min-height:100vh;
  overflow-x:hidden;
}

:global(body::after) {
  content:'';
  position:fixed;inset:0;pointer-events:none;z-index:900;
  background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.035'/%3E%3C/svg%3E");
  opacity:.5;
}

:global(*, *::before, *::after) {
  box-sizing:border-box;margin:0;padding:0;
}
:global(html) {
  scroll-behavior:smooth;
}

/* ─────── LAYOUT ─────── */
.wrap { max-width:720px;margin:0 auto;padding:0 20px 80px; }

/* ─────── SCREEN SYSTEM ─────── */
.screen { display:none; }
.screen.active { display:block; }

/* ─────── INTRO ─────── */
.intro-hero { text-align:center;padding:64px 16px 48px; }
.eyebrow { font-family:'DM Mono',monospace;font-size:10px;letter-spacing:4px;color:var(--teal);text-transform:uppercase;margin-bottom:24px; }
.logo { font-family:'Cinzel',serif;font-size:clamp(42px,10vw,68px);font-weight:900;letter-spacing:8px;background:linear-gradient(135deg,var(--gold) 0%,var(--gold-lt) 50%,var(--gold) 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;line-height:1;margin-bottom:6px; }
.logo-sub { font-family:'DM Mono',monospace;font-size:11px;letter-spacing:10px;color:var(--teal);margin-bottom:36px; }
.hero-headline { font-size:clamp(20px,4vw,30px);font-weight:300;color:var(--white);line-height:1.4;max-width:560px;margin:0 auto 12px; }
.hero-sub { font-size:15px;color:var(--text-md);max-width:480px;margin:0 auto 36px;line-height:1.7; }
.divider-gold { width:56px;height:1px;background:linear-gradient(90deg,transparent,var(--gold),transparent);margin:0 auto 36px; }
.stats-row { display:flex;justify-content:center;gap:48px;margin-bottom:44px;flex-wrap:wrap; }
.stat-num { font-family:'Cinzel',serif;font-size:30px;font-weight:700;color:var(--gold);display:block; }
.stat-label { font-family:'DM Mono',monospace;font-size:10px;letter-spacing:2px;color:var(--text-md);text-transform:uppercase;display:block;margin-top:4px; }

/* ─── VERSION TOGGLE ─── */
.toggle-wrap { display:flex;background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:4px;max-width:500px;margin:0 auto 44px; }
.toggle-btn { flex:1;padding:14px 12px;border-radius:8px;border:none;background:transparent;color:var(--text-md);font-family:'Inter',sans-serif;font-size:13px;font-weight:600;cursor:pointer;transition:all .2s;line-height:1.3; }
.toggle-btn.on { background:linear-gradient(135deg,var(--gold),#9A7010);color:#000;box-shadow:0 4px 20px rgba(201,162,39,.3); }
.toggle-btn span { display:block;font-size:10px;font-weight:400;opacity:.7;margin-top:3px; }

/* ─────── BUTTONS ─────── */
.btn { display:inline-flex;align-items:center;gap:8px;padding:16px 36px;border:none;border-radius:8px;font-family:'Inter',sans-serif;font-size:15px;font-weight:700;letter-spacing:.5px;cursor:pointer;transition:all .2s; }
.btn-gold { background:linear-gradient(135deg,var(--gold),#9A7010);color:#000;box-shadow:0 6px 28px rgba(201,162,39,.35); }
.btn-gold:hover { transform:translateY(-2px);box-shadow:0 10px 36px rgba(201,162,39,.48); }
.btn-gold:disabled { opacity:.35;cursor:not-allowed;transform:none; }
.btn-ghost { background:transparent;color:var(--text-md);border:1px solid var(--border); }
.btn-ghost:hover { border-color:var(--gold);color:var(--gold); }
.btn-block { width:100%;justify-content:center; }

/* ─────── PROGRESS ─────── */
.progress-wrap { padding-top:36px;margin-bottom:32px; }
.progress-top { display:flex;justify-content:space-between;align-items:center;margin-bottom:8px; }
.block-label { font-family:'DM Mono',monospace;font-size:9px;letter-spacing:3px;color:var(--teal);text-transform:uppercase; }
.q-counter { font-family:'DM Mono',monospace;font-size:11px;color:var(--text-dim); }
.bar-track { height:2px;background:var(--border);border-radius:2px;overflow:hidden; }
.bar-fill { height:100%;border-radius:2px;background:linear-gradient(90deg,var(--teal),var(--gold));transition:width .4s ease; }

/* ─────── QUESTION ─────── */
.q-card { background:var(--panel);border:1px solid var(--border);border-radius:16px;padding:36px 32px;margin-bottom:20px;animation:fadeUp .3s ease; transition: opacity 0.3s ease; }
@keyframes fadeUp { from{opacity:0;transform:translateY(14px)} to{opacity:1;transform:translateY(0)} }
.q-num { font-family:'DM Mono',monospace;font-size:10px;letter-spacing:3px;color:var(--text-dim);text-transform:uppercase;margin-bottom:14px; }
.q-text { font-size:clamp(17px,2.8vw,22px);font-weight:400;color:var(--white);line-height:1.5;margin-bottom:28px; }
.opts { display:flex;flex-direction:column;gap:10px; }
.opt { display:flex;align-items:flex-start;gap:14px;padding:16px 18px;background:rgba(255,255,255,.02);border:1px solid var(--border);border-radius:10px;cursor:pointer;transition:all .2s;text-align:left;width:100%;color:var(--text);font-family:'Inter',sans-serif;font-size:14px;line-height:1.5; }
.opt:hover { border-color:rgba(201,162,39,.5);background:rgba(201,162,39,.04);color:var(--white); }
.opt.sel { border-color:var(--gold);background:rgba(201,162,39,.1);color:var(--white); }
.opt-lbl { flex-shrink:0;width:28px;height:28px;border-radius:6px;background:rgba(255,255,255,.05);border:1px solid var(--border);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:var(--text-md);transition:all .2s; }
.opt.sel .opt-lbl { background:var(--gold);border-color:var(--gold);color:#000; }

/* ─────── NAV BUTTONS ─────── */
.nav-btns { display:flex;justify-content:space-between;align-items:center;margin-top:4px; }

/* ─────── BLOCK BRIDGE ─────── */
.block-bridge { background:linear-gradient(135deg,rgba(13,200,200,.08),rgba(13,200,200,.02));border:1px solid rgba(13,200,200,.2);border-radius:12px;padding:24px;text-align:center;margin-bottom:28px;animation:fadeUp .4s ease; }
.bridge-text { font-size:15px;color:var(--teal);font-style:italic;font-weight:500; }

/* ─────── CAPTURE ─────── */
.capture-card { background:var(--panel);border:1px solid var(--border);border-radius:16px;padding:44px 36px;text-align:center;margin-top:40px;animation:fadeUp .3s ease; }
.capture-icon { font-size:44px;margin-bottom:20px;display:block; }
.capture-title { font-family:'Cinzel',serif;font-size:clamp(20px,4vw,28px);color:var(--gold);margin-bottom:10px; }
.capture-sub { font-size:15px;color:var(--text-md);max-width:400px;margin:0 auto 28px;line-height:1.7; }
.field { width:100%;padding:14px 18px;background:rgba(255,255,255,.04);border:1px solid var(--border);border-radius:8px;color:var(--white);font-family:'Inter',sans-serif;font-size:15px;margin-bottom:10px;outline:none;transition:border-color .2s; }
.field:focus { border-color:var(--gold); }
.field::placeholder { color:var(--text-dim); }

/* ─────── RESULT ─────── */
.result-hero { text-align:center;padding:52px 16px 40px; }
.result-medal { font-size:64px;display:block;margin-bottom:16px; }
.result-lv-label { font-family:'DM Mono',monospace;font-size:10px;letter-spacing:4px;color:var(--text-md);text-transform:uppercase;margin-bottom:8px; }
.result-lv-name { font-family:'Cinzel',serif;font-size:clamp(32px,8vw,54px);font-weight:900;line-height:1;margin-bottom:10px; }
.result-greeting { font-size:16px;color:var(--text-md);font-style:italic;margin-bottom:28px; }
.score-box { display:inline-flex;align-items:center;gap:28px;background:var(--panel);border:1px solid var(--border);border-radius:14px;padding:18px 32px;margin-bottom:10px;flex-wrap:wrap;justify-content:center; }
.sc-num { font-family:'Cinzel',serif;font-size:38px;font-weight:700;color:var(--gold);display:block;line-height:1; }
.sc-lbl { font-family:'DM Mono',monospace;font-size:10px;letter-spacing:2px;color:var(--text-md);text-transform:uppercase;display:block;margin-top:4px; }
.sc-sep { width:1px;height:44px;background:var(--border); }
.gap-note { font-size:13px;color:var(--text-md);margin-top:10px; }
.gap-note strong { color:var(--gold); }

/* ─── RESULT PANELS ─── */
.r-panel { background:var(--panel);border:1px solid var(--border);border-radius:14px;padding:26px 28px;margin-bottom:14px; }
.r-eye { font-family:'DM Mono',monospace;font-size:10px;letter-spacing:3px;color:var(--teal);text-transform:uppercase;margin-bottom:12px; }
.r-title { font-size:18px;font-weight:600;color:var(--white);margin-bottom:10px; }
.r-body  { font-size:14px;color:var(--text-md);line-height:1.7; }
.str-list { list-style:none;display:flex;flex-direction:column;gap:9px; }
.str-item { display:flex;align-items:flex-start;gap:10px;font-size:14px;color:var(--text);line-height:1.5; }
.dot { width:5px;height:5px;border-radius:50%;background:var(--gold);flex-shrink:0;margin-top:8px; }
.gap-box { background:rgba(239,68,68,.06);border:1px solid rgba(239,68,68,.2);border-radius:8px;padding:16px 18px; }
.gap-txt { font-size:14px;color:#FCA5A5;line-height:1.6; }
.next-box { background:rgba(201,162,39,.07);border:1px solid rgba(201,162,39,.2);border-radius:8px;padding:18px;margin-bottom:10px; }
.next-txt { font-size:14px;color:var(--text);line-height:1.6; }
.daily-box { background:rgba(13,200,200,.07);border:1px solid rgba(13,200,200,.2);border-radius:8px;padding:14px 18px; }
.daily-lbl { font-family:'DM Mono',monospace;font-size:9px;letter-spacing:3px;color:var(--teal);text-transform:uppercase;font-weight:600;margin-bottom:6px; }
.daily-txt { font-size:14px;color:var(--text);line-height:1.5; }
.stage-box { background:rgba(13,200,200,.05);border-left:3px solid var(--teal);padding:14px 18px;border-radius:0 8px 8px 0;margin-top:10px; }
.stage-lbl { font-family:'DM Mono',monospace;font-size:9px;letter-spacing:3px;color:var(--teal);text-transform:uppercase;margin-bottom:5px; }
.stage-txt { font-size:14px;color:var(--text);font-weight:500; }
.usdc-pill { display:inline-flex;align-items:center;gap:6px;background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.3);border-radius:20px;padding:4px 14px;font-size:11px;font-weight:600;color:#34D399;letter-spacing:1px;margin-top:14px; }

/* ─── EVOLUTION LADDER ─── */
.evo-row { display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid rgba(255,255,255,.04); }
.evo-row:last-child { border-bottom:none; }
.evo-icon { font-size:18px;width:28px;text-align:center;flex-shrink:0; }
.evo-name { font-size:13px;font-weight:600;flex:1.2;min-width:120px; }
.evo-track { flex:2;height:4px;background:rgba(255,255,255,.06);border-radius:2px;overflow:hidden; }
.evo-fill { height:100%;border-radius:2px;transition:width 1s ease; }
.evo-pct { font-family:'DM Mono',monospace;font-size:10px;color:var(--text-dim);width:48px;text-align:right; }

/* ─── TRANSFORMATIONAL ─── */
.transform-section { background:linear-gradient(135deg,rgba(201,162,39,.07),rgba(13,200,200,.04));border:1px solid rgba(201,162,39,.2);border-radius:16px;padding:40px 32px;text-align:center;margin:14px 0; }
.transform-quote { font-family:'Cinzel',serif;font-size:clamp(16px,3vw,22px);color:var(--white);line-height:1.5;margin-bottom:20px; }
.transform-quote em { color:var(--gold);font-style:normal; }
.transform-body { font-size:14px;color:var(--text-md);max-width:500px;margin:0 auto;line-height:1.8; }

/* ─── CTA ─── */
.cta-section { text-align:center;padding:40px 16px; }
.cta-pre { font-size:14px;color:var(--text-md);font-style:italic;margin-bottom:14px; }
.cta-h { font-family:'Cinzel',serif;font-size:clamp(18px,3.5vw,26px);color:var(--white);margin-bottom:8px;line-height:1.3; }
.cta-sub { font-size:14px;color:var(--text-md);margin-bottom:28px; }
.btn-cta { display:inline-flex;align-items:center;gap:10px;padding:20px 44px;background:linear-gradient(135deg,var(--gold),#9A7010);color:#000;font-family:'Inter',sans-serif;font-size:16px;font-weight:700;border:none;border-radius:8px;cursor:pointer;box-shadow:0 8px 30px rgba(201,162,39,.4);text-decoration:none;transition:all .2s; }
.btn-cta:hover { transform:translateY(-2px);box-shadow:0 14px 40px rgba(201,162,39,.5); }
.restart-btn { display:block;margin:18px auto 0;background:none;border:none;font-family:'Inter',sans-serif;font-size:13px;color:var(--text-dim);cursor:pointer;text-decoration:underline; }
.restart-btn:hover { color:var(--gold); }

@media(max-width:600px){
  .q-card { padding:22px 18px; }
  .r-panel { padding:18px 16px; }
  .score-box { padding:14px 20px;gap:18px; }
  .transform-section { padding:28px 18px; }
  .capture-card { padding:30px 20px; }
  .nav-btns { flex-direction:column;gap:10px; }
  .nav-btns .btn { width:100%;justify-content:center; }
}
</style>
