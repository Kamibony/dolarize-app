<script>
    import { onMount } from 'svelte';
    import ChatWidget from '$lib/components/ChatWidget.svelte';

    let currentTier = 'C';
    let userId = "test-user-123"; // Default fallback

    onMount(() => {
        // Generate or retrieve unique User ID
        const storedUserId = localStorage.getItem('dolarize_user_id');
        if (storedUserId) {
            userId = storedUserId;
        } else {
            // Simple UUID generator fallback if crypto.randomUUID is not available
            userId = crypto.randomUUID ? crypto.randomUUID() : 'user-' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('dolarize_user_id', userId);
        }
    });

    // Dynamic background based on tier
    $: backgroundClasses = (() => {
        switch (currentTier) {
            case 'A': return 'bg-gradient-to-br from-dolarize-dark via-[#0F172A] to-dolarize-gold/10'; // Qualified
            case 'B': return 'bg-gradient-to-br from-dolarize-dark via-[#0F172A] to-dolarize-blue-glow/20'; // Education
            default: return 'bg-dolarize-dark'; // Cold
        }
    })();
</script>

<div class={`min-h-screen text-white font-sans transition-all duration-1000 ease-in-out ${backgroundClasses}`}>
    <div class="max-w-7xl mx-auto px-6 py-12 lg:py-24">

        <!-- Hero Section -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <!-- Left Column: Copy -->
            <div class="flex flex-col space-y-8 text-center lg:text-left">
                 <div class="inline-block px-4 py-1.5 rounded-full bg-dolarize-gold/10 border border-dolarize-gold/20 text-dolarize-gold text-sm font-semibold tracking-wider uppercase self-center lg:self-start mb-4">
                    Imersão Dólarize 2.0
                </div>
                <h1 class="text-4xl md:text-5xl lg:text-6xl font-bold text-white leading-tight tracking-tight">
                    Proteja seu patrimônio da <span class="text-transparent bg-clip-text bg-gradient-to-r from-dolarize-gold to-yellow-200">inflação.</span>
                </h1>
                <p class="text-lg md:text-xl text-gray-300 leading-relaxed max-w-2xl mx-auto lg:mx-0">
                    Converse com nosso Agente de Inteligência Artificial para descobrir sua estratégia ideal de autocustódia e segurança financeira.
                </p>

                 <!-- Mobile Call to Action Arrow (Visual cue) -->
                 <div class="lg:hidden flex justify-center text-dolarize-gold animate-bounce pt-4">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                    </svg>
                </div>
            </div>

            <!-- Right Column: Chat Widget -->
            <div class="w-full max-w-lg mx-auto lg:max-w-none lg:mx-0 shadow-2xl rounded-2xl">
                 <ChatWidget bind:currentTier userId={userId} />
            </div>
        </div>

        <!-- Value Proposition Section -->
        <div class="mt-24 lg:mt-32 grid grid-cols-1 md:grid-cols-3 gap-8">
            <!-- Benefit 1: Segurança -->
            <div class="bg-dolarize-card/50 backdrop-blur-sm p-8 rounded-2xl border border-white/5 hover:border-dolarize-gold/30 transition-all duration-300 hover:-translate-y-1">
                <div class="w-12 h-12 bg-dolarize-gold/10 rounded-xl flex items-center justify-center mb-6 text-dolarize-gold">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z" />
                    </svg>
                </div>
                <h3 class="text-xl font-bold text-white mb-3">Segurança</h3>
                <p class="text-gray-400 leading-relaxed">
                    Proteja seu capital contra riscos sistêmicos e inflação com estratégias validadas.
                </p>
            </div>

            <!-- Benefit 2: Autocustódia -->
            <div class="bg-dolarize-card/50 backdrop-blur-sm p-8 rounded-2xl border border-white/5 hover:border-dolarize-gold/30 transition-all duration-300 hover:-translate-y-1">
                <div class="w-12 h-12 bg-dolarize-blue-glow/10 rounded-xl flex items-center justify-center mb-6 text-dolarize-blue-glow">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
                    </svg>
                </div>
                <h3 class="text-xl font-bold text-white mb-3">Autocustódia</h3>
                <p class="text-gray-400 leading-relaxed">
                    Tenha controle total sobre seus ativos. Sem intermediários, sem bloqueios.
                </p>
            </div>

            <!-- Benefit 3: Liberdade -->
            <div class="bg-dolarize-card/50 backdrop-blur-sm p-8 rounded-2xl border border-white/5 hover:border-dolarize-gold/30 transition-all duration-300 hover:-translate-y-1">
                <div class="w-12 h-12 bg-green-500/10 rounded-xl flex items-center justify-center mb-6 text-green-400">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M6.115 5.19l.319 1.913A6 6 0 008.11 10.36L9.75 12l-.387.775c-.217.433-.132.956.21 1.298l1.348 1.348c.21.21.329.497.329.795v1.089c0 .426.24.815.622 1.006l.153.076c.433.217.956.132 1.298-.21l.723-.723a8.7 8.7 0 002.288-4.042 3.104 3.104 0 00-.21-2.87l-.837-1.675a.6.6 0 01.18-.738l.231-.173c.43-.323.902-.51 1.386-.543 1.102-.072 2.39.223 3.535 1.256 1.485 1.335 1.62 3.68.299 5.34l-.531.665c-.734.92-1.604 2.334-2.508 5.318a6 6 0 00-.403 2.13.04.04 0 00.04.04h4.743a.04.04 0 00.04-.04c.037-.96.09-2.013.3-2.992.547-2.561 2.29-4.938 4.29-6.31M15 20.25h.008v.008H15v-.008zM6.75 15.75h.008v.008H6.75v-.008z" />
                    </svg>
                </div>
                <h3 class="text-xl font-bold text-white mb-3">Liberdade</h3>
                <p class="text-gray-400 leading-relaxed">
                    Opere globalmente e acesse oportunidades que antes eram exclusivas.
                </p>
            </div>
        </div>

         <footer class="mt-24 text-center text-gray-500 text-sm">
            &copy; 2024 Dólarize 2.0. Todos os direitos reservados.
        </footer>
    </div>
</div>
