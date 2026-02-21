<script>
    import { onMount } from 'svelte';
    import { page } from '$app/stores';
    import { fade } from 'svelte/transition';

    let user = null;
    let insights = null;
    let history = [];
    let isLoading = true;
    let error = null;
    let isHistoryOpen = false;

    // Use specific endpoint for this page
    const userId = $page.params.id;
    const API_BASE_URL = import.meta.env.PUBLIC_API_URL || 'https://dolarize-api-493794054971.us-central1.run.app';

    async function loadData() {
        isLoading = true;
        try {
            // Fetch Lead Insights (Backend handles generation/retrieval)
            const res = await fetch(`${API_BASE_URL}/admin/lead/${userId}/insights`);

            if (res.ok) {
                const data = await res.json();
                user = data.user;
                insights = data.insights;
                history = data.history || []; // Backend should return history too for timeline/full chat
            } else {
                const err = await res.json();
                error = err.detail || "Erro ao carregar lead.";
            }
        } catch (e) {
            error = "Erro de conexão com o servidor.";
            console.error(e);
        } finally {
            isLoading = false;
        }
    }

    async function sendPaymentLink() {
        if (!confirm("Gerar e enviar link de pagamento via WhatsApp? (Simulação)")) return;
        alert("Funcionalidade em desenvolvimento (Fase 2).");
    }

    function getStatusColor(status) {
        if (status === 'Aluno') return 'text-green-400 bg-green-900/20 border-green-500/50';
        return 'text-yellow-400 bg-yellow-900/20 border-yellow-500/50';
    }

    function getProfileColor(profile) {
        if (!profile) return 'text-gray-400 bg-gray-900/20 border-gray-500/50';
        if (profile.startsWith('A')) return 'text-green-400 bg-green-900/20 border-green-500/50';
        if (profile.startsWith('B')) return 'text-yellow-400 bg-yellow-900/20 border-yellow-500/50';
        return 'text-blue-400 bg-blue-900/20 border-blue-500/50';
    }

    onMount(() => {
        loadData();
    });
</script>

