<script>
    import { onMount } from 'svelte';
    import { fade, fly } from 'svelte/transition';

    export let currentTier = 'C'; // Default to Cold/Welcome
    export let userId = "test-user-123";
    export let agentName = "André Digital"; // Configurable
    export let companyName = "Dolarize"; // Configurable

    const API_BASE_URL = import.meta.env.PUBLIC_API_URL || 'https://dolarize-api-493794054971.us-central1.run.app';

    let messages = [
        { sender: 'agent', text: `Olá. Sou o ${agentName}. Estou aqui para ajudar você.` },
    ];
    let newMessage = '';
    let isLoading = false;
    let chatContainer;
    let hasInteracted = false;

    // Helper to safely track Meta Pixel events
    function trackPixelEvent(eventName, params = {}) {
        if (typeof window !== 'undefined' && window.fbq) {
            console.log(`[Pixel] Tracking event: ${eventName}`, params);
            window.fbq('track', eventName, params);
        } else {
            console.log(`[Pixel] Placeholder tracked: ${eventName}`, params);
        }
    }

    function formatMessage(text) {
        if (!text) return '';

        // 1. Escape HTML special characters to prevent XSS
        const safeText = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");

        // 2. Replace URLs with anchor tags
        const urlRegex = /(\b(https?):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;

        return safeText.replace(urlRegex, (url) => {
            return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="text-blue-400 underline hover:text-blue-300">${url}</a>`;
        });
    }

    async function sendMessage() {
        if (newMessage.trim() === '' || isLoading) return;

        // Marketing Analytics: Track first interaction
        if (!hasInteracted) {
            trackPixelEvent('Lead'); // Or 'InitiateCheckout' as per strategy
            hasInteracted = true;
        }

        const userMessage = newMessage;

        // Marketing Analytics: Detect Email for 'CompleteRegistration'
        const emailRegex = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/;
        if (emailRegex.test(userMessage)) {
            trackPixelEvent('CompleteRegistration', { value: 0.00, currency: 'BRL' });
        }

        messages = [...messages, { sender: 'user', text: userMessage }];
        newMessage = '';
        isLoading = true;

        try {
            const response = await fetch(`${API_BASE_URL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: userMessage,
                    user_id: userId
                })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();

            // Only add agent message if response is not empty (handles bot_paused case)
            if (data.response && data.response.trim() !== '') {
                messages = [...messages, { sender: 'agent', text: data.response }];
            }

            // Update tier if provided
            if (data.user_tier) {
                currentTier = data.user_tier;
            }
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

    $: if (messages && chatContainer) {
        setTimeout(() => {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }, 0);
    }
</script>

<div class="flex flex-col h-[500px] md:h-[600px] w-full bg-dolarize-card rounded-2xl shadow-2xl overflow-hidden border border-dolarize-gold/20 relative">
    <!-- Header -->
    <header class="flex items-center justify-between px-6 py-4 border-b border-dolarize-blue-glow/30 bg-dolarize-dark/95 backdrop-blur-sm sticky top-0 z-10">
        <div class="flex flex-col">
            <h2 class="text-lg font-bold tracking-tight text-white">{agentName}</h2>
            <span class="text-[10px] text-dolarize-gold uppercase tracking-widest font-semibold">Extensão {companyName}</span>
        </div>
        <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.6)] animate-pulse"></div>
            <span class="text-xs text-green-400 font-medium">Online</span>
        </div>
    </header>

    <!-- Chat Area -->
    <div class="flex-1 overflow-y-auto p-4 space-y-4 bg-dolarize-dark/50" bind:this={chatContainer}>
        {#each messages as message}
            <div
                in:fly="{{ y: 20, duration: 300 }}"
                class={`flex w-full ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
                <div class={`
                    max-w-[85%] p-3 md:p-4 rounded-2xl shadow-sm text-sm md:text-base leading-relaxed
                    ${message.sender === 'user'
                        ? 'bg-dolarize-blue-glow/20 text-white rounded-br-none border border-dolarize-blue-glow/30'
                        : 'bg-dolarize-card text-gray-100 rounded-bl-none border-l-2 border-dolarize-gold shadow-md'
                    }
                `}>
                    {@html formatMessage(message.text)}
                </div>
            </div>
        {/each}
        {#if isLoading}
            <div class="flex w-full justify-start" in:fade>
                <div class="bg-dolarize-card text-gray-100 border-l-2 border-dolarize-gold shadow-lg p-4 rounded-2xl rounded-bl-none">
                    <div class="flex space-x-2">
                        <div class="w-1.5 h-1.5 bg-dolarize-gold rounded-full animate-bounce"></div>
                        <div class="w-1.5 h-1.5 bg-dolarize-gold rounded-full animate-bounce delay-100"></div>
                        <div class="w-1.5 h-1.5 bg-dolarize-gold rounded-full animate-bounce delay-200"></div>
                    </div>
                </div>
            </div>
        {/if}
    </div>

    <!-- Input Area -->
    <footer class="p-4 bg-dolarize-dark border-t border-dolarize-blue-glow/20">
        <div class="relative w-full">
            <input
                type="text"
                bind:value={newMessage}
                on:keydown={handleKeydown}
                placeholder="Digite sua mensagem..."
                disabled={isLoading}
                class="w-full bg-dolarize-card text-white placeholder-gray-500 px-4 py-3 pr-12 rounded-xl focus:outline-none focus:ring-1 focus:ring-dolarize-gold/50 focus:border-dolarize-blue-glow/50 transition-all shadow-inner border border-gray-800 disabled:opacity-50 text-sm md:text-base"
            />
            <button
                on:click={sendMessage}
                class="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-dolarize-gold hover:text-white transition-colors disabled:opacity-50 rounded-lg hover:bg-dolarize-blue-glow/10"
                disabled={!newMessage.trim() || isLoading}
                aria-label="Enviar mensagem"
            >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5">
                  <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
                </svg>
            </button>
        </div>
    </footer>
</div>
