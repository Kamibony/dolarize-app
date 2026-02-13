<script>
    import { onMount } from 'svelte';
    import { fade } from 'svelte/transition';

    let users = [];
    let selectedUser = null;
    let chatHistory = [];
    let isLoadingUsers = true;
    let isLoadingHistory = false;

    onMount(async () => {
        try {
            const response = await fetch('http://localhost:8080/admin/users');
            if (response.ok) {
                users = await response.json();
            } else {
                console.error("Failed to fetch users");
            }
        } catch (error) {
            console.error("Error fetching users:", error);
        } finally {
            isLoadingUsers = false;
        }
    });

    async function selectUser(user) {
        selectedUser = user;
        isLoadingHistory = true;
        chatHistory = [];
        try {
            const response = await fetch(`http://localhost:8080/admin/users/${user.id}/history`);
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
        <div class="p-6 border-b border-dolarize-blue-glow/20">
            <h1 class="text-xl font-bold tracking-tight text-white">CRM Admin</h1>
            <span class="text-xs text-dolarize-gold uppercase tracking-widest font-semibold">Dólarize 2.0</span>
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
            <div class="flex-1 flex flex-col items-center justify-center text-gray-600 bg-dolarize-dark/50">
                <div class="w-16 h-16 rounded-full bg-dolarize-blue-glow/10 flex items-center justify-center mb-4">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8 text-dolarize-blue-glow">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                    </svg>
                </div>
                <p class="text-lg font-medium text-gray-400 mb-1">Selecione um Lead</p>
                <p class="text-sm">Clique em um usuário à esquerda para ver o histórico completo.</p>
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
