import os
from google.cloud import firestore
from datetime import datetime
from typing import Dict

def init_firestore():
    return firestore.Client()

def save_initial_doc(db, job_id: str, destination: str, duration: int):
    initial_data = {
        "jobId": job_id,
        "status": "processing",
        "destination": destination,
        "durationDays": duration,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "completedAt": None,
        "itinerary": None,
        "error": None
    }
    db.collection("itineraries").document(job_id).set(initial_data)

def update_result_doc(db, job_id: str, result: Dict):
    result["completedAt"] = firestore.SERVER_TIMESTAMP
    db.collection("itineraries").document(job_id).update(result)