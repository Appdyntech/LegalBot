import { initializeApp } from "firebase/app";
import {
  getAuth,
  GoogleAuthProvider,
  signInWithPopup,
  signOut,
  onAuthStateChanged,
  setPersistence,
  browserLocalPersistence,
} from "firebase/auth";

// ✅ Firebase Config (from Firebase Console → Web App config)
const firebaseConfig = {
  apiKey: "AIzaSyCXlpR7njhxxOwfmYHe8Bg3JlFLGxTxbnU",
  authDomain: "legalcbot.firebaseapp.com",
  projectId: "legalcbot",
  storageBucket: "legalcbot.appspot.com",
  messagingSenderId: "472601913147",
  appId: "1:472601913147:web:2763ef33c494e957f3391e",
  measurementId: "G-302X18JTMC",
};

// 🚀 Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();
provider.setCustomParameters({ prompt: "select_account" });

// 🧠 Keep user signed in
setPersistence(auth, browserLocalPersistence)
  .then(() => console.log("🔐 Firebase persistence: LOCAL"))
  .catch((e) => console.warn("⚠️ Persistence setup error:", e.message));

// 👀 Listen to auth changes
onAuthStateChanged(auth, async (user) => {
  if (user) {
    console.log("✅ Firebase user signed in:", user.email);
    const token = await user.getIdToken(true);
    localStorage.setItem("token", token);
    localStorage.setItem(
      "user",
      JSON.stringify({
        name: user.displayName,
        email: user.email,
        picture: user.photoURL,
      })
    );
    console.log("🔑 Firebase token saved");
  } else {
    console.log("⚠️ No Firebase user signed in");
    localStorage.removeItem("token");
    localStorage.removeItem("user");
  }
});

// 🔐 Google Sign-in popup
export async function signInWithGoogle() {
  try {
    console.log("🚀 Starting Google Sign-in...");
    const result = await signInWithPopup(auth, provider);
    const user = result.user;
    const idToken = await user.getIdToken(true);
    localStorage.setItem("token", idToken);
    localStorage.setItem(
      "user",
      JSON.stringify({
        name: user.displayName,
        email: user.email,
        picture: user.photoURL,
      })
    );
    console.log("✅ Logged in as:", user.email);
    return user;
  } catch (error: any) {
    console.error("❌ Google Sign-in error:", error);
    alert("Sign-in failed. Ensure localhost/127.0.0.1 is an authorized domain.");
    throw error;
  }
}

// 🚪 Logout
export async function logout() {
  await signOut(auth);
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  console.log("👋 Logged out");
}

(window as any).firebaseAuth = auth;
console.log("🔥 Firebase Auth ready (window.firebaseAuth)");

export { app, auth };
