document.addEventListener("DOMContentLoaded", async () => {
    const auth = firebase.auth();

    auth.onAuthStateChanged(async (user) => {
        if (user) {
            const userId = user.uid;
            await loadRecommendations(userId);
        } else {
            console.log("User not logged in.");
            const container = document.getElementById("job-recommendations-container");
            container.innerHTML = "<p>Please log in to view recommendations.</p>";
        }
    });
});

async function loadRecommendations(userId) {
    const container = document.getElementById("job-recommendations-container");
    const noRecommendations = document.getElementById("no-recommendations");

    try {
        const response = await fetch(`http://127.0.0.1:5000/recommendations/${userId}`);
        const jobs = await response.json();

        if (response.status !== 200) {
            noRecommendations.textContent = jobs.error || "Failed to load recommendations.";
            return;
        }

        noRecommendations.style.display = "none";

        jobs.forEach(job => {
            const jobCard = document.createElement("div");
            jobCard.className = "job-card";
            jobCard.innerHTML = `
                <div class="job-header">
                    <h2>${job.title}</h2>
                </div>
                <p class="job-company">${job.company || "Unknown Company"}</p>
                <p class="job-source">Source: ${job.source || "N/A"}</p>
                <div class="job-footer">
                    <button onclick="window.open('${job.url || "#"}', '_blank')" class="apply-button">View Job</button>
                </div>
            `;
            container.appendChild(jobCard);
        });
    } catch (error) {
        console.error("Error loading recommendations:", error);
        noRecommendations.textContent = "Failed to load recommendations. Please try again.";
    }
}


document.getElementById("keywords-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const keywordsInput = document.getElementById("user_keywords");
    const errorMessage = document.getElementById("error-message");
    const progressContainer = document.getElementById("progress-container");
    const progressBar = document.getElementById("progress-bar");
    const keywords = keywordsInput.value.trim();

    if (!keywords) {
        errorMessage.textContent = "Please enter some keywords or phrases.";
        return;
    }

    const keywordsArray = keywords.split(',').map(k => k.trim()).filter(k => k);
    if (keywordsArray.length === 0) {
        errorMessage.textContent = "Please enter valid keywords.";
        return;
    }

    try {
        const user = firebase.auth().currentUser;
        if (!user) {
            alert("You need to log in to build recommendations.");
            return;
        }

       
        progressContainer.style.display = "block";
        progressBar.style.width = "0%";

        
        await firebase.firestore().collection("users").doc(user.uid).set(
            {
                preferences: { keywords: keywordsArray, updatedAt: firebase.firestore.FieldValue.serverTimestamp() }
            },
            { merge: true }
        );

        
        progressBar.style.width = "50%";

        
        const response = await fetch(`http://127.0.0.1:5000/rerun_recommendations/${user.uid}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: user.uid, keywords: keywordsArray })
        });

        if (response.status === 200) {
            progressBar.style.width = "100%";
            alert("Recommendations have been updated successfully!");
        } else {
            const result = await response.json();
            errorMessage.textContent = result.error || "Failed to update recommendations.";
        }
    } catch (error) {
        console.error("Error updating recommendations:", error);
        errorMessage.textContent = "An error occurred. Please try again.";
    } finally {
        setTimeout(() => {
            progressContainer.style.display = "none";
            progressBar.style.width = "0%";
        }, 2000);
    }
});
