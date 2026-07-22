import { Connection, PublicKey, LAMPORTS_PER_SOL } from '@solana/web3.js';

let cachedPrice = 0;
let cacheTimestamp = 0;
const CACHE_DURATION_MS = 60000;

export async function getSolPriceInUsd(): Promise<number> {
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
        return cachedPrice > 0 ? cachedPrice : 0;
    }
}

export async function getSolanaBalance(address: string) {
    const pubKey = new PublicKey(address);
    const rpcUrl = import.meta.env.VITE_SOLANA_RPC_URL || 'https://api.mainnet-beta.solana.com';
    const connection = new Connection(rpcUrl, 'confirmed');

    const balanceLamports = await connection.getBalance(pubKey);
    const balanceSol = balanceLamports / LAMPORTS_PER_SOL;

    const priceUsd = await getSolPriceInUsd();
    const balanceUsd = balanceSol * priceUsd;

    return {
        address,
        balanceSol,
        priceUsd,
        balanceUsd
    };
}
