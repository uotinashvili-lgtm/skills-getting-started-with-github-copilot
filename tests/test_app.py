import copy
from urllib.parse import quote
import pytest
from fastapi.testclient import TestClient
import src.app as app_module
from src.app import app

ORIGINAL_ACTIVITIES = copy.deepcopy(app_module.activities)

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict to its original state before each test."""
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

def test_root_redirects_to_index():
    # Arrange — no setup needed

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in (307, 308)
    assert response.headers["location"] == "/static/index.html"


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_all_activities():
    # Arrange — no setup needed

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) > 0


def test_get_activities_each_entry_has_required_fields():
    # Arrange
    required_fields = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")

    # Assert
    for name, details in response.json().items():
        assert required_fields <= details.keys(), f"{name} is missing fields"


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_adds_participant_successfully():
    # Arrange
    activity_name = "Chess Club"
    new_email = "newstudent@mergington.edu"
    encoded_activity_name = quote(activity_name, safe="")

    # Act
    response = client.post(
        f"/activities/{encoded_activity_name}/signup",
        params={"email": new_email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {new_email} for {activity_name}"}
    assert new_email in app_module.activities[activity_name]["participants"]


def test_signup_returns_404_for_unknown_activity():
    # Arrange
    unknown_activity = "Underwater Basket Weaving"
    email = "student@mergington.edu"
    encoded_activity_name = quote(unknown_activity, safe="")

    # Act
    response = client.post(
        f"/activities/{encoded_activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_returns_400_when_already_registered():
    # Arrange
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"  # pre-seeded in Chess Club
    encoded_activity_name = quote(activity_name, safe="")

    # Act
    response = client.post(
        f"/activities/{encoded_activity_name}/signup",
        params={"email": existing_email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_normalizes_email_and_prevents_case_variation_duplicates():
    # Arrange
    activity_name = "Chess Club"
    raw_email = "  NewStudent@Mergington.edu  "
    normalized_email = "newstudent@mergington.edu"
    encoded_activity_name = quote(activity_name, safe="")

    # Act
    first_response = client.post(
        f"/activities/{encoded_activity_name}/signup",
        params={"email": raw_email},
    )
    second_response = client.post(
        f"/activities/{encoded_activity_name}/signup",
        params={"email": "NEWSTUDENT@MERGINGTON.EDU"},
    )

    # Assert
    assert first_response.status_code == 200
    assert first_response.json() == {"message": f"Signed up {normalized_email} for {activity_name}"}
    assert normalized_email in app_module.activities[activity_name]["participants"]
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_invalid_email():
    # Arrange
    activity_name = "Chess Club"
    invalid_email = "not-an-email"
    encoded_activity_name = quote(activity_name, safe="")

    # Act
    response = client.post(
        f"/activities/{encoded_activity_name}/signup",
        params={"email": invalid_email},
    )

    # Assert
    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid email address"


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_unregister_removes_participant_successfully():
    # Arrange
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"  # pre-seeded in Chess Club
    encoded_activity_name = quote(activity_name, safe="")

    # Act
    response = client.delete(
        f"/activities/{encoded_activity_name}/signup",
        params={"email": existing_email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {existing_email} from {activity_name}"}
    assert existing_email not in app_module.activities[activity_name]["participants"]


def test_unregister_returns_404_for_unknown_activity():
    # Arrange
    unknown_activity = "Underwater Basket Weaving"
    email = "student@mergington.edu"
    encoded_activity_name = quote(unknown_activity, safe="")

    # Act
    response = client.delete(
        f"/activities/{encoded_activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_404_when_not_registered():
    # Arrange
    activity_name = "Chess Club"
    unregistered_email = "ghost@mergington.edu"
    encoded_activity_name = quote(activity_name, safe="")

    # Act
    response = client.delete(
        f"/activities/{encoded_activity_name}/signup",
        params={"email": unregistered_email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_normalizes_email_before_lookup():
    # Arrange
    activity_name = "Chess Club"
    raw_email = "  MICHAEL@MERGINGTON.EDU  "
    encoded_activity_name = quote(activity_name, safe="")

    # Act
    response = client.delete(
        f"/activities/{encoded_activity_name}/signup",
        params={"email": raw_email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": "Unregistered michael@mergington.edu from Chess Club"}
    assert "michael@mergington.edu" not in app_module.activities[activity_name]["participants"]
