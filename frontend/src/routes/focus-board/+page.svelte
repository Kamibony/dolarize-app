<script lang="ts">
    import { onMount } from 'svelte';
    import { auth, db } from '$lib/firebase';
    import { doc, getDoc, updateDoc, setDoc, arrayUnion, arrayRemove, collection, getDocs, addDoc } from 'firebase/firestore';
    import type { User, DailyLog, Wallet } from '$lib/types/database';

    let user: User | null = null;
    let loading = true;

    // Hardcoded practical skills for MVP
    const ALL_SKILLS = [
        "Create Metamask/Phantom Wallet",
        "Fund Wallet with SOL",
        "Make First Swap on Jupiter",
        "Provide Liquidity on Raydium"
    ];

    // Habits for MVP
    const DAILY_HABITS = [
        "Check crypto prices",
        "Read 1 article on DeFi",
        "Review open positions"
    ];

    let todayDateStr = new Date().toISOString().split('T')[0];
    let dailyLog: DailyLog | null = null;
    let loadingDaily = true;

    // Wallet Integration
    let wallets: Wallet[] = [];
    let newWalletAddress = '';
    let fetchingBalance = false;
    let walletBalances: Record<string, any> = {};

    onMount(async () => {
        auth.onAuthStateChanged(async (firebaseUser) => {
            if (firebaseUser) {
                await loadUserData(firebaseUser.uid);
                await loadDailyLog(firebaseUser.uid);
                await loadWallets(firebaseUser.uid);
            } else {
                user = null;
                loading = false;
            }
        });
    });

    async function loadUserData(uid: string) {
        const userRef = doc(db, 'users', uid);
        const userSnap = await getDoc(userRef);
        if (userSnap.exists()) {
            user = { uid, ...userSnap.data() } as User;
            if (!user.practicalSkills) user.practicalSkills = [];
            if (!user.streakCount) user.streakCount = 0;
        }
        loading = false;
    }

    async function loadDailyLog(uid: string) {
        const logRef = doc(db, `users/${uid}/daily_logs`, todayDateStr);
        const logSnap = await getDoc(logRef);
        if (logSnap.exists()) {
            dailyLog = { id: todayDateStr, ...logSnap.data() } as DailyLog;
            if (!dailyLog.habitsCompleted) dailyLog.habitsCompleted = [];
        } else {
            dailyLog = {
                id: todayDateStr,
                date: new Date(),
                habitsCompleted: [],
                createdAt: new Date()
            };
        }
        loadingDaily = false;
    }

    async function loadWallets(uid: string) {
        const walletsRef = collection(db, `users/${uid}/wallets`);
        const snapshot = await getDocs(walletsRef);
        wallets = snapshot.docs.map(doc => ({ walletId: doc.id, ...doc.data() } as Wallet));

        // Fetch balances for loaded wallets
        for (const w of wallets) {
            await fetchBalance(w.address);
        }
    }

    async function toggleSkill(skill: string, isChecked: boolean) {
        if (!user) return;
        const userRef = doc(db, 'users', user.uid);

        if (isChecked) {
            await updateDoc(userRef, {
                practicalSkills: arrayUnion(skill)
            });
            user.practicalSkills = [...user.practicalSkills, skill];
        } else {
            await updateDoc(userRef, {
                practicalSkills: arrayRemove(skill)
            });
            user.practicalSkills = user.practicalSkills.filter(s => s !== skill);
        }
    }

    async function toggleHabit(habit: string, isChecked: boolean) {
        if (!user || !dailyLog) return;

        const logRef = doc(db, `users/${user.uid}/daily_logs`, todayDateStr);
        const userRef = doc(db, 'users', user.uid);

        let newHabits = [...dailyLog.habitsCompleted];

        if (isChecked) {
            newHabits.push(habit);
        } else {
            newHabits = newHabits.filter(h => h !== habit);
        }

        // Save log
        await setDoc(logRef, {
            ...dailyLog,
            habitsCompleted: newHabits
        }, { merge: true });

        // Update local state
        dailyLog.habitsCompleted = newHabits;

        // Simple MVP streak logic: if all habits done today, increment streak (only once per day ideally, but for MVP we just +1 if full)
        // A better approach would be to check yesterday's log, but keeping MVP scope:
        if (newHabits.length === DAILY_HABITS.length && isChecked) {
             const newStreak = user.streakCount + 1;
             await updateDoc(userRef, { streakCount: newStreak });
             user.streakCount = newStreak;
        }
    }

    async function addWallet() {
        if (!user || !newWalletAddress.trim()) return;

        const address = newWalletAddress.trim();
        const walletsRef = collection(db, `users/${user.uid}/wallets`);

        const newWallet = {
            address,
            network: 'solana',
            isPrimary: wallets.length === 0,
            addedAt: new Date()
        };

        const docRef = await addDoc(walletsRef, newWallet);
        const addedWallet = { walletId: docRef.id, ...newWallet } as Wallet;

        wallets = [...wallets, addedWallet];
        newWalletAddress = '';

        await fetchBalance(addedWallet.address);
    }

    async function fetchBalance(address: string) {
        fetchingBalance = true;
        try {
            const res = await fetch(`/api/solana-balance?address=${encodeURIComponent(address)}`);
            if (res.ok) {
                const data = await res.json();
                walletBalances[address] = data;
            } else {
                console.error("Failed to fetch balance");
            }
        } catch (err) {
            console.error(err);
        } finally {
            fetchingBalance = false;
        }
    }

    function refreshAllBalances() {
        for (const w of wallets) {
            fetchBalance(w.address);
        }
    }

</script>

