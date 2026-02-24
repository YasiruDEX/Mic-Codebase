import { initializeApp } from "firebase/app";
import { getDatabase } from "firebase/database";

// Your web app's Firebase configuration
const firebaseConfig = {
    // We use the database URL provided. Realtime DB only requires databaseURL and projectId
    databaseURL: "https://classroom-bot-a7454-default-rtdb.asia-southeast1.firebasedatabase.app/",
    projectId: "classroom-bot-a7454"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Realtime Database and get a reference to the service
export const db = getDatabase(app);
