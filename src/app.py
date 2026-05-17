"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
import re
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Competitive basketball team with practice and games",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 15,
        "participants": ["james@mergington.edu"]
    },
    "Tennis Club": {
        "description": "Tennis lessons and friendly matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:00 PM",
        "max_participants": 10,
        "participants": ["alex@mergington.edu", "sara@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore painting, drawing, and sculpture techniques",
        "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
        "max_participants": 18,
        "participants": ["lisa@mergington.edu"]
    },
    "Drama Club": {
        "description": "Theater performances and acting workshops",
        "schedule": "Mondays and Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 25,
        "participants": ["marcus@mergington.edu", "nina@mergington.edu"]
    },
    "Science Club": {
        "description": "Hands-on experiments and scientific research projects",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 20,
        "participants": ["ryan@mergington.edu"]
    },
    "Debate Team": {
        "description": "Argumentative debate and public speaking competitions",
        "schedule": "Tuesdays and Saturdays, 3:00 PM - 4:30 PM",
        "max_participants": 16,
        "participants": ["grace@mergington.edu", "tyler@mergington.edu"]
    }
}


EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
)


def normalize_email(email: str) -> str:
    normalized_email = email.strip().lower()

    if not normalized_email:
        raise HTTPException(status_code=400, detail="Email cannot be empty")

    if not EMAIL_PATTERN.fullmatch(normalized_email):
        raise HTTPException(status_code=422, detail="Invalid email address")

    return normalized_email


def find_participant_index(participants: list[str], email: str):
    for index, participant in enumerate(participants):
        if participant.strip().lower() == email:
            return index
    return None


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]
    normalized_email = normalize_email(email)

    # Check if student is already signed up
    if find_participant_index(activity["participants"], normalized_email) is not None:
        raise HTTPException(status_code=400, detail="Student already signed up for this activity")

    # Add student
    activity["participants"].append(normalized_email)
    return {"message": f"Signed up {normalized_email} for {activity_name}"}


@app.delete("/activities/{activity_name}/signup")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]
    normalized_email = normalize_email(email)
    participant_index = find_participant_index(activity["participants"], normalized_email)

    # Check if student is signed up
    if participant_index is None:
        raise HTTPException(status_code=404, detail="Student is not signed up for this activity")

    # Remove student
    activity["participants"].pop(participant_index)
    return {"message": f"Unregistered {normalized_email} from {activity_name}"}
