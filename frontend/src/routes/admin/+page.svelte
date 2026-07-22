<script lang="ts">
    import { onMount } from 'svelte';
    import { auth, db } from '$lib/firebase';
    import { signOut } from 'firebase/auth';
    import { goto } from '$app/navigation';
    import { collection, query, where, getDocs, orderBy, limit } from 'firebase/firestore';
    import type { User, MonthlySnapshot } from '$lib/types/database';

    let userEmail = '';
    let students: any[] = [];
    let loading = true;

    onMount(async () => {
        if (auth.currentUser) {
            userEmail = auth.currentUser.email || '';
            await loadStudents();
        } else {
            // Setup auth listener just in case it takes a moment
            auth.onAuthStateChanged(async (firebaseUser) => {
                if (firebaseUser) {
                    userEmail = firebaseUser.email || '';
                    await loadStudents();
                }
            });
        }
    });

    async function loadStudents() {
        loading = true;
        try {
            const usersRef = collection(db, 'users');
            // Assuming we only want students or we filter by role
            const q = query(usersRef, where('role', '==', 'student'));
            const snapshot = await getDocs(q);

            let loadedStudents = [];

            for (const docSnap of snapshot.docs) {
                const userData = { uid: docSnap.id, ...docSnap.data() } as User;

                // Fetch latest monthly snapshot for performance fee
                let latestFee = 0;
                try {
                    const snapshotsRef = collection(db, `users/${userData.uid}/monthly_snapshots`);
                    const snapQuery = query(snapshotsRef, orderBy('createdAt', 'desc'), limit(1));
                    const monthSnap = await getDocs(snapQuery);
                    if (!monthSnap.empty) {
                        const snapData = monthSnap.docs[0].data() as MonthlySnapshot;
                        latestFee = snapData.performanceFee || 0;
                    }
                } catch (e) {
                    console.error("Error fetching snapshot for", userData.uid, e);
                }

                loadedStudents.push({
                    uid: userData.uid,
                    email: userData.email,
                    archetype: userData.currentArchetype || 'N/A',
                    streak: userData.streakCount || 0,
                    performanceFee: latestFee,
                    createdAt: userData.createdAt
                });
            }

            students = loadedStudents;
        } catch (error) {
            console.error("Error loading students:", error);
        } finally {
            loading = false;
        }
    }

    function exportToCSV() {
        if (students.length === 0) return;

        const headers = ['Email', 'Archetype', 'Streak', 'Performance Fee (USD)'];

        const rows = students.map(s => [
            s.email,
            s.archetype,
            s.streak,
            s.performanceFee.toFixed(2)
        ]);

        const csvContent = [
            headers.join(','),
            ...rows.map(e => e.join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', `dolarize_students_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    async function handleLogout() {
        await signOut(auth);
        goto('/admin/login');
    }
</script>

<svelte:head>
    <title>Admin Panel - Dólarize Focus Board</title>
</svelte:head>

<div class="min-h-screen bg-gray-900 text-white p-8">
    <div class="max-w-6xl mx-auto">
        <div class="flex justify-between items-center mb-8">
            <h1 class="text-3xl font-bold">Mentor Dashboard</h1>
            <div class="flex items-center gap-4">
                <span class="text-gray-400">{userEmail}</span>
                <button on:click={handleLogout} class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded font-medium">
                    Logout
                </button>
            </div>
        </div>

        <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-xl font-semibold">Student Overview</h2>
                <button
                    on:click={exportToCSV}
                    class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium disabled:opacity-50"
                    disabled={loading || students.length === 0}
                >
                    Download CSV
                </button>
            </div>

            {#if loading}
                <div class="text-center py-8 text-gray-400">Loading student data...</div>
            {:else if students.length === 0}
                <div class="text-center py-8 text-gray-400">No students found.</div>
            {:else}
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="bg-gray-700 text-gray-300 text-sm uppercase tracking-wide">
                                <th class="p-4 rounded-tl-lg">Email</th>
                                <th class="p-4">Archetype</th>
                                <th class="p-4">Streak</th>
                                <th class="p-4 rounded-tr-lg">Performance Fee</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-700">
                            {#each students as student}
                                <tr class="hover:bg-gray-750 transition-colors">
                                    <td class="p-4">{student.email}</td>
                                    <td class="p-4">
                                        <span class="inline-block px-2 py-1 bg-yellow-900 text-yellow-300 rounded text-xs font-bold">
                                            {student.archetype}
                                        </span>
                                    </td>
                                    <td class="p-4 font-medium">{student.streak} days</td>
                                    <td class="p-4 text-green-400 font-medium">${student.performanceFee.toFixed(2)}</td>
                                </tr>
                            {/each}
                        </tbody>
                    </table>
                </div>
            {/if}
        </div>
    </div>
</div>