<svelte:head>
    <title>Focus Board - Dólarize</title>
</svelte:head>

<div class="min-h-screen bg-gray-900 text-white p-8">
    <div class="max-w-6xl mx-auto">
        <h1 class="text-3xl font-bold mb-8">Dashboard: Focus Board</h1>

        {#if loading}
            <p>Loading your data...</p>
        {:else if !user}
            <p>Please log in to view your dashboard.</p>
        {:else}
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <!-- Profile & Archetype -->
                <div class="bg-gray-800 p-6 rounded-lg border border-gray-700 col-span-1">
                    <h2 class="text-xl font-semibold mb-4 text-blue-400">Profile</h2>
                    <p class="text-gray-300 mb-2"><span class="font-bold">Email:</span> {user.email}</p>
                    <div class="mt-4 p-4 bg-gray-700 rounded-lg text-center">
                        <p class="text-sm text-gray-400 uppercase tracking-wide">Current Archetype</p>
                        <p class="text-4xl font-bold text-yellow-400 mt-2">{user.currentArchetype || '?'}</p>
                    </div>
                    <div class="mt-4 p-4 bg-gray-700 rounded-lg text-center flex items-center justify-center gap-2">
                        <span class="text-2xl">🔥</span>
                        <div>
                            <p class="text-sm text-gray-400 uppercase tracking-wide">Current Streak</p>
                            <p class="text-2xl font-bold">{user.streakCount} days</p>
                        </div>
                    </div>
                </div>

                <!-- Daily Tracker -->
                <div class="bg-gray-800 p-6 rounded-lg border border-gray-700 col-span-1">
                    <h2 class="text-xl font-semibold mb-4 text-green-400">Daily Habits ({todayDateStr})</h2>
                    {#if loadingDaily}
                        <p class="text-sm text-gray-500">Loading today's habits...</p>
                    {:else if dailyLog}
                        <div class="space-y-3">
                            {#each DAILY_HABITS as habit}
                                <label class="flex items-center space-x-3 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        class="form-checkbox h-5 w-5 text-green-500 rounded bg-gray-700 border-gray-600 focus:ring-green-500 focus:ring-offset-gray-800"
                                        checked={dailyLog.habitsCompleted.includes(habit)}
                                        on:change={(e) => toggleHabit(habit, e.currentTarget.checked)}
                                    />
                                    <span class="text-gray-200">{habit}</span>
                                </label>
                            {/each}
                        </div>
                    {/if}
                </div>

                <!-- Practical Skills -->
                <div class="bg-gray-800 p-6 rounded-lg border border-gray-700 col-span-1">
                    <h2 class="text-xl font-semibold mb-4 text-purple-400">Practical Skills</h2>
                    <div class="space-y-3">
                        {#each ALL_SKILLS as skill}
                            <label class="flex items-center space-x-3 cursor-pointer">
                                <input
                                    type="checkbox"
                                    class="form-checkbox h-5 w-5 text-purple-500 rounded bg-gray-700 border-gray-600 focus:ring-purple-500 focus:ring-offset-gray-800"
                                    checked={user.practicalSkills?.includes(skill)}
                                    on:change={(e) => toggleSkill(skill, e.currentTarget.checked)}
                                />
                                <span class="text-gray-200">{skill}</span>
                            </label>
                        {/each}
                    </div>
                </div>

                <!-- Web3/Solana Wallet Integration -->
                <div class="bg-gray-800 p-6 rounded-lg border border-gray-700 col-span-1 md:col-span-3 mt-4">
                    <div class="flex justify-between items-center mb-4">
                        <h2 class="text-xl font-semibold text-teal-400">Web3 Portfolio (Solana)</h2>
                        <button on:click={refreshAllBalances} class="text-sm bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded" disabled={fetchingBalance}>
                            {fetchingBalance ? 'Refreshing...' : 'Refresh Balances'}
                        </button>
                    </div>

                    <div class="flex gap-4 mb-6">
                        <input
                            type="text"
                            bind:value={newWalletAddress}
                            placeholder="Enter Solana Address (Read-only)"
                            class="flex-1 bg-gray-700 border border-gray-600 rounded px-4 py-2 text-white focus:outline-none focus:border-teal-500"
                        />
                        <button on:click={addWallet} class="bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded font-medium">
                            Add Wallet
                        </button>
                    </div>

                    {#if wallets.length === 0}
                        <p class="text-gray-400 text-sm">No wallets added yet. Add your Solana address to track your balance.</p>
                    {:else}
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {#each wallets as wallet}
                                <div class="bg-gray-700 p-4 rounded-lg flex flex-col justify-between">
                                    <div class="flex justify-between items-start mb-2">
                                        <span class="text-xs text-gray-400 font-mono break-all">{wallet.address}</span>
                                        {#if wallet.isPrimary}
                                            <span class="text-xs bg-teal-900 text-teal-300 px-2 py-1 rounded">Primary</span>
                                        {/if}
                                    </div>

                                    {#if walletBalances[wallet.address]}
                                        <div class="mt-2">
                                            <p class="text-2xl font-bold">${walletBalances[wallet.address].balanceUsd.toFixed(2)} USD</p>
                                            <p class="text-sm text-gray-400">{walletBalances[wallet.address].balanceSol.toFixed(4)} SOL (@ ${walletBalances[wallet.address].priceUsd.toFixed(2)}/SOL)</p>
                                        </div>
                                    {:else}
                                        <div class="mt-2 text-gray-400 text-sm">Loading balance...</div>
                                    {/if}
                                </div>
                            {/each}
                        </div>
                    {/if}
                </div>

            </div>
        {/if}
    </div>
</div>
