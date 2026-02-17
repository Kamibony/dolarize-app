<script>
    import { onMount } from 'svelte';
    import { fade } from 'svelte/transition';

    let users = [];
    let selectedUser = null;
    let chatHistory = [];
    let isLoadingUsers = true;
    let isLoadingHistory = false;
    let dashboardStats = null;

    // CRM vs KB vs Config vs Videos Mode
    let mode = 'crm'; // 'crm' | 'kb' | 'config' | 'videos'

    // Knowledge Base State
    let activeKbTab = 'knowledge'; // 'knowledge' | 'persona'
    let knowledgeFiles = [];
    let isLoadingFiles = false;
    let isUploading = false;
    let uploadStatus = ''; // 'success', 'error', ''
    let fileInput;

    // Config State
    let corePromptText = '';
    let isLoadingPrompt = false;
    let isSavingPrompt = false;
    let promptStatus = ''; // 'saved', 'reset', 'error', ''

    // Video State
    let videos = [];
    let isLoadingVideos = false;
    let isSavingVideo = false;
    let videoForm = { id: null, title: '', url: '', trigger_context: '' };
    let isEditingVideo = false;

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

    // Fetch data based on mode
    $: if (mode === 'kb') {
        fetchFiles();
    } else if (mode === 'config') {
        fetchCorePrompt();
    } else if (mode === 'videos') {
        fetchVideos();
    }

    async function fetchCorePrompt() {
        isLoadingPrompt = true;
        promptStatus = '';
        try {
            const res = await fetch('https://dolarize-api-493794054971.us-central1.run.app/admin/config/core-prompt');
            if (res.ok) {
                const data = await res.json();
                corePromptText = data.prompt;
            } else {
                console.error("Failed to fetch prompt");
            }
        } catch (e) {
            console.error("Error fetching prompt:", e);
        } finally {
            isLoadingPrompt = false;
        }
    }

    async function saveCorePrompt() {
        if (!confirm('ATENÇÃO: Você está prestes a alterar o comportamento fundamental da IA. Tem certeza?')) return;

        isSavingPrompt = true;
        promptStatus = '';
        try {
            const res = await fetch('https://dolarize-api-493794054971.us-central1.run.app/admin/config/core-prompt', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: corePromptText })
            });

            if (res.ok) {
                promptStatus = 'saved';
            } else {
                promptStatus = 'error';
            }
        } catch (e) {
            console.error("Error saving prompt:", e);
            promptStatus = 'error';
        } finally {
            isSavingPrompt = false;
        }
    }

    async function resetCorePrompt() {
        if (!confirm('ATENÇÃO: Isso irá apagar todas as personalizações e restaurar o prompt original de fábrica. Esta ação é irreversível. Continuar?')) return;

        isSavingPrompt = true; // Use same loading state
        promptStatus = '';
        try {
            const res = await fetch('https://dolarize-api-493794054971.us-central1.run.app/admin/config/core-prompt/reset', {
                method: 'POST'
            });

            if (res.ok) {
                promptStatus = 'reset';
                await fetchCorePrompt(); // Reload text
            } else {
                promptStatus = 'error';
            }
        } catch (e) {
            console.error("Error resetting prompt:", e);
            promptStatus = 'error';
        } finally {
            isSavingPrompt = false;
        }
    }

    async function fetchFiles() {
        isLoadingFiles = true;
        try {
            const res = await fetch(`https://dolarize-api-493794054971.us-central1.run.app/admin/knowledge/files?type=${activeKbTab}`);
            if (res.ok) {
                knowledgeFiles = await res.json();
            } else {
                console.error("Failed to fetch files");
            }
        } catch (e) {
            console.error("Error fetching files:", e);
        } finally {
            isLoadingFiles = false;
        }
    }

    function switchKbTab(tab) {
        activeKbTab = tab;
        fetchFiles();
    }

    async function handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        isUploading = true;
        uploadStatus = '';

        const formData = new FormData();
        formData.append('file', file);
        formData.append('file_type', activeKbTab);

        try {
            const res = await fetch('https://dolarize-api-493794054971.us-central1.run.app/admin/knowledge/upload', {
                method: 'POST',
                body: formData
            });

            if (res.ok) {
                uploadStatus = 'success';
                await fetchFiles(); // Refresh list
            } else {
                uploadStatus = 'error';
                console.error("Upload failed");
            }
        } catch (e) {
            console.error("Upload error:", e);
            uploadStatus = 'error';
        } finally {
            isUploading = false;
            if (fileInput) fileInput.value = ''; // Reset input
        }
    }

    async function deleteFile(fileId) {
        if (!confirm('Tem certeza que deseja excluir este arquivo? A IA deixará de utilizá-lo.')) return;

        try {
            const res = await fetch(`https://dolarize-api-493794054971.us-central1.run.app/admin/knowledge/files/${fileId}`, {
                method: 'DELETE'
            });

            if (res.ok) {
                await fetchFiles();
            } else {
                alert("Erro ao excluir arquivo.");
            }
        } catch (e) {
            console.error("Delete error:", e);
            alert("Erro ao excluir arquivo.");
        }
    }

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

    async function toggleBotPause(user) {
        if (!user) return;
        const newStatus = !user.bot_paused;

        try {
            const res = await fetch(`https://dolarize-api-493794054971.us-central1.run.app/admin/users/${user.id}/toggle-bot`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ paused: newStatus })
            });

            if (res.ok) {
                // Update local state
                user.bot_paused = newStatus;
                users = users; // Trigger reactivity
                selectedUser = user; // Trigger reactivity
            } else {
                console.error("Failed to toggle bot pause");
                alert("Erro ao alterar status do bot.");
            }
        } catch (e) {
            console.error("Error toggling bot pause:", e);
            alert("Erro ao alterar status do bot.");
        }
    }

    // Video Functions
    async function fetchVideos() {
        isLoadingVideos = true;
        try {
            const res = await fetch('https://dolarize-api-493794054971.us-central1.run.app/admin/videos');
            if (res.ok) {
                videos = await res.json();
            } else {
                console.error("Failed to fetch videos");
            }
        } catch (e) {
            console.error("Error fetching videos:", e);
        } finally {
            isLoadingVideos = false;
        }
    }

    function editVideo(video) {
        videoForm = { ...video };
        isEditingVideo = true;
    }

    function cancelEditVideo() {
        videoForm = { id: null, title: '', url: '', trigger_context: '' };
        isEditingVideo = false;
    }

    async function saveVideo() {
        if (!videoForm.title || !videoForm.url || !videoForm.trigger_context) {
            alert("Preencha todos os campos.");
            return;
        }

        isSavingVideo = true;
        try {
            const method = videoForm.id ? 'PUT' : 'POST';
            const url = videoForm.id
                ? `https://dolarize-api-493794054971.us-central1.run.app/admin/videos/${videoForm.id}`
                : 'https://dolarize-api-493794054971.us-central1.run.app/admin/videos';

            const res = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: videoForm.title,
                    url: videoForm.url,
                    trigger_context: videoForm.trigger_context
                })
            });

            if (res.ok) {
                await fetchVideos();
                cancelEditVideo();
            } else {
                alert("Erro ao salvar vídeo.");
            }
        } catch (e) {
            console.error("Error saving video:", e);
            alert("Erro ao salvar vídeo.");
        } finally {
            isSavingVideo = false;
        }
    }

    async function deleteVideo(videoId) {
        if (!confirm('Tem certeza que deseja excluir este vídeo?')) return;

        try {
            const res = await fetch(`https://dolarize-api-493794054971.us-central1.run.app/admin/videos/${videoId}`, {
                method: 'DELETE'
            });

            if (res.ok) {
                await fetchVideos();
            } else {
                alert("Erro ao excluir vídeo.");
            }
        } catch (e) {
            console.error("Delete error:", e);
            alert("Erro ao excluir vídeo.");
        }
    }
