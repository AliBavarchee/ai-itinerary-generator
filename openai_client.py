import openai
import os
import json
import logging
from dotenv import load_dotenv
from models import Activity, Day
from pydantic import ValidationError

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")



def generate_itinerary(destination: str, days: int) -> list:
    prompt = f"""
Generate a detailed {days}-day travel itinerary to {destination}. 
Include diverse activities with specific locations and times.

Output must be in this EXACT JSON format:
[
  {{
    "day": 1,
    "theme": "Cultural Exploration",
    "activities": [
      {{
        "time": "9:00 AM",
        "description": "Visit local museum",
        "location": "National Museum of History"
      }},
      {{
        "time": "1:00 PM",
        "description": "Lunch at traditional restaurant",
        "location": "Old Town Cafe"
      }}
    ]
  }}
]
"""
    try:
        response = openai.ChatCompletion.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            messages=[
                {"role": "system", "content": "You are a professional travel planner."},
                {"role": "user", "content": prompt}
            ],
            temperature=float(os.getenv("OPENAI_TEMPERATURE", 0.7)),
            max_tokens=2000
        )

        content = response['choices'][0]['message']['content']
        
        # Clean JSON extraction
        json_start = content.find('[')
        json_end = content.rfind(']') + 1
        json_str = content[json_start:json_end]
        
        # Parse and validate
        itinerary_data = json.loads(json_str)
        
        # Validate each day with Pydantic
        validated_days = []
        for day_data in itinerary_data:
            activities = [Activity(**act) for act in day_data["activities"]]
            day = Day(
                day=day_data["day"],
                theme=day_data["theme"],
                activities=activities
            )
            validated_days.append(day.dict())
            
        return validated_days
        
    except json.JSONDecodeError:
        logging.error("Invalid JSON format from OpenAI")
        raise ValueError("Failed to parse itinerary data")
    except ValidationError as ve:
        logging.error(f"Validation error: {str(ve)}")
        raise ValueError("Invalid itinerary structure")
    except KeyError:
        logging.error("Unexpected response format from OpenAI")
        raise ValueError("Failed to generate itinerary")