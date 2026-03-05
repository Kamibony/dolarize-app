<script>
    import { auth } from '$lib/firebase';
    import { signInWithEmailAndPassword } from 'firebase/auth';
    import { goto } from '$app/navigation';

    let email = '';
    let password = '';
    let error = null;
    let loading = false;

    async function handleLogin() {
        error = null;
        loading = true;
        try {
            await signInWithEmailAndPassword(auth, email, password);
            goto('/admin');
        } catch (err) {
            console.error('Login error:', err);
            error = 'Falha no login. Verifique suas credenciais.';
        } finally {
            loading = false;
        }
    }
</script>

<svelte:head>
    <title>Login - Dólarize Admin</title>
</svelte:head>

<div class="min-h-screen bg-dolarize-dark flex flex-col justify-center py-12 sm:px-6 lg:px-8">
    <div class="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 class="mt-6 text-center text-3xl font-extrabold text-white">
            Admin Console
        </h2>
        <p class="mt-2 text-center text-sm text-gray-400">
            Acesso restrito Dólarize
        </p>
    </div>

    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div class="bg-dolarize-card py-8 px-4 shadow-xl border border-dolarize-blue-glow/20 sm:rounded-lg sm:px-10">
            <form class="space-y-6" on:submit|preventDefault={handleLogin}>
                <div>
                    <label for="email" class="block text-sm font-medium text-gray-300">
                        Email
                    </label>
                    <div class="mt-1">
                        <input id="email" name="email" type="email" autocomplete="email" required bind:value={email}
                            class="appearance-none block w-full px-3 py-2 border border-gray-600 rounded-md shadow-sm placeholder-gray-400 bg-black/30 text-white focus:outline-none focus:ring-dolarize-gold focus:border-dolarize-gold sm:text-sm">
                    </div>
                </div>

                <div>
                    <label for="password" class="block text-sm font-medium text-gray-300">
                        Senha
                    </label>
                    <div class="mt-1">
                        <input id="password" name="password" type="password" autocomplete="current-password" required bind:value={password}
                            class="appearance-none block w-full px-3 py-2 border border-gray-600 rounded-md shadow-sm placeholder-gray-400 bg-black/30 text-white focus:outline-none focus:ring-dolarize-gold focus:border-dolarize-gold sm:text-sm">
                    </div>
                </div>

                {#if error}
                    <div class="text-red-400 text-sm bg-red-900/20 border border-red-500/30 p-3 rounded">
                        {error}
                    </div>
                {/if}

                <div>
                    <button type="submit" disabled={loading}
                        class={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-dolarize-dark bg-dolarize-gold hover:bg-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-dolarize-gold focus:ring-offset-dolarize-dark transition-colors ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}>
                        {#if loading}
                            Entrando...
                        {:else}
                            Entrar
                        {/if}
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