</script>

<div class="flex h-screen bg-dolarize-dark text-white font-sans overflow-hidden">
    <!-- Sidebar / Master View -->
    <aside class="w-1/3 min-w-[300px] border-r border-dolarize-blue-glow/20 bg-dolarize-dark/95 flex flex-col">
        <div class="p-6 border-b border-dolarize-blue-glow/20">
            <div class="flex items-center gap-2 mb-4 cursor-pointer" on:click={() => { selectedUser = null; mode = 'crm'; }}>
                 <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-dolarize-gold">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
                </svg>
                <h1 class="text-xl font-bold tracking-tight text-white">Admin Console</h1>
            </div>

            <!-- Navigation Tabs -->
            <div class="flex space-x-1 bg-black/20 p-1 rounded-lg">
                <button
                    class={`flex-1 text-xs font-bold uppercase tracking-wider py-2 rounded-md transition-all ${mode === 'crm' ? 'bg-dolarize-gold text-dolarize-dark shadow' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
                    on:click={() => { mode = 'crm'; selectedUser = null; }}
                >
                    CRM
                </button>
                <button
                    class={`flex-1 text-xs font-bold uppercase tracking-wider py-2 rounded-md transition-all ${mode === 'videos' ? 'bg-dolarize-gold text-dolarize-dark shadow' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
                    on:click={() => { mode = 'videos'; selectedUser = null; }}
                >
                    Vídeos
                </button>
                <button
                    class={`flex-1 text-xs font-bold uppercase tracking-wider py-2 rounded-md transition-all ${mode === 'kb' ? 'bg-dolarize-gold text-dolarize-dark shadow' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
                    on:click={() => { mode = 'kb'; selectedUser = null; }}
                >
                    Conhecimento
                </button>
                <button
                    class={`flex-1 text-xs font-bold uppercase tracking-wider py-2 rounded-md transition-all ${mode === 'config' ? 'bg-red-500 text-white shadow' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
                    on:click={() => { mode = 'config'; selectedUser = null; }}
                >
                    Nuclear
                </button>
            </div>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar">
            {#if mode === 'crm'}
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
            {:else if mode === 'videos'}
                <!-- Videos Info -->
                <div class="p-6 text-sm text-gray-400 space-y-4">
                    <p>Central de Vídeos Inteligente.</p>
                    <p>Cadastre vídeos que a IA recomendará estrategicamente durante as conversas.</p>
                    <div class="bg-dolarize-gold/10 border border-dolarize-gold/30 p-3 rounded text-xs text-yellow-200">
                        Nota: A IA apenas recomendará vídeos para leads qualificados (Perfil A ou B).
                    </div>
                </div>
            {:else if mode === 'kb'}
                <!-- Knowledge Base Info -->
                <div class="p-6 text-sm text-gray-400 space-y-4">
                    <p>Gerencie aqui os arquivos que compõem o "cérebro" do André Digital.</p>
                    <p>O agente consultará estes documentos para responder perguntas técnicas.</p>
                    <div class="bg-blue-900/20 border border-blue-500/30 p-3 rounded text-xs text-blue-200">
                        Arquivos suportados: PDF, DOCX, TXT.
                    </div>
                </div>
            {:else if mode === 'config'}
                 <!-- Config Info -->
                <div class="p-6 text-sm text-gray-400 space-y-4">
                    <div class="bg-red-900/20 border border-red-500/30 p-4 rounded text-xs text-red-200 font-bold flex items-start gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-6 h-6 shrink-0">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                        </svg>
                        <p>AVISO: Esta área altera o DNA do agente. Edições incorretas podem quebrar a lógica de segurança.</p>
                    </div>
                    <p>Aqui você edita o "Prompt do Sistema" (System Prompt), que define a identidade e as regras imutáveis do André Digital.</p>
                    <p class="text-xs text-gray-500">Este texto tem precedência sobre todos os arquivos de conhecimento.</p>
                </div>
            {/if}
        </div>
    </aside>

    <!-- Main Content / Detail View -->
    <main class="flex-1 flex flex-col bg-dolarize-dark relative">
        {#if mode === 'crm'}
            {#if selectedUser}
                <!-- User Header -->
                <header class="px-6 py-4 border-b border-dolarize-blue-glow/20 bg-dolarize-dark/95 backdrop-blur-sm flex justify-between items-center z-10">
                    <div>
                        <div class="flex items-center gap-3">
                            <h2 class="text-lg font-bold text-white tracking-tight">{selectedUser.nome || 'Usuário'}</h2>
                             <button
                                on:click={() => toggleBotPause(selectedUser)}
                                class={`text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded transition-all border flex items-center gap-1 ${selectedUser.bot_paused ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50 hover:bg-yellow-500/30' : 'bg-green-500/20 text-green-400 border-green-500/50 hover:bg-green-500/30'}`}
                                title={selectedUser.bot_paused ? "Clique para reativar a IA" : "Clique para pausar a IA e assumir o chat"}
                            >
                                {#if selectedUser.bot_paused}
                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-3 h-3">
                                      <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                                    </svg>
                                    IA Pausada
                                {:else}
                                     <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-3 h-3">
                                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd" />
                                    </svg>
                                    IA Ativa
                                {/if}
                            </button>
                        </div>
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
                                        <th class="p-4 border-b border-white/5">ID</th>
                                        <th class="p-4 border-b border-white/5">Nome</th>
                                        <th class="p-4 border-b border-white/5">E-mail</th>
                                        <th class="p-4 border-b border-white/5">Status</th>
                                        <th class="p-4 border-b border-white/5 hidden md:table-cell">Dor Principal</th>
                                        <th class="p-4 border-b border-white/5 hidden md:table-cell">Maturidade</th>
                                        <th class="p-4 border-b border-white/5 text-right">Ação</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-white/5 text-sm">
                                    {#each users as user}
                                    <tr class="hover:bg-white/5 transition-colors group">
                                        <td class="p-4 font-mono text-xs text-gray-500">
                                            {user.id.substring(0, 8)}...
                                        </td>
                                        <td class="p-4 font-medium text-white">
                                            {#if user.nome}
                                                <div class="font-bold text-gray-200 group-hover:text-white transition-colors">{user.nome}</div>
                                            {:else}
                                                <div class="text-gray-600 italic text-xs">Aguardando...</div>
                                            {/if}
                                        </td>
                                        <td class="p-4 text-gray-400">
                                            {#if user.email}
                                                <div>{user.email}</div>
                                            {:else}
                                                <div class="text-gray-600 italic text-xs">Aguardando...</div>
                                            {/if}
                                        </td>
                                        <td class="p-4">
                                            <span class={`text-[10px] uppercase font-bold px-2 py-1 rounded-full border shadow-sm ${
                                                user.classificacao_lead?.startsWith('A') ? 'border-green-500/50 text-green-300 bg-green-900/30' :
                                                user.classificacao_lead?.startsWith('B') ? 'border-yellow-500/50 text-yellow-300 bg-yellow-900/20' :
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
        {:else if mode === 'videos'}
             <!-- Videos Mode -->
             <div class="flex-1 flex flex-col p-8 overflow-y-auto custom-scrollbar bg-gradient-to-br from-dolarize-dark to-dolarize-card" in:fade>
                <div class="flex justify-between items-start mb-8">
                    <div>
                        <h1 class="text-2xl font-bold tracking-tight text-white mb-2">Central de Vídeos</h1>
                        <p class="text-sm text-gray-400">Gerencie a biblioteca de vídeos recomendados pela IA.</p>
                    </div>

                    <!-- Add Video Button -->
                     <button
                        class="bg-dolarize-gold text-dolarize-dark font-bold text-sm px-4 py-2 rounded shadow-lg hover:shadow-xl hover:scale-105 transition-all flex items-center gap-2"
                        on:click={() => { cancelEditVideo(); isEditingVideo = true; }}
                    >
                         <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                        </svg>
                        Novo Vídeo
                    </button>
                </div>

                <!-- Editor Form -->
                {#if isEditingVideo}
                    <div class="bg-gray-800/50 border border-dolarize-blue-glow/30 rounded-lg p-6 mb-8 shadow-xl" in:fade>
                         <h3 class="text-lg font-bold text-white mb-4">{videoForm.id ? 'Editar Vídeo' : 'Novo Vídeo'}</h3>
                         <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                             <div>
                                 <label class="block text-xs font-bold uppercase text-gray-400 mb-1">Título</label>
                                 <input type="text" bind:value={videoForm.title} class="w-full bg-black/30 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:border-dolarize-gold focus:outline-none transition-colors" placeholder="Ex: Como proteger seu patrimônio">
                             </div>
                             <div>
                                 <label class="block text-xs font-bold uppercase text-gray-400 mb-1">URL (YouTube)</label>
                                 <input type="text" bind:value={videoForm.url} class="w-full bg-black/30 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:border-dolarize-gold focus:outline-none transition-colors" placeholder="https://youtu.be/...">
                             </div>
                         </div>
                         <div class="mb-4">
                             <label class="block text-xs font-bold uppercase text-gray-400 mb-1">Contexto de Gatilho (Para a IA)</label>
                             <textarea bind:value={videoForm.trigger_context} class="w-full bg-black/30 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:border-dolarize-gold focus:outline-none transition-colors h-24 resize-none" placeholder="Descreva QUANDO a IA deve recomendar este vídeo. Ex: Quando o lead perguntar sobre segurança da corretora..."></textarea>
                         </div>
                         <div class="flex justify-end gap-3">
                             <button on:click={cancelEditVideo} class="px-4 py-2 rounded border border-gray-600 text-gray-300 hover:bg-gray-700 text-sm font-semibold transition-colors">Cancelar</button>
                             <button on:click={saveVideo} disabled={isSavingVideo} class="px-4 py-2 rounded bg-dolarize-gold text-dolarize-dark font-bold text-sm hover:bg-white transition-colors flex items-center gap-2">
                                 {#if isSavingVideo}Saving...{:else}Salvar Vídeo{/if}
                             </button>
                         </div>
                    </div>
                {/if}

                <!-- Video List -->
                <div class="bg-dolarize-card rounded-lg border border-dolarize-blue-glow/20 flex flex-col flex-1 overflow-hidden shadow-xl">
                    <div class="p-4 border-b border-white/5 bg-white/5 flex justify-between items-center">
                        <h3 class="text-sm font-bold text-white uppercase tracking-wide">Vídeos Ativos</h3>
                        <span class="text-xs text-gray-400">{videos.length} vídeos</span>
                    </div>

                    {#if isLoadingVideos}
                        <div class="p-12 text-center text-gray-500 animate-pulse">Carregando vídeos...</div>
                    {:else if videos.length === 0}
                         <div class="p-12 text-center flex flex-col items-center justify-center text-gray-500">
                             <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-12 h-12 mb-4 opacity-30">
                              <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
                            </svg>
                             <p>Nenhum vídeo cadastrado.</p>
                         </div>
                    {:else}
                        <div class="overflow-auto custom-scrollbar flex-1">
                            <table class="w-full text-left border-collapse">
                                <thead class="bg-black/20 text-xs text-gray-400 uppercase font-semibold sticky top-0 z-10 backdrop-blur-sm">
                                    <tr>
                                        <th class="p-4 border-b border-white/5">Título</th>
                                        <th class="p-4 border-b border-white/5">Gatilho (Contexto)</th>
                                        <th class="p-4 border-b border-white/5 text-right">Ação</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-white/5 text-sm">
                                    {#each videos as video}
                                    <tr class="hover:bg-white/5 transition-colors group">
                                        <td class="p-4 font-medium text-white flex items-center gap-3">
                                            <div class="p-2 bg-red-500/10 rounded text-red-400">
                                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                                                  <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.91 11.672a.375.375 0 010 .656l-5.603 3.113a.375.375 0 01-.557-.328V8.887c0-.286.307-.466.557-.328l5.603 3.113z" />
                                                </svg>
                                            </div>
                                            <div>
                                                <div class="font-bold text-gray-200 group-hover:text-white transition-colors">{video.title}</div>
                                                <a href={video.url} target="_blank" class="text-[10px] text-blue-400 hover:text-blue-300 hover:underline font-mono truncate max-w-[200px] block">{video.url}</a>
                                            </div>
                                        </td>
                                        <td class="p-4 text-gray-400 text-xs leading-relaxed max-w-[300px]">{video.trigger_context}</td>
                                        <td class="p-4 text-right">
                                            <button
                                                class="text-blue-400 hover:text-blue-200 hover:bg-blue-900/30 p-2 rounded transition-colors mr-1"
                                                title="Editar"
                                                on:click={() => editVideo(video)}
                                            >
                                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                                                  <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                                                </svg>
                                            </button>
                                            <button
                                                class="text-red-400 hover:text-red-200 hover:bg-red-900/30 p-2 rounded transition-colors"
                                                title="Excluir"
                                                on:click={() => deleteVideo(video.id)}
                                            >
                                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                                                  <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                                                </svg>
                                            </button>
                                        </td>
                                    </tr>
                                    {/each}
                                </tbody>
                            </table>
                        </div>
                    {/if}
                </div>
             </div>
        {:else if mode === 'kb'}
            <!-- Knowledge Base Mode -->
             <div class="flex-1 flex flex-col p-8 overflow-y-auto custom-scrollbar bg-gradient-to-br from-dolarize-dark to-dolarize-card" in:fade>
                <div class="flex justify-between items-start mb-8">
                    <div>
                        <h1 class="text-2xl font-bold tracking-tight text-white mb-2">Base de Conhecimento Dinâmica</h1>
                        <p class="text-sm text-gray-400 mb-4">Gerencie os documentos que alimentam a inteligência do agente.</p>

                        <!-- KB Tabs -->
                        <div class="flex space-x-1 bg-black/20 p-1 rounded-lg inline-flex">
                            <button
                                class={`px-4 py-2 text-xs font-bold uppercase tracking-wider rounded-md transition-all ${activeKbTab === 'knowledge' ? 'bg-dolarize-blue-glow/20 text-white shadow ring-1 ring-dolarize-blue-glow/50' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
                                on:click={() => switchKbTab('knowledge')}
                            >
                                Base de Conhecimento
                            </button>
                            <button
                                class={`px-4 py-2 text-xs font-bold uppercase tracking-wider rounded-md transition-all ${activeKbTab === 'persona' ? 'bg-purple-900/40 text-purple-200 shadow ring-1 ring-purple-500/50' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
                                on:click={() => switchKbTab('persona')}
                            >
                                Centro de Personalidade
                            </button>
                        </div>
                    </div>

                    <!-- Upload Component -->
                    <div class="flex items-center gap-4">
                         <input
                            type="file"
                            id="fileUpload"
                            class="hidden"
                            accept=".pdf,.docx,.txt"
                            bind:this={fileInput}
                            on:change={handleFileUpload}
                            disabled={isUploading}
                        >
                        <label
                            for="fileUpload"
                            class={`cursor-pointer font-bold uppercase tracking-wide text-xs px-4 py-2.5 rounded hover:bg-white transition-colors flex items-center gap-2 ${isUploading ? 'opacity-50 cursor-not-allowed' : ''} ${activeKbTab === 'persona' ? 'bg-purple-500 text-white hover:text-purple-900' : 'bg-dolarize-gold text-dolarize-dark'}`}
                        >
                            {#if isUploading}
                                <svg class="animate-spin h-4 w-4 text-dolarize-dark" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                <span>Enviando...</span>
                            {:else}
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4">
                                  <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                                </svg>
                                <span>Upload de Arquivo</span>
                            {/if}
                        </label>
                    </div>
                </div>

                {#if uploadStatus === 'success'}
                    <div class="mb-6 p-3 bg-green-900/20 border border-green-500/30 text-green-400 text-sm rounded flex items-center gap-2" in:fade>
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" /></svg>
                        Arquivo enviado e indexado com sucesso. O agente já está atualizado.
                    </div>
                {/if}

                {#if uploadStatus === 'error'}
                     <div class="mb-6 p-3 bg-red-900/20 border border-red-500/30 text-red-400 text-sm rounded flex items-center gap-2" in:fade>
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" /></svg>
                        Erro ao enviar arquivo. Verifique se o formato é suportado e tente novamente.
                    </div>
                {/if}

                <!-- File List -->
                <div class="bg-dolarize-card rounded-lg border border-dolarize-blue-glow/20 flex flex-col flex-1 overflow-hidden shadow-xl">
                    <div class="p-4 border-b border-white/5 bg-white/5 flex justify-between items-center">
                        <h3 class="text-sm font-bold text-white uppercase tracking-wide">Arquivos de {activeKbTab === 'persona' ? 'Personalidade' : 'Conhecimento'}</h3>
                        <span class="text-xs text-gray-400">{knowledgeFiles.length} documentos indexados</span>
                    </div>

                    {#if isLoadingFiles}
                        <div class="p-12 text-center text-gray-500 animate-pulse">Carregando arquivos...</div>
                    {:else if knowledgeFiles.length === 0}
                         <div class="p-12 text-center flex flex-col items-center justify-center text-gray-500">
                             {#if activeKbTab === 'persona'}
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-12 h-12 mb-4 opacity-30 text-purple-400">
                                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.182 15.182a4.5 4.5 0 01-6.364 0M21 12a9 9 0 11-18 0 9 9 0 0118 0zM9.75 9.75c0 .414-.168.75-.375.75S9 10.164 9 9.75 9.168 9 9.375 9s.375.336.375.75zm-.375 0h.008v.015h-.008V9.75zm5.625 0c0 .414-.168.75-.375.75s-.375-.336-.375-.75.168-.75.375-.75.375.336.375.75zm-.375 0h.008v.015h-.008V9.75z" />
                                </svg>
                                 <p>Nenhum arquivo de personalidade definido.</p>
                                 <p class="text-xs mt-1">Faça upload de guias de estilo e tom de voz.</p>
                             {:else}
                                 <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-12 h-12 mb-4 opacity-30">
                                  <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                                </svg>
                                 <p>Nenhum arquivo na base de conhecimento.</p>
                                 <p class="text-xs mt-1">Faça upload de documentos para treinar o agente.</p>
                             {/if}
                         </div>
                    {:else}
                        <div class="overflow-auto custom-scrollbar flex-1">
                            <table class="w-full text-left border-collapse">
                                <thead class="bg-black/20 text-xs text-gray-400 uppercase font-semibold sticky top-0 z-10 backdrop-blur-sm">
                                    <tr>
                                        <th class="p-4 border-b border-white/5">Arquivo</th>
                                        <th class="p-4 border-b border-white/5">Tipo</th>
                                        <th class="p-4 border-b border-white/5">Tamanho</th>
                                        <th class="p-4 border-b border-white/5">Data Envio</th>
                                        <th class="p-4 border-b border-white/5 text-right">Ação</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-white/5 text-sm">
                                    {#each knowledgeFiles as file}
                                    <tr class="hover:bg-white/5 transition-colors group">
                                        <td class="p-4 font-medium text-white flex items-center gap-3">
                                            <div class="p-2 bg-dolarize-blue-glow/10 rounded text-blue-300">
                                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                                                  <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                                                </svg>
                                            </div>
                                            <div>
                                                <div class="font-bold text-gray-200 group-hover:text-white transition-colors">{file.display_name}</div>
                                                <div class="text-[10px] text-gray-500 font-mono">{file.name}</div>
                                            </div>
                                        </td>
                                        <td class="p-4 text-gray-400 text-xs uppercase tracking-wide">{file.mime_type?.split('/')[1] || 'DOC'}</td>
                                        <td class="p-4 text-gray-400 font-mono text-xs">{(file.size_bytes / 1024).toFixed(1)} KB</td>
                                        <td class="p-4 text-gray-400 font-mono text-xs">{new Date(file.created_at).toLocaleDateString()}</td>
                                        <td class="p-4 text-right">
                                            <button
                                                class="text-red-400 hover:text-red-200 hover:bg-red-900/30 p-2 rounded transition-colors"
                                                title="Excluir Arquivo"
                                                on:click={() => deleteFile(file.id)}
                                            >
                                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                                                  <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                                                </svg>
                                            </button>
                                        </td>
                                    </tr>
                                    {/each}
                                </tbody>
                            </table>
                        </div>
                    {/if}
                </div>
             </div>
        {:else if mode === 'config'}
            <!-- Config Mode -->
            <div class="flex-1 flex flex-col p-8 overflow-y-auto custom-scrollbar bg-gray-900" in:fade>
                <div class="mb-6">
                    <h1 class="text-2xl font-bold tracking-tight text-white mb-2 flex items-center gap-2">
                        <span class="text-red-500">⚙️</span> Configurações Nucleares
                    </h1>
                    <p class="text-sm text-gray-400">Edite diretamente o prompt do sistema. As alterações têm efeito imediato na próxima interação.</p>
                </div>

                <!-- Warning Banner -->
                <div class="bg-orange-900/20 border-l-4 border-orange-500 p-4 mb-6 rounded-r">
                    <div class="flex">
                        <div class="flex-shrink-0">
                            <svg class="h-5 w-5 text-orange-400" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                            </svg>
                        </div>
                        <div class="ml-3">
                            <p class="text-sm text-orange-200">
                                <strong class="font-bold text-orange-100">CUIDADO EXTREMO:</strong>
                                Editar este texto pode alterar a personalidade, segurança e limites do agente. Modifique apenas se souber exatamente o que está fazendo.
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Status Messages -->
                {#if promptStatus === 'saved'}
                    <div class="mb-4 p-3 bg-green-900/30 border border-green-500/50 text-green-300 text-sm rounded flex items-center gap-2 animate-pulse">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" /></svg>
                        Prompt atualizado com sucesso. O cérebro do agente foi reiniciado.
                    </div>
                {:else if promptStatus === 'reset'}
                     <div class="mb-4 p-3 bg-blue-900/30 border border-blue-500/50 text-blue-300 text-sm rounded flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" /></svg>
                        Padrão de fábrica restaurado com sucesso.
                    </div>
                {:else if promptStatus === 'error'}
                     <div class="mb-4 p-3 bg-red-900/30 border border-red-500/50 text-red-300 text-sm rounded flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" /></svg>
                        Erro ao salvar alterações. Tente novamente.
                    </div>
                {/if}

                <!-- Editor -->
                <div class="flex-1 flex flex-col relative bg-black/40 rounded-lg border border-gray-700 shadow-inner">
                    {#if isLoadingPrompt}
                        <div class="absolute inset-0 flex items-center justify-center bg-black/50 z-20 backdrop-blur-sm rounded-lg">
                            <div class="text-white animate-pulse font-mono">Carregando DNA...</div>
                        </div>
                    {/if}

                    <div class="bg-gray-800 px-4 py-2 rounded-t-lg border-b border-gray-700 flex justify-between items-center">
                        <span class="text-xs font-mono text-gray-400">system_prompt.txt</span>
                        <span class="text-[10px] text-gray-500 uppercase">UTF-8</span>
                    </div>

                    <textarea
                        bind:value={corePromptText}
                        class="flex-1 bg-transparent text-gray-300 font-mono text-sm p-4 resize-none focus:outline-none focus:ring-0 custom-scrollbar leading-relaxed"
                        spellcheck="false"
                        disabled={isSavingPrompt}
                    ></textarea>
                </div>

                <!-- Controls -->
                <div class="mt-6 flex justify-between items-center pt-6 border-t border-white/10">
                    <button
                        on:click={resetCorePrompt}
                        disabled={isSavingPrompt}
                        class="text-red-400 hover:text-red-300 text-xs font-bold uppercase tracking-wider px-4 py-2 rounded border border-red-500/20 hover:bg-red-900/20 transition-all flex items-center gap-2"
                    >
                         <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
                        </svg>
                        Restaurar Padrão de Fábrica
                    </button>

                    <button
                        on:click={saveCorePrompt}
                        disabled={isSavingPrompt}
                        class={`bg-dolarize-gold text-dolarize-dark font-bold text-sm px-6 py-2.5 rounded shadow-lg hover:shadow-xl hover:scale-105 transition-all flex items-center gap-2 ${isSavingPrompt ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        {#if isSavingPrompt}
                             <svg class="animate-spin h-4 w-4 text-dolarize-dark" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Salvando...
                        {:else}
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4">
                              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Salvar Alterações
                        {/if}
                    </button>
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
