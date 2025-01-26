import admin from "firebase-admin";
import { readFileSync } from "fs";


const serviceAccount = JSON.parse(
    readFileSync("C:/Users/Skmal/Downloads/wadhifati-db-firebase-adminsdk-15rnt-520ef3807a.json", "utf8")
);


admin.initializeApp({
    credential: admin.credential.cert(serviceAccount),
    databaseURL: "https://wadhifati-db-default-rtdb.firebaseio.com",
});


async function setAdminRole(uid) {
    try {
        await admin.auth().setCustomUserClaims(uid, { admin: true });
        console.log(`Admin role assigned to user: ${uid}`);
    } catch (error) {
        console.error("Error assigning admin role:", error);
    }
}

const userUID = "2pAc3CyQpgeWEEFiVNedymviMTd2"; 
setAdminRole(userUID);
