export type UserRole = 'student' | 'admin';

export interface User {
    uid: string; // The user's unique ID
    email: string;
    role: UserRole;
    currentArchetype?: string; // e.g., 'A', 'B', 'C'
    streakCount: number;
    practicalSkills: string[]; // Denormalized list of skills/tags
    createdAt: Date;
    updatedAt: Date;
}

export interface Wallet {
    walletId: string; // e.g., could be the Solana address itself or a generated ID
    address: string; // Primary Solana public address for MVP
    network: 'solana'; // Future proofing for Phase 1
    isPrimary: boolean;
    addedAt: Date;
}

export interface DailyLog {
    id: string; // Doc ID formatted as YYYY-MM-DD
    date: Date;
    habitsCompleted: string[]; // List of habit IDs or names completed
    notes?: string;
    createdAt: Date;
}

export interface MonthlySnapshot {
    monthId: string; // e.g., YYYY-MM
    startUsdBalance: number;
    endUsdBalance: number;
    deltaPercentage: number;
    performanceFee: number; // Pre-calculated fee
    createdAt: Date;
}

export interface Diagnostic {
    diagnosticId: string; // Unique ID for the quiz attempt
    answers: Record<string, any>; // The 15-question answers
    resultArchetype: string;
    takenAt: Date;
}
