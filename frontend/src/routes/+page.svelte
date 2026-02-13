<script>
    import { onMount } from 'svelte';
    import { fade, fly } from 'svelte/transition';

    let messages = [
        { sender: 'agent', text: 'Olá. Sou o André Digital. Estou aqui para ajudar você a organizar sua jornada financeira com estrutura e segurança.' },
    ];
    let newMessage = '';
    let isLoading = false;
    // Hardcoded user_id for now as per instructions
    const USER_ID = "test-user-123";

    async function sendMessage() {
        if (newMessage.trim() === '' || isLoading) return;

        const userMessage = newMessage;
        messages = [...messages, { sender: 'user', text: userMessage }];
        newMessage = '';
        isLoading = true;

        try {
            const response = await fetch('http://localhost:8080/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: userMessage,
                    user_id: USER_ID
                })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            messages = [...messages, { sender: 'agent', text: data.response }];
        } catch (error) {
            console.error('Error sending message:', error);
            messages = [...messages, { sender: 'agent', text: 'Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente mais tarde.' }];
        } finally {
            isLoading = false;
        }
    }

    function handleKeydown(event) {
        if (event.key === 'Enter') {
            sendMessage();
        }
    }

    let chatContainer;
    $: if (messages && chatContainer) {
        setTimeout(() => {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }, 0);
    }
</script>

<div class="flex flex-col h-screen bg-dolarize-dark text-white font-sans overflow-hidden">
    <!-- Header -->
    <header class="flex items-center justify-between px-6 py-4 border-b border-dolarize-blue-glow/30 bg-dolarize-dark/95 backdrop-blur-sm sticky top-0 z-10">
        <div class="flex flex-col">
            <h1 class="text-xl font-bold tracking-tight text-white">André Digital</h1>
            <span class="text-xs text-dolarize-gold uppercase tracking-widest font-semibold">Extensão Dólarize 2.0</span>
        </div>
        <div class="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.6)]"></div>
    </header>

    <!-- Chat Area -->
    <main class="flex-1 overflow-y-auto p-4 md:p-6 space-y-6" bind:this={chatContainer}>
        {#each messages as message}
            <div
                in:fly="{{ y: 20, duration: 300 }}"
                class={`flex w-full ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
                <div class={`
                    max-w-[85%] md:max-w-[70%] p-4 rounded-lg shadow-lg relative
                    ${message.sender === 'user'
                        ? 'bg-transparent text-gray-200 text-right border border-gray-700/50'
                        : 'bg-dolarize-card text-gray-100 border-l-2 border-dolarize-gold shadow-[0_4px_20px_rgba(0,0,0,0.2)]'
                    }
                `}>
                    <p class="leading-relaxed text-sm md:text-base">{message.text}</p>
                </div>
            </div>
        {/each}
        {#if isLoading}
             <div class="flex w-full justify-start" in:fade>
                <div class="bg-dolarize-card text-gray-100 border-l-2 border-dolarize-gold shadow-lg p-4 rounded-lg">
                    <div class="flex space-x-2">
                        <div class="w-2 h-2 bg-dolarize-gold rounded-full animate-bounce"></div>
                        <div class="w-2 h-2 bg-dolarize-gold rounded-full animate-bounce delay-100"></div>
                        <div class="w-2 h-2 bg-dolarize-gold rounded-full animate-bounce delay-200"></div>
                    </div>
                </div>
            </div>
        {/if}
    </main>

    <!-- Input Area -->
    <footer class="p-4 md:p-6 bg-dolarize-dark border-t border-dolarize-blue-glow/20">
        <div class="relative max-w-4xl mx-auto">
            <input
                type="text"
                bind:value={newMessage}
                on:keydown={handleKeydown}
                placeholder="Digite sua mensagem aqui..."
                disabled={isLoading}
                class="w-full bg-dolarize-card text-white placeholder-gray-500 px-6 py-4 pr-24 rounded-lg focus:outline-none focus:ring-1 focus:ring-dolarize-gold/50 focus:border-dolarize-blue-glow/50 transition-all shadow-inner border border-gray-800 disabled:opacity-50"
            />
            <button
                on:click={sendMessage}
                class="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 text-sm font-semibold text-dolarize-gold hover:text-white transition-colors uppercase tracking-wider disabled:opacity-50"
                disabled={!newMessage.trim() || isLoading}
            >
                Enviar
            </button>
        </div>
    </footer>
</div>
