import admin from "firebase-admin";
import { readFileSync } from "fs";

const serviceAccount = JSON.parse(
    readFileSync("C:/Users/Skmal/Downloads/wadhifati-db-firebase-adminsdk-15rnt-520ef3807a.json", "utf8")
);

admin.initializeApp({
    credential: admin.credential.cert(serviceAccount),
    databaseURL: "https://wadhifati-db-default-rtdb.firebaseio.com",
});


async function setAdminRoles(uids) {
    for (const uid of uids) {
        try {
            await admin.auth().setCustomUserClaims(uid, { admin: true });
            console.log(`Admin role assigned to user: ${uid}`);
        } catch (error) {
            console.error(`Error assigning admin role to user ${uid}:`, error);
        }
    }
}


async function revokeAdminRole(uid) {
    try {
        
        const user = await admin.auth().getUser(uid);
        const claims = user.customClaims || {};

        
        delete claims.admin;

        await admin.auth().setCustomUserClaims(uid, claims);
        console.log(`Admin role revoked for user: ${uid}`);
    } catch (error) {
        console.error(`Error revoking admin role for user ${uid}:`, error);
    }
}


const adminUIDs = [
    "2pAc3CyQpgeWEEFiVNedymviMTd2"
];

const revokeUID =
    "qsBN0xnMp6UuwONHHMfktqA9WNb2";


setAdminRoles(adminUIDs);


revokeAdminRole(revokeUID);