<div class="min-h-screen bg-dolarize-dark text-white font-sans flex flex-col">
    <!-- Navigation Bar -->
    <div class="p-4 border-b border-dolarize-blue-glow/20 bg-black/20 backdrop-blur-sm flex items-center gap-4">
        <a href="/admin" class="text-gray-400 hover:text-white transition-colors flex items-center gap-1 text-sm font-bold uppercase tracking-wider">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4">
              <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
            </svg>
            Voltar
        </a>
        <h1 class="text-lg font-bold tracking-tight text-white border-l border-gray-700 pl-4">Lead Command Center</h1>
    </div>

    {#if isLoading}
        <div class="flex-1 flex flex-col items-center justify-center">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-dolarize-gold mb-4"></div>
            <p class="text-dolarize-gold font-mono animate-pulse">Analisando Lead com IA...</p>
        </div>
    {:else if error}
        <div class="flex-1 flex items-center justify-center">
            <div class="bg-red-900/20 border border-red-500/50 p-6 rounded-lg max-w-md text-center">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-12 h-12 mx-auto text-red-500 mb-4">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                </svg>
                <h3 class="text-lg font-bold text-white mb-2">Erro</h3>
                <p class="text-gray-400">{error}</p>
                <button on:click={loadData} class="mt-4 px-4 py-2 bg-white/10 hover:bg-white/20 rounded text-sm font-bold transition-colors">Tentar Novamente</button>
            </div>
        </div>
    {:else if user}
        <div class="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 custom-scrollbar" in:fade>

            <!-- 1. Identity Header -->
            <section class="bg-dolarize-card border border-dolarize-blue-glow/20 rounded-lg p-6 shadow-lg relative overflow-hidden">
                <div class="absolute top-0 right-0 p-6 opacity-10 pointer-events-none">
                     <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-32 h-32 text-dolarize-gold">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                    </svg>
                </div>

                <div class="flex flex-col md:flex-row md:items-start justify-between gap-6 relative z-10">
                    <div>
                        <div class="flex items-center gap-3 mb-2">
                            <h2 class="text-3xl font-bold text-white tracking-tight">{user.nome || 'Lead Sem Nome'}</h2>
                            <span class={`text-xs font-bold px-2 py-1 rounded border uppercase tracking-wider ${getStatusColor(user.status)}`}>
                                {user.status || 'Interessado'}
                            </span>
                        </div>
                        <div class="flex flex-col gap-1 text-sm text-gray-400 mb-4 font-mono">
                            <div class="flex items-center gap-2">
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 text-dolarize-gold">
                                  <path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
                                </svg>
                                {user.email || 'E-mail não capturado'}
                            </div>
                            <div class="flex items-center gap-2">
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 text-dolarize-gold">
                                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z" />
                                </svg>
                                {user.telefone || 'Telefone não capturado'}
                            </div>
                        </div>

                        {#if user.dor_principal}
                            <div class="inline-block bg-white/5 border border-white/10 rounded-lg p-3">
                                <div class="text-[10px] text-dolarize-gold uppercase tracking-widest font-bold mb-1">Dor Principal Identificada</div>
                                <div class="text-white italic">"{user.dor_principal}"</div>
                            </div>
                        {/if}
                    </div>

                    <div class="flex flex-col items-end gap-2">
                         <div class="text-right">
                             <div class="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-1">Classificação (Lead Scoring)</div>
                             <span class={`text-sm font-bold px-3 py-1.5 rounded border uppercase tracking-wide ${getProfileColor(user.classificacao_lead)}`}>
                                 {user.classificacao_lead || 'Não Classificado'}
                             </span>
                         </div>
                         <div class="text-right mt-2">
                              <div class="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-1">Última Interação</div>
                              <div class="text-sm text-gray-300 font-mono">
                                  {user.last_interaction_timestamp ? new Date(user.last_interaction_timestamp).toLocaleString() : 'N/A'}
                              </div>
                         </div>
                    </div>
                </div>
            </section>

            <!-- 2. AI Insights Panel -->
            <section class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <!-- Summary -->
                <div class="bg-dolarize-card border border-dolarize-blue-glow/20 rounded-lg p-6 shadow-lg flex flex-col">
                    <div class="flex items-center gap-2 mb-4">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-blue-400">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
                        </svg>
                        <h3 class="text-sm font-bold text-white uppercase tracking-wider">Resumo do Perfil</h3>
                    </div>
                    <p class="text-sm text-gray-300 leading-relaxed flex-1">
                        {insights?.summary || 'Aguardando análise da IA...'}
                    </p>
                </div>

                <!-- Objection -->
                <div class="bg-dolarize-card border border-dolarize-blue-glow/20 rounded-lg p-6 shadow-lg flex flex-col">
                    <div class="flex items-center gap-2 mb-4">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-red-400">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                        </svg>
                        <h3 class="text-sm font-bold text-white uppercase tracking-wider">Principal Objeção</h3>
                    </div>
                    <p class="text-sm text-gray-300 leading-relaxed flex-1 italic border-l-2 border-red-500/30 pl-3">
                        "{insights?.objection || 'Não identificada.'}"
                    </p>
                </div>

                <!-- Sales Strategy -->
                <div class="bg-dolarize-card border border-dolarize-blue-glow/20 rounded-lg p-6 shadow-lg flex flex-col relative overflow-hidden">
                     <div class="absolute inset-0 bg-gradient-to-br from-dolarize-gold/5 to-transparent pointer-events-none"></div>
                    <div class="flex items-center gap-2 mb-4 relative z-10">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-dolarize-gold">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.631 8.41m5.96 5.96a14.926 14.926 0 01-5.841 2.58m-.119-8.54a6 6 0 00-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 00-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 01-2.448-2.448 14.9 14.9 0 01.06-.312m-2.24 2.39a4.493 4.493 0 00-1.757 4.306 4.493 4.493 0 004.306-1.758M16.5 9a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
                        </svg>
                        <h3 class="text-sm font-bold text-dolarize-gold uppercase tracking-wider">Estratégia Recomendada</h3>
                    </div>
                    <p class="text-sm text-white font-medium leading-relaxed flex-1 relative z-10">
                        {insights?.sales_angle || 'Aguardando análise...'}
                    </p>
                </div>
            </section>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- 3. Journey Timeline -->
                <div class="lg:col-span-2 bg-dolarize-card border border-dolarize-blue-glow/20 rounded-lg p-6 shadow-lg">
                    <h3 class="text-sm font-bold text-white uppercase tracking-wider mb-6 flex items-center gap-2">
                         <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-gray-400">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Jornada do Lead
                    </h3>

                    <div class="relative border-l border-gray-700 ml-3 space-y-8">
                        {#each (isHistoryOpen ? history.slice().reverse() : history.slice().reverse().slice(0, 5)) as event, i}
                             <div class="mb-10 ml-6 relative group">
                                <span class={`absolute flex items-center justify-center w-6 h-6 rounded-full -left-9 ring-4 ring-dolarize-dark ${event.role === 'user' ? 'bg-blue-500' : 'bg-gray-600'}`}>
                                    {#if event.role === 'user'}
                                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-3 h-3 text-white">
                                          <path d="M10 8a3 3 0 100-6 3 3 0 000 6zM3.465 14.493a1.23 1.23 0 00.41 1.412A9.957 9.957 0 0010 18c2.31 0 4.438-.784 6.131-2.1.43-.333.604-.903.408-1.41a7.002 7.002 0 00-13.074.003z" />
                                        </svg>
                                    {:else}
                                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-3 h-3 text-white">
                                          <path fill-rule="evenodd" d="M10 2c-1.716 0-3.408.106-5.07.31C3.806 2.45 3 3.414 3 4.517V17.25a.75.75 0 001.075.676L10 15.082l5.925 2.844A.75.75 0 0017 17.25V4.517c0-1.103-.806-2.068-1.93-2.207A41.403 41.403 0 0010 2z" clip-rule="evenodd" />
                                        </svg>
                                    {/if}
                                </span>
                                <div class="flex items-center justify-between mb-1">
                                    <h4 class="flex items-center text-sm font-semibold text-white">
                                        {event.role === 'user' ? 'Lead' : 'André Digital'}
                                        {#if event.role === 'user' && i === 0}
                                            <span class="bg-blue-100 text-blue-800 text-[10px] font-medium mr-2 px-2.5 py-0.5 rounded ml-2">Última</span>
                                        {/if}
                                    </h4>
                                    <time class="block mb-1 text-xs font-normal text-gray-500 font-mono">
                                        {event.timestamp ? new Date(event.timestamp).toLocaleString() : 'Data N/A'}
                                    </time>
                                </div>
                                <p class="mb-4 text-sm font-normal text-gray-400 bg-black/20 p-3 rounded border border-white/5 whitespace-pre-wrap max-h-32 overflow-hidden relative group-hover:max-h-full transition-all">
                                    {event.content || (Array.isArray(event.parts) ? event.parts[0] : event.parts) || '...'}
                                </p>
                            </div>
                        {/each}
                        {#if !isHistoryOpen && history.length > 5}
                            <div class="ml-6 mb-10">
                                <button
                                    on:click={() => isHistoryOpen = true}
                                    class="text-xs text-dolarize-gold hover:text-white underline italic"
                                >
                                    + Ver {history.length - 5} interações anteriores...
                                </button>
                            </div>
                        {/if}
                         <!-- Start Node -->
                        <div class="ml-6">
                            <span class="absolute flex items-center justify-center w-6 h-6 bg-green-500 rounded-full -left-9 ring-4 ring-dolarize-dark">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-3 h-3 text-white">
                                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm.75-11.25a.75.75 0 00-1.5 0v2.5h-2.5a.75.75 0 000 1.5h2.5v2.5a.75.75 0 001.5 0v-2.5h2.5a.75.75 0 000-1.5h-2.5v-2.5z" clip-rule="evenodd" />
                                </svg>
                            </span>
                            <h3 class="font-medium leading-tight text-white">Início da Jornada</h3>
                            <p class="text-sm text-gray-500">Cadastro/Primeiro contato</p>
                        </div>
                    </div>
                </div>

                <!-- 4. Action Hub -->
                <div class="space-y-6">
                    <div class="bg-dolarize-card border border-dolarize-blue-glow/20 rounded-lg p-6 shadow-lg">
                        <h3 class="text-sm font-bold text-white uppercase tracking-wider mb-4">Ações Rápidas</h3>
                        <div class="space-y-3">
                             <button
                                on:click={() => isHistoryOpen = !isHistoryOpen}
                                class="w-full py-3 px-4 bg-white/5 hover:bg-white/10 border border-white/10 rounded text-sm font-bold text-white transition-colors flex items-center justify-center gap-2"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                                  <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
                                </svg>
                                {isHistoryOpen ? 'Ocultar Chat Completo' : 'Ver Chat Completo'}
                            </button>

                            <button
                                on:click={sendPaymentLink}
                                class="w-full py-3 px-4 bg-green-600 hover:bg-green-500 text-white rounded text-sm font-bold transition-colors flex items-center justify-center gap-2 shadow-lg shadow-green-900/20"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
                                </svg>
                                Enviar Link de Pagamento
                            </button>

                            <button
                                disabled
                                class="w-full py-3 px-4 bg-gray-700/50 border border-gray-600 text-gray-400 rounded text-sm font-bold cursor-not-allowed flex items-center justify-center gap-2"
                                title="Em breve"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                                  <path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.159 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
                                </svg>
                                Mensagem Manual (WhatsApp)
                            </button>
                        </div>
                    </div>

                    <!-- AI Status -->
                    <div class="bg-black/20 border border-white/5 rounded-lg p-4">
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-xs font-bold text-gray-400 uppercase">Status do Agente</span>
                            <div class="flex items-center gap-2">
                                <span class={`w-2 h-2 rounded-full ${user.bot_paused ? 'bg-yellow-500' : 'bg-green-500'} animate-pulse`}></span>
                                <span class="text-xs text-white">{user.bot_paused ? 'Pausado' : 'Ativo'}</span>
                            </div>
                        </div>
                        <p class="text-[10px] text-gray-500 leading-tight">
                            {user.bot_paused
                                ? 'O agente não responderá a novas mensagens deste lead.'
                                : 'O agente está monitorando e respondendo automaticamente.'}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    {/if}
</div>

<style>
    /* Custom Scrollbar */
    .custom-scrollbar::-webkit-scrollbar {
        width: 6px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
        background: rgba(11, 19, 43, 0.5);
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
        background-color: rgba(30, 64, 175, 0.3);
        border-radius: 3px;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover {
        background-color: rgba(197, 160, 89, 0.5);
    }
</style>
