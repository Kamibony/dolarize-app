import { initializeApp, getApps, getApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: "AIzaSyAct_Zdloy0OrC9TlwILU0WAHru7rVhZLk",
  authDomain: "dolarize-app.firebaseapp.com",
  projectId: "dolarize-app",
  storageBucket: "dolarize-app.firebasestorage.app",
  messagingSenderId: "493794054971",
  appId: "1:493794054971:web:1ff2314020d64b08749d1e",
  measurementId: "G-WDYFBV9051"
};

const app = !getApps().length ? initializeApp(firebaseConfig) : getApp();
const db = getFirestore(app);
const auth = getAuth(app);

export { app, db, auth };
