import { initializeApp, getApps, getApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
<<<<<<< fix-qa-dashboard-firebase-8217239342447709458
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
=======
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "dolarize-app",
>>>>>>> main
    storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
    appId: import.meta.env.VITE_FIREBASE_APP_ID
};

<<<<<<< fix-qa-dashboard-firebase-8217239342447709458
// Initialize Firebase only if it hasn't been initialized yet
const app = getApps().length > 0 ? getApp() : initializeApp(firebaseConfig);
=======
const app = !getApps().length ? initializeApp(firebaseConfig) : getApp();
>>>>>>> main
const db = getFirestore(app);

export { app, db };
