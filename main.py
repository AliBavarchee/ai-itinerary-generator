import os
import uuid
import threading
import logging
import webbrowser
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for
from firestore import init_firestore, save_initial_doc, update_result_doc
from openai_client import generate_itinerary
from models import ItineraryDocument, ItineraryInput

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set Google credentials 4 Firestore
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "ai-itinerary-generator.json"

app = Flask(__name__, static_folder='static', template_folder='templates')
db = init_firestore()

# Helper function
def format_timestamp(ts):
    if not ts:
        return ""
    try:
        if hasattr(ts, 'to_datetime'):
            dt = ts.to_datetime()
        elif isinstance(ts, datetime):
            dt = ts
        else:
            return str(ts)
        return dt.strftime("%B %d, %Y at %H:%M")
    except Exception as e:
        logger.error(f"Error formatting timestamp: {str(e)}")
        return str(ts)

# Main form page (index.html)
@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

# Form submission endpoint
@app.route('/generate', methods=['GET', 'POST'])
def generate_form():
    if request.method == 'GET':
        return redirect(url_for('home'))
    
    try:
        # Get form data
        destination = request.form.get('destination')
        duration_days = request.form.get('durationDays')
        
        # Validate input
        if not destination or not duration_days:
            return render_template('error.html',
                                  error_title="Missing Information",
                                  error_message="Please provide both destination and duration")
        
        try:
            duration_days = int(duration_days)
            if duration_days < 1 or duration_days > 30:
                raise ValueError("Duration must be between 1 and 30 days")
        except ValueError:
            return render_template('error.html',
                                  error_title="Invalid Duration",
                                  error_message="Please enter a valid number between 1 and 30")
        
        # Generate jobID
        job_id = str(uuid.uuid4())
        logger.info(f"Starting job {job_id} for {destination} ({duration_days} days)")
        
        # Save initial document -------->
        save_initial_doc(db, job_id, destination, duration_days)
        
        # Background processing
        def async_generate():
            try:
                logger.info(f"Processing job {job_id}")
                itinerary = generate_itinerary(destination, duration_days)
                
                doc = ItineraryDocument(
                    jobId=job_id,
                    status="completed",
                    destination=destination,
                    durationDays=duration_days,
                    itinerary=itinerary
                )
                update_result_doc(db, job_id, doc.dict(exclude_none=True))
                logger.info(f"Completed job {job_id}")
                
            except Exception as e:
                logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
                error_doc = ItineraryDocument(
                    jobId=job_id,
                    status="failed",
                    destination=destination,
                    durationDays=duration_days,
                    error=str(e)
                )
                update_result_doc(db, job_id, error_doc.dict(exclude_none=True))
        
        threading.Thread(target=async_generate).start()
        
        # Redirect to itinerary status page
        return redirect(url_for('get_itinerary', job_id=job_id))
    
    except Exception as e:
        logger.exception("Unexpected error in form submission")
        return render_template('error.html',
                              error_title="Server Error",
                              error_message="An unexpected error occurred while processing your request")

# Itinerary status page
@app.route('/itineraries/<job_id>', methods=['GET'])
def get_itinerary(job_id):
    try:
        doc_ref = db.collection("itineraries").document(job_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return render_template('error.html', 
                                  error_title="Itinerary Not Found",
                                  error_message=f"No itinerary found with ID: {job_id}"), 404
            
        data = doc.to_dict()
        status = data.get('status', 'unknown')
        
        # Format timestamps
        created_at = format_timestamp(data.get('createdAt'))
        completed_at = format_timestamp(data.get('completedAt'))
        
        # Handle different statuses
        if status == "completed":
            return render_template(
                'itinerary.html',
                job_id=job_id,
                destination=data.get('destination'),
                duration=data.get('durationDays'),
                itinerary=data.get('itinerary', []),
                created_at=created_at,
                completed_at=completed_at
            )
        elif status == "processing":
            return render_template('processing.html',
                                  job_id=job_id,
                                  destination=data.get('destination'),
                                  duration=data.get('durationDays'))
        elif status == "failed":
            return render_template('error.html',
                                  error_title="Generation Failed",
                                  error_message=data.get('error', 'Unknown error'))
        else:
            return render_template('error.html',
                                  error_title="Unknown Status",
                                  error_message=f"Unexpected status: {status}")
        
    except Exception as e:
        logger.error(f"Error retrieving itinerary: {str(e)}")
        return render_template('error.html',
                              error_title="Server Error",
                              error_message="An unexpected error occurred while fetching your itinerary"), 500


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200


def app_function(request):
    return app(request.environ, lambda status, headers: None)


if __name__ == "__main__":
    # Auto-open browser
    from threading import Timer
    def open_browser():
        webbrowser.open_new('http://localhost:8080')
    
    Timer(1, open_browser).start()
    app.run(host='0.0.0.0', port=8080, debug=True)