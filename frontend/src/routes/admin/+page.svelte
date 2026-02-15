<script>
    import { onMount } from 'svelte';
    import { fade } from 'svelte/transition';

    let users = [];
    let selectedUser = null;
    let chatHistory = [];
    let isLoadingUsers = true;
    let isLoadingHistory = false;
    let dashboardStats = null;

    onMount(async () => {
        try {
            const [usersRes, statsRes] = await Promise.all([
                fetch('https://dolarize-api-493794054971.us-central1.run.app/admin/users'),
                fetch('https://dolarize-api-493794054971.us-central1.run.app/admin/stats')
            ]);

            if (usersRes.ok) {
                users = await usersRes.json();
            } else {
                console.error("Failed to fetch users");
            }

            if (statsRes.ok) {
                dashboardStats = await statsRes.json();
            } else {
                console.error("Failed to fetch stats");
            }
        } catch (error) {
            console.error("Error fetching data:", error);
        } finally {
            isLoadingUsers = false;
        }
    });

    async function selectUser(user) {
        selectedUser = user;
        isLoadingHistory = true;
        chatHistory = [];
        try {
            const response = await fetch(`https://dolarize-api-493794054971.us-central1.run.app/admin/users/${user.id}/history`);
            if (response.ok) {
                const historyData = await response.json();

                // Sort interactions chronologically (oldest first)
                // Backend returns DESC (newest first)
                const chronologicalInteractions = [...historyData].reverse();

                let allMessages = [];
                chronologicalInteractions.forEach(interaction => {
                    if (interaction.mensagens) {
                        interaction.mensagens.forEach(msg => {
                            allMessages.push({
                                role: msg.role,
                                content: msg.content,
                                timestamp: interaction.timestamp
                            });
                        });
                    }
                });
                chatHistory = allMessages;
            } else {
                console.error("Failed to fetch history");
            }
        } catch (error) {
            console.error("Error fetching history:", error);
        } finally {
            isLoadingHistory = false;
        }
    }
</script>

<div class="flex h-screen bg-dolarize-dark text-white font-sans overflow-hidden">
    <!-- Sidebar / Master View -->
    <aside class="w-1/3 min-w-[300px] border-r border-dolarize-blue-glow/20 bg-dolarize-dark/95 flex flex-col">
        <div class="p-6 border-b border-dolarize-blue-glow/20 cursor-pointer hover:bg-white/5 transition-colors group" on:click={() => selectedUser = null}>
            <div class="flex items-center gap-2">
                 <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-dolarize-gold group-hover:scale-110 transition-transform">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
                </svg>
                <h1 class="text-xl font-bold tracking-tight text-white">CRM Admin</h1>
            </div>
            <span class="text-xs text-dolarize-gold uppercase tracking-widest font-semibold ml-7">Dólarize 2.0</span>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar">
            {#if isLoadingUsers}
                <div class="p-6 text-center text-gray-500 animate-pulse">Carregando leads...</div>
            {:else if users.length === 0}
                <div class="p-6 text-center text-gray-500">Nenhum usuário encontrado.</div>
            {:else}
                <ul class="divide-y divide-gray-800/50">
                    {#each users as user}
                        <li>
                            <button
                                class={`w-full text-left p-4 hover:bg-white/5 transition-colors ${selectedUser?.id === user.id ? 'bg-white/5 border-l-4 border-dolarize-gold' : 'border-l-4 border-transparent'}`}
                                on:click={() => selectUser(user)}
                            >
                                <div class="flex justify-between items-start mb-1">
                                    <span class="font-semibold text-white truncate pr-2">{user.nome || 'Usuário Sem Nome'}</span>
                                    <span class={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full border ${
                                        user.classificacao_lead?.startsWith('A') ? 'border-green-500/50 text-green-400 bg-green-900/20' :
                                        user.classificacao_lead?.startsWith('B') ? 'border-yellow-500/50 text-yellow-400 bg-yellow-900/20' :
                                        'border-gray-500/50 text-gray-400 bg-gray-900/20'
                                    }`}>
                                        {user.classificacao_lead ? user.classificacao_lead.split(' - ')[0] : 'N/A'}
                                    </span>
                                </div>
                                <div class="text-xs text-gray-400 mb-2 font-mono opacity-70">ID: {user.id}</div>
                                {#if user.tags && user.tags.length > 0}
                                    <div class="flex flex-wrap gap-1">
                                        {#each user.tags as tag}
                                            <span class="text-[10px] px-1.5 py-0.5 bg-dolarize-blue-glow/10 text-blue-200 rounded border border-dolarize-blue-glow/20">#{tag}</span>
                                        {/each}
                                    </div>
                                {/if}
                            </button>
                        </li>
                    {/each}
                </ul>
            {/if}
        </div>
    </aside>

    <!-- Main Content / Detail View -->
    <main class="flex-1 flex flex-col bg-dolarize-dark relative">
        {#if selectedUser}
            <!-- User Header -->
            <header class="px-6 py-4 border-b border-dolarize-blue-glow/20 bg-dolarize-dark/95 backdrop-blur-sm flex justify-between items-center z-10">
                <div>
                    <h2 class="text-lg font-bold text-white tracking-tight">{selectedUser.nome || 'Usuário'}</h2>
                    <p class="text-sm text-gray-400">{selectedUser.telefone || 'Sem telefone'}</p>
                </div>
                <div class="text-right">
                     <div class="text-[10px] text-dolarize-gold uppercase tracking-widest font-semibold mb-1">Nível de Acesso</div>
                     <div class="text-sm text-gray-300 font-medium">{selectedUser.nivel_acesso || 'Desconhecido'}</div>
                </div>
            </header>

            <!-- Chat History -->
            <div class="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
                {#if isLoadingHistory}
                    <div class="flex items-center justify-center h-full">
                        <div class="text-center text-gray-500 animate-pulse">Carregando histórico...</div>
                    </div>
                {:else if chatHistory.length === 0}
                    <div class="flex items-center justify-center h-full">
                        <div class="text-center text-gray-600">Nenhuma interação registrada.</div>
                    </div>
                {:else}
                    {#each chatHistory as msg}
                         <div class={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`} in:fade>
                            <div class={`
                                max-w-[80%] p-4 rounded-lg text-sm shadow-md relative
                                ${msg.role === 'user'
                                    ? 'bg-dolarize-blue-glow/10 text-gray-200 border border-dolarize-blue-glow/30 rounded-tr-none'
                                    : 'bg-dolarize-card text-gray-100 border-l-2 border-dolarize-gold rounded-tl-none'
                                }
                            `}>
                                <div class="flex justify-between items-center mb-2 pb-2 border-b border-white/5 gap-4">
                                    <span class="text-[10px] opacity-70 uppercase tracking-wider font-bold">
                                        {msg.role === 'user' ? 'Lead' : 'André Digital'}
                                    </span>
                                    {#if msg.timestamp}
                                        <span class="text-[10px] opacity-40 font-mono">
                                            {new Date(msg.timestamp).toLocaleString()}
                                        </span>
                                    {/if}
                                </div>
                                <p class="leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                            </div>
                        </div>
                    {/each}
                {/if}
            </div>
        {:else}
            <!-- Executive Dashboard -->
            <div class="flex-1 flex flex-col p-6 overflow-y-auto custom-scrollbar bg-gradient-to-br from-dolarize-dark to-dolarize-card" in:fade>
                <div class="mb-8">
                    <h1 class="text-2xl font-bold tracking-tight text-white mb-2">Painel Executivo</h1>
                    <p class="text-sm text-gray-400">Visão geral de desempenho e leads</p>
                </div>

                <!-- KPI Cards -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <!-- Total Leads -->
                    <div class="bg-dolarize-card p-6 rounded-lg border border-dolarize-blue-glow/20 relative overflow-hidden shadow-lg">
                        <div class="absolute top-0 right-0 p-4 opacity-10">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
                        </div>
                        <h3 class="text-xs font-semibold text-dolarize-gold uppercase tracking-wider mb-1">Total de Leads</h3>
                        <div class="text-3xl font-bold text-white">{dashboardStats ? dashboardStats.total_leads : '...'}</div>
                    </div>

                    <!-- Conversion Rate -->
                    <div class="bg-dolarize-card p-6 rounded-lg border border-dolarize-blue-glow/20 relative overflow-hidden shadow-lg">
                        <div class="absolute top-0 right-0 p-4 opacity-10">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
                        </div>
                        <h3 class="text-xs font-semibold text-dolarize-gold uppercase tracking-wider mb-1">Conversão (Perfil A)</h3>
                        <div class="text-3xl font-bold text-white">{dashboardStats ? dashboardStats.conversion_rate_a + '%' : '...'}</div>
                    </div>

                    <!-- Funnel Distribution -->
                    <div class="bg-dolarize-card p-6 rounded-lg border border-dolarize-blue-glow/20 relative overflow-hidden shadow-lg">
                         <div class="absolute top-0 right-0 p-4 opacity-10">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
                        </div>
                        <h3 class="text-xs font-semibold text-dolarize-gold uppercase tracking-wider mb-1">Distribuição do Funil</h3>
                        <div class="flex items-end space-x-4 text-sm mt-2">
                            <div class="flex flex-col items-center">
                                <span class="text-green-400 font-bold text-lg">{dashboardStats ? dashboardStats.funnel_distribution.A : 0}</span>
                                <span class="text-[10px] text-gray-500 font-bold">A</span>
                            </div>
                            <div class="w-px h-8 bg-gray-700/50"></div>
                            <div class="flex flex-col items-center">
                                <span class="text-yellow-400 font-bold text-lg">{dashboardStats ? dashboardStats.funnel_distribution.B : 0}</span>
                                <span class="text-[10px] text-gray-500 font-bold">B</span>
                            </div>
                            <div class="w-px h-8 bg-gray-700/50"></div>
                            <div class="flex flex-col items-center">
                                <span class="text-gray-400 font-bold text-lg">{dashboardStats ? dashboardStats.funnel_distribution.C : 0}</span>
                                <span class="text-[10px] text-gray-500 font-bold">C</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Lead Management Grid -->
                <div class="bg-dolarize-card rounded-lg border border-dolarize-blue-glow/20 flex flex-col flex-1 overflow-hidden shadow-xl">
                    <div class="p-4 border-b border-white/5 bg-white/5 flex justify-between items-center">
                        <h3 class="text-sm font-bold text-white uppercase tracking-wide">Gerenciamento de Leads</h3>
                        <span class="text-xs text-gray-400">{users.length} leads encontrados</span>
                    </div>
                    <div class="overflow-auto custom-scrollbar flex-1">
                        <table class="w-full text-left border-collapse">
                            <thead class="bg-black/20 text-xs text-gray-400 uppercase font-semibold sticky top-0 z-10 backdrop-blur-sm">
                                <tr>
                                    <th class="p-4 border-b border-white/5">Lead</th>
                                    <th class="p-4 border-b border-white/5">Status</th>
                                    <th class="p-4 border-b border-white/5 hidden md:table-cell">Dor Principal</th>
                                    <th class="p-4 border-b border-white/5 hidden md:table-cell">Maturidade</th>
                                    <th class="p-4 border-b border-white/5 text-right">Ação</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-white/5 text-sm">
                                {#each users as user}
                                <tr class="hover:bg-white/5 transition-colors group">
                                    <td class="p-4 font-medium text-white">
                                        <div class="font-bold text-gray-200 group-hover:text-white transition-colors">{user.nome || 'Sem Nome'}</div>
                                        <div class="text-[10px] text-gray-500 font-mono">{user.id.substring(0, 8)}...</div>
                                    </td>
                                    <td class="p-4">
                                        <span class={`text-[10px] uppercase font-bold px-2 py-1 rounded-full border shadow-sm ${
                                            user.classificacao_lead?.startsWith('A') ? 'border-green-500/50 text-green-300 bg-green-900/30' :
                                            user.classificacao_lead?.startsWith('B') ? 'border-yellow-500/50 text-yellow-300 bg-yellow-900/30' :
                                            'border-gray-500/50 text-gray-400 bg-gray-800/50'
                                        }`}>
                                            {user.classificacao_lead ? user.classificacao_lead.split(' - ')[0] : 'N/A'}
                                        </span>
                                    </td>
                                    <td class="p-4 text-gray-400 hidden md:table-cell max-w-[150px] truncate" title={user.dor_principal}>{user.dor_principal || '-'}</td>
                                    <td class="p-4 text-gray-400 hidden md:table-cell capitalize">{user.maturidade || '-'}</td>
                                    <td class="p-4 text-right">
                                        <button
                                            class="text-[10px] font-bold text-dolarize-gold hover:text-white uppercase tracking-wider px-3 py-1.5 border border-dolarize-gold/30 rounded hover:bg-dolarize-gold/10 transition-all hover:border-dolarize-gold/80"
                                            on:click={() => selectUser(user)}
                                        >
                                            Inspecionar
                                        </button>
                                    </td>
                                </tr>
                                {/each}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        {/if}
    </main>
</div>

<style>
    /* Custom Scrollbar for Webkit */
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
