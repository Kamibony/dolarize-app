<script>
    import { onMount } from 'svelte';
    import { auth } from '$lib/firebase';
    import { signOut } from 'firebase/auth';
    import { goto } from '$app/navigation';

    let userEmail = '';

    onMount(() => {
        if (auth.currentUser) {
            userEmail = auth.currentUser.email || '';
        }
    });

    async function handleLogout() {
        await signOut(auth);
        goto('/admin/login');
    }
</script>

<svelte:head>
    <title>Admin Panel - Dólarize Focus Board</title>
</svelte:head>

<div class="min-h-screen bg-dolarize-dark text-white p-8">
    <div class="flex justify-between items-center mb-8">
        <h1 class="text-3xl font-bold">Admin Panel</h1>
        <div class="flex items-center gap-4">
            <span class="text-gray-400">{userEmail}</span>
            <button on:click={handleLogout} class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded">
                Logout
            </button>
        </div>
    </div>

    <div class="bg-dolarize-card p-6 rounded-lg border border-gray-700">
        <h2 class="text-xl font-semibold mb-4">Focus Board Administration</h2>
        <p class="text-gray-400">Welcome to the Focus Board Admin Panel. Configure MVP settings here.</p>
    </div>
</div>
