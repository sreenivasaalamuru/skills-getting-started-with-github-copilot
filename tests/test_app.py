import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def restore_participants():
    participant_snapshots = {
        name: activity["participants"].copy()
        for name, activity in activities.items()
    }
    yield
    for name, participants in participant_snapshots.items():
        activities[name]["participants"][:] = participants


def test_get_activities_returns_available_activities(client):
    # Arrange
    activity_name = "Soccer Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert activity_name in response.json()
    assert response.json()[activity_name]["participants"] == []


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Soccer Club"
    email = "new-student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name.replace(' ', '%20')}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Soccer Club"
    email = "existing-student@mergington.edu"
    activities[activity_name]["participants"][:] = [email]

    # Act
    response = client.post(
        f"/activities/{activity_name.replace(' ', '%20')}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert activities[activity_name]["participants"] == [email]


def test_signup_returns_not_found_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_only_selected_participant(client):
    # Arrange
    activity_name = "Soccer Club"
    email = "remove-student@mergington.edu"
    remaining_email = "remaining-student@mergington.edu"
    activities[activity_name]["participants"][:] = [email, remaining_email]

    # Act
    response = client.delete(
        f"/activities/{activity_name.replace(' ', '%20')}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert activities[activity_name]["participants"] == [remaining_email]


def test_unregister_returns_not_found_for_unregistered_participant(client):
    # Arrange
    activity_name = "Soccer Club"
    email = "not-signed-up@mergington.edu"
    remaining_email = "remaining-student@mergington.edu"
    activities[activity_name]["participants"][:] = [remaining_email]

    # Act
    response = client.delete(
        f"/activities/{activity_name.replace(' ', '%20')}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert activities[activity_name]["participants"] == [remaining_email]