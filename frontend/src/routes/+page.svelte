<script>
    import { goto } from '$app/navigation';
</script>

<svelte:head>
    <title>Dólarize - Focus Board</title>
</svelte:head>

<div class="min-h-screen bg-dolarize-dark text-white flex flex-col items-center justify-center p-8">
    <h1 class="text-4xl md:text-5xl font-extrabold text-white mb-6 text-center">
        Bem-vindo ao <span class="text-yellow-500">Focus Board</span>
    </h1>

    <p class="text-lg text-gray-300 max-w-2xl text-center mb-12">
        Acesse seu dashboard unificado para gerenciar ativos on-chain, arquétipos e hábitos diários.
    </p>

    <div class="flex gap-4">
        <button on:click={() => goto('/quiz')} class="bg-dolarize-gold text-dolarize-dark font-bold px-8 py-3 rounded-lg shadow-lg hover:bg-white transition-colors">
            Fazer o Quiz
        </button>
        <button on:click={() => goto('/focus-board')} class="border border-dolarize-gold text-dolarize-gold font-bold px-8 py-3 rounded-lg hover:bg-dolarize-gold/10 transition-colors">
            Acessar Dashboard
        </button>
    </div>
</div>
