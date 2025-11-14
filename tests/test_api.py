"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    activities.clear()
    activities.update({
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
    })
    yield


def test_root_redirects_to_static(client):
    """Test that root URL redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert len(data["Chess Club"]["participants"]) == 2
    assert data["Chess Club"]["max_participants"] == 12


def test_signup_for_activity_success(client):
    """Test successful signup for an activity"""
    response = client.post(
        "/activities/Chess%20Club/signup?email=test@mergington.edu"
    )
    assert response.status_code == 200
    data = response.json()
    assert "Signed up test@mergington.edu for Chess Club" in data["message"]
    
    # Verify the participant was added
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert "test@mergington.edu" in activities_data["Chess Club"]["participants"]


def test_signup_for_nonexistent_activity(client):
    """Test signup for an activity that doesn't exist"""
    response = client.post(
        "/activities/Nonexistent%20Club/signup?email=test@mergington.edu"
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Activity not found"


def test_signup_already_registered(client):
    """Test signup when student is already registered"""
    # First signup
    client.post("/activities/Chess%20Club/signup?email=test@mergington.edu")
    
    # Try to signup again
    response = client.post(
        "/activities/Chess%20Club/signup?email=test@mergington.edu"
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Student is already signed up"


def test_unregister_from_activity_success(client):
    """Test successful unregistration from an activity"""
    # First, signup a student
    client.post("/activities/Chess%20Club/signup?email=test@mergington.edu")
    
    # Then unregister
    response = client.delete(
        "/activities/Chess%20Club/unregister?email=test@mergington.edu"
    )
    assert response.status_code == 200
    data = response.json()
    assert "Unregistered test@mergington.edu from Chess Club" in data["message"]
    
    # Verify the participant was removed
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert "test@mergington.edu" not in activities_data["Chess Club"]["participants"]


def test_unregister_not_registered(client):
    """Test unregistration when student is not registered"""
    response = client.delete(
        "/activities/Chess%20Club/unregister?email=notregistered@mergington.edu"
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Student is not registered for this activity"


def test_unregister_from_nonexistent_activity(client):
    """Test unregistration from an activity that doesn't exist"""
    response = client.delete(
        "/activities/Nonexistent%20Club/unregister?email=test@mergington.edu"
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Activity not found"


def test_multiple_signups_different_students(client):
    """Test multiple students signing up for the same activity"""
    emails = [
        "student1@mergington.edu",
        "student2@mergington.edu",
        "student3@mergington.edu"
    ]
    
    for email in emails:
        response = client.post(f"/activities/Chess%20Club/signup?email={email}")
        assert response.status_code == 200
    
    # Verify all students were added
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    participants = activities_data["Chess Club"]["participants"]
    
    for email in emails:
        assert email in participants


def test_activity_has_correct_structure(client):
    """Test that activity data has the correct structure"""
    response = client.get("/activities")
    data = response.json()
    
    for activity_name, activity_data in data.items():
        assert "description" in activity_data
        assert "schedule" in activity_data
        assert "max_participants" in activity_data
        assert "participants" in activity_data
        assert isinstance(activity_data["participants"], list)
        assert isinstance(activity_data["max_participants"], int)


def test_spots_calculation(client):
    """Test that spots are calculated correctly"""
    response = client.get("/activities")
    data = response.json()
    
    chess_club = data["Chess Club"]
    spots_left = chess_club["max_participants"] - len(chess_club["participants"])
    
    # Chess Club starts with 2 participants and max 12
    assert spots_left == 10
    
    # Add a participant
    client.post("/activities/Chess%20Club/signup?email=newstudent@mergington.edu")
    
    response = client.get("/activities")
    data = response.json()
    chess_club = data["Chess Club"]
    spots_left = chess_club["max_participants"] - len(chess_club["participants"])
    
    # Now should have 9 spots left
    assert spots_left == 9
