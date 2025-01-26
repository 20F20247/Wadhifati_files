const functions = require("firebase-functions");
const admin = require("firebase-admin");

admin.initializeApp();


exports.listUsers = functions.https.onCall(async (data, context) => {
    if (!context.auth || !context.auth.token.admin) {
        throw new functions.https.HttpsError(
            "permission-denied",
            "Only admins can perform this action."
        );
    }

    let users = [];
    let nextPageToken;

    do {
        try {
            const result = await admin.auth().listUsers(1000, nextPageToken);
            users = users.concat(
                result.users.map((user) => ({
                    uid: user.uid,
                    email: user.email,
                }))
            );
            nextPageToken = result.pageToken;
        } catch (error) {
            throw new functions.https.HttpsError(
                "internal",
                "Error listing users.",
                error.message
            );
        }
    } while (nextPageToken);

    return { data: users };
});


exports.deleteUser = functions.https.onCall(async (data, context) => {
    if (!context.auth || !context.auth.token.admin) {
        throw new functions.https.HttpsError(
            "permission-denied",
            "Only admins can perform this action."
        );
    }

    const { uid } = data;
    if (!uid) {
        throw new functions.https.HttpsError(
            "invalid-argument",
            "User UID is required."
        );
    }

    try {
        await admin.auth().deleteUser(uid);
        return { success: true, message: "User deleted successfully." };
    } catch (error) {
        throw new functions.https.HttpsError(
            "internal",
            "Error deleting user.",
            error.message
        );
    }
});
