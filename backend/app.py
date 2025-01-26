from flask import Flask, render_template, jsonify, request, send_from_directory
import firebase_admin
from firebase_admin import credentials, firestore
from sentence_transformers import SentenceTransformer, util
import threading
import logging
from job_scraper import scrape_all_jobs  


if not firebase_admin._apps:
    cred = credentials.Certificate("C:\\Users\\Skmal\\Downloads\\wadhifati-db-firebase-adminsdk-15rnt-520ef3807a.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()


model = SentenceTransformer("C:\\Users\\Skmal\\job_title_model_final")


app = Flask(__name__, template_folder='../frontend/Html', static_folder='../static')


logging.basicConfig(level=logging.INFO)


def fetch_job_listings():
    """Fetch job listings from Firestore."""
    try:
        job_docs = db.collection("jobs").stream()
        job_listings = [doc.to_dict() for doc in job_docs]
        logging.info(f"Fetched job listings: {job_listings}")
        return job_listings
    except Exception as e:
        logging.error(f"Error fetching job listings: {e}")
        return []


def rank_job_listings(keywords, job_listings):
    """Rank job listings based on similarity to keywords."""
    try:
        results = []
        for job in job_listings:
            title = job.get("title", "")
            if not title:
                continue  
            title_embedding = model.encode(title, convert_to_tensor=True)
            total_similarity = sum(
                util.cos_sim(title_embedding, model.encode(keyword, convert_to_tensor=True)).item()
                for keyword in keywords
            )
            avg_similarity = total_similarity / len(keywords)
            job["similarity"] = avg_similarity
            results.append(job)

        
        ranked_results = sorted(results, key=lambda x: x["similarity"], reverse=True)[:9]
        logging.info(f"Ranked job listings: {ranked_results}")
        return ranked_results
    except Exception as e:
        logging.error(f"Error ranking job listings: {e}")
        return []


def process_recommendations(user_id, keywords):
    """Process recommendations for a user and update Firestore."""
    try:
        logging.info(f"Processing recommendations for user: {user_id} with keywords: {keywords}")
        job_listings = fetch_job_listings()
        logging.info(f"Fetched {len(job_listings)} job listings")

        if not job_listings:
            logging.warning(f"No job listings found for user {user_id}")
            return

        
        top_jobs = rank_job_listings(keywords, job_listings)
        logging.info(f"Generated recommendations: {top_jobs}")

        db.collection("users").document(user_id).update({"top_jobs": top_jobs})
        logging.info(f"Successfully updated Firestore for user {user_id}")
    except Exception as e:
        logging.error(f"Error processing recommendations for user {user_id}: {e}")


@app.route('/rerun_recommendations/<user_id>', methods=['POST'])
def rerun_recommendations(user_id):
    """Endpoint to rerun recommendations for a user."""
    try:
        user_doc = db.collection("users").document(user_id).get()
        if not user_doc.exists:
            return jsonify({"error": "User not found"}), 404

        user_data = user_doc.to_dict()
        keywords = user_data.get("preferences", {}).get("keywords", [])

        if not keywords:
            return jsonify({"error": "No keywords found for the user"}), 400

        
        threading.Thread(target=process_recommendations, args=(user_id, keywords)).start()

        return jsonify({"message": "Recommendation process started"}), 200
    except Exception as e:
        logging.error(f"Error starting recommendation process for user {user_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/scrape_jobs', methods=['POST'])
def scrape_jobs_route():
    """Endpoint to trigger job scraping."""
    try:
        threading.Thread(target=scrape_all_jobs).start()
        return jsonify({"message": "Job scraping started successfully!"}), 200
    except Exception as e:
        logging.error(f"Error during job scraping: {e}")
        return jsonify({"error": "Job scraping failed!"}), 500


@app.route('/recommendations/<user_id>', methods=['GET'])
def recommendations(user_id):
    """Endpoint to fetch recommendations for a user."""
    try:
        user_doc = db.collection("users").document(user_id).get()
        if not user_doc.exists:
            return jsonify({"error": "User not found"}), 404

        user_data = user_doc.to_dict()
        top_jobs = user_data.get("top_jobs", [])

        return jsonify(top_jobs)
    except Exception as e:
        logging.error(f"Error fetching recommendations: {e}")
        return jsonify({"error": "Internal server error"}), 500



@app.route('/CSS/<path:filename>')
def serve_css(filename):
    return send_from_directory('../frontend/CSS', filename)

@app.route('/images/<path:filename>')
def serve_images(filename):
    return send_from_directory('../frontend/images', filename)



@app.route('/')
def index():
    return render_template('Home.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/profile')
def profile():
    return render_template('preferences.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/adminlogin')
def admin_login():
    return render_template('adminlogin.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/recommendations')
def recommendations_page():
    return render_template('rec.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
