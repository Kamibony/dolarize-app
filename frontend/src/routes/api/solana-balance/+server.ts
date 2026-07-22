import { json } from '@sveltejs/kit';
import { Connection, PublicKey, LAMPORTS_PER_SOL } from '@solana/web3.js';
import type { RequestHandler } from './$types';

// Simple in-memory cache for SOL/USD price to avoid rate limits
let cachedPrice = 0;
let cacheTimestamp = 0;
const CACHE_DURATION_MS = 60000; // 60 seconds

async function getSolPriceInUsd(): Promise<number> {
    const now = Date.now();
    if (cachedPrice > 0 && (now - cacheTimestamp < CACHE_DURATION_MS)) {
        return cachedPrice;
    }

    try {
        const response = await fetch('https://price.jup.ag/v4/price?ids=SOL');
        if (!response.ok) {
            throw new Error(`Jupiter API error: ${response.status}`);
        }
        const data = await response.json();
        const price = data.data.SOL.price;

        cachedPrice = price;
        cacheTimestamp = now;
        return price;
    } catch (error) {
        console.error("Failed to fetch SOL price:", error);
        // Fallback to cache if available even if expired, or return 0
        return cachedPrice > 0 ? cachedPrice : 0;
    }
}

export const GET: RequestHandler = async ({ url, setHeaders }) => {
    const address = url.searchParams.get('address');

    if (!address) {
        return json({ error: 'Address is required' }, { status: 400 });
    }

    try {
        const pubKey = new PublicKey(address);
        // Using mainnet-beta public RPC. In production, this could be replaced with an environment variable containing a Helius/QuickNode URL.
        const rpcUrl = import.meta.env.VITE_SOLANA_RPC_URL || 'https://api.mainnet-beta.solana.com';
        const connection = new Connection(rpcUrl, 'confirmed');

        const balanceLamports = await connection.getBalance(pubKey);
        const balanceSol = balanceLamports / LAMPORTS_PER_SOL;

        const priceUsd = await getSolPriceInUsd();
        const balanceUsd = balanceSol * priceUsd;

        // Cache the response for 30 seconds on the client side
        setHeaders({
            'Cache-Control': 'public, max-age=30'
        });

        return json({
            address,
            balanceSol,
            priceUsd,
            balanceUsd
        });
    } catch (error: any) {
        console.error("Solana balance error:", error);
        return json({ error: error.message || 'Failed to fetch balance' }, { status: 500 });
    }
};
