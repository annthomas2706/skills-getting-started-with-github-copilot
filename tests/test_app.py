"""
Backend tests for Mergington High School activity management API.

Tests follow the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and state
- Act: Execute the code being tested
- Assert: Verify the results
"""

import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Fixture providing a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def fresh_activities(monkeypatch):
    """
    Fixture providing a fresh copy of activities for each test.
    Uses monkeypatch to replace the activities dict in src.app module,
    ensuring each test starts with clean data and doesn't affect other tests.
    """
    # Create a deep copy of the original activities
    import src.app as app_module
    
    fresh_copy = copy.deepcopy(activities)
    
    # Monkeypatch the app module's activities dict
    monkeypatch.setattr(app_module, "activities", fresh_copy)
    
    # Return the fresh copy so tests can reference it if needed
    return fresh_copy


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, fresh_activities):
        """
        ARRANGE: No setup needed
        ACT: Make GET request to /activities
        ASSERT: Verify response contains all 9 activities with correct structure
        """
        # ACT
        response = client.get("/activities")
        
        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_returns_correct_structure(self, client, fresh_activities):
        """
        ARRANGE: No setup needed
        ACT: Make GET request to /activities
        ASSERT: Verify each activity has required fields
        """
        # ACT
        response = client.get("/activities")
        data = response.json()
        
        # ASSERT
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_get_activities_has_initial_participants(self, client, fresh_activities):
        """
        ARRANGE: No setup needed
        ACT: Make GET request to /activities
        ASSERT: Verify activities have the expected initial participants
        """
        # ACT
        response = client.get("/activities")
        data = response.json()
        
        # ASSERT
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]
        assert len(data["Chess Club"]["participants"]) == 2


class TestSignupSuccess:
    """Tests for successful signup scenarios."""

    def test_signup_success_adds_participant(self, client, fresh_activities):
        """
        ARRANGE: Prepare a new email and activity name
        ACT: Post signup request with valid data
        ASSERT: Verify response is 200 and participant is added
        """
        # ARRANGE
        email = "newstudent@test.edu"
        activity_name = "Basketball Team"
        
        # ACT
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            headers={"Content-Type": "application/json"}
        )
        
        # ASSERT
        assert response.status_code == 200
        assert "message" in response.json()
        
        # Verify participant was added by fetching activities
        activities_response = client.get("/activities")
        updated_activities = activities_response.json()
        assert email in updated_activities[activity_name]["participants"]

    def test_signup_increases_participant_count(self, client, fresh_activities):
        """
        ARRANGE: Get initial participant count for an activity
        ACT: Sign up a new participant
        ASSERT: Verify count increased by 1
        """
        # ARRANGE
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Tennis Club"]["participants"])
        
        email = "student@test.edu"
        activity_name = "Tennis Club"
        
        # ACT
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # ASSERT
        assert response.status_code == 200
        
        # Verify count increased
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity_name]["participants"])
        assert final_count == initial_count + 1

    def test_signup_returns_success_message(self, client, fresh_activities):
        """
        ARRANGE: Prepare signup data
        ACT: Post signup request
        ASSERT: Verify response contains appropriate message
        """
        # ARRANGE
        email = "student@test.edu"
        activity_name = "Art Studio"
        
        # ACT
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]


class TestSignupErrors:
    """Tests for signup error scenarios."""

    def test_signup_nonexistent_activity_returns_404(self, client, fresh_activities):
        """
        ARRANGE: Prepare data with non-existent activity name
        ACT: Post signup request
        ASSERT: Verify 404 response
        """
        # ARRANGE
        email = "student@test.edu"
        activity_name = "Nonexistent Activity"
        
        # ACT
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # ASSERT
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_signup_duplicate_email_returns_400(self, client, fresh_activities):
        """
        ARRANGE: Prepare email that's already registered
        ACT: Post signup request for same email
        ASSERT: Verify 400 response
        """
        # ARRANGE
        email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"
        
        # ACT
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # ASSERT
        assert response.status_code == 400
        assert "detail" in response.json()
        assert "already signed up" in response.json()["detail"]

    def test_signup_duplicate_email_does_not_duplicate_participant(self, client, fresh_activities):
        """
        ARRANGE: Sign up a participant, then attempt duplicate signup
        ACT: Try to sign up same participant twice
        ASSERT: Verify participant appears only once
        """
        # ARRANGE
        email = "uniquestudent@test.edu"
        activity_name = "Music Band"
        
        # First signup (should succeed)
        response1 = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Get count after first signup
        activities_response = client.get("/activities")
        count_after_first = len(activities_response.json()[activity_name]["participants"])
        
        # ACT: Try duplicate signup
        response2 = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # ASSERT
        assert response2.status_code == 400
        
        # Verify participant count didn't increase (no duplicate added)
        activities_response = client.get("/activities")
        count_after_second = len(activities_response.json()[activity_name]["participants"])
        assert count_after_second == count_after_first


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint."""

    def test_remove_participant_success(self, client, fresh_activities):
        """
        ARRANGE: Identify a participant in an activity
        ACT: Send DELETE request to remove them
        ASSERT: Verify 200 response and participant removed
        """
        # ARRANGE
        email = "michael@mergington.edu"
        activity_name = "Chess Club"
        
        # ACT
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # ASSERT
        assert response.status_code == 200
        assert "message" in response.json()
        
        # Verify removed from participants list
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity_name]["participants"]

    def test_remove_participant_decreases_count(self, client, fresh_activities):
        """
        ARRANGE: Get initial participant count
        ACT: Remove a participant
        ASSERT: Verify count decreased by 1
        """
        # ARRANGE
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Chess Club"]["participants"])
        
        email = "daniel@mergington.edu"
        activity_name = "Chess Club"
        
        # ACT
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # ASSERT
        assert response.status_code == 200
        
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity_name]["participants"])
        assert final_count == initial_count - 1

    def test_remove_participant_nonexistent_activity_returns_404(self, client, fresh_activities):
        """
        ARRANGE: Prepare data with non-existent activity
        ACT: Send DELETE request
        ASSERT: Verify 404 response
        """
        # ARRANGE
        email = "student@test.edu"
        activity_name = "Nonexistent Activity"
        
        # ACT
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # ASSERT
        assert response.status_code == 404

    def test_remove_participant_not_in_activity_returns_404(self, client, fresh_activities):
        """
        ARRANGE: Use email not registered in the activity
        ACT: Send DELETE request
        ASSERT: Verify 404 response
        """
        # ARRANGE
        email = "notregistered@test.edu"
        activity_name = "Chess Club"
        
        # ACT
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # ASSERT
        assert response.status_code == 404

    def test_remove_different_participants_independently(self, client, fresh_activities):
        """
        ARRANGE: Activity has multiple participants
        ACT: Remove one participant
        ASSERT: Verify only that participant removed, others remain
        """
        # ARRANGE
        email_to_remove = "michael@mergington.edu"
        email_to_keep = "daniel@mergington.edu"
        activity_name = "Chess Club"
        
        # ACT
        response = client.delete(
            f"/activities/{activity_name}/participants/{email_to_remove}"
        )
        
        # ASSERT
        assert response.status_code == 200
        
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        
        assert email_to_remove not in participants
        assert email_to_keep in participants


class TestRootRedirect:
    """Tests for GET / redirect endpoint."""

    def test_root_redirects_to_index(self, client, fresh_activities):
        """
        ARRANGE: No setup needed
        ACT: Make GET request to /
        ASSERT: Verify redirect to /static/index.html
        """
        # ACT
        response = client.get("/", follow_redirects=False)
        
        # ASSERT
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]

    def test_root_with_follow_redirects(self, client, fresh_activities):
        """
        ARRANGE: No setup needed
        ACT: Make GET request to / with follow_redirects=True
        ASSERT: Verify final response contains HTML content
        """
        # ACT
        response = client.get("/", follow_redirects=True)
        
        # ASSERT
        assert response.status_code == 200


class TestIntegrationScenarios:
    """Integration tests combining multiple operations."""

    def test_signup_then_remove_workflow(self, client, fresh_activities):
        """
        ARRANGE: Fresh activities state
        ACT: Sign up participant, then remove them
        ASSERT: Verify both operations succeed and state is correct
        """
        # ARRANGE
        email = "integration@test.edu"
        activity_name = "Debate Club"
        
        # ACT: Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # ASSERT signup
        assert signup_response.status_code == 200
        
        # Verify added
        activities_before_remove = client.get("/activities").json()
        assert email in activities_before_remove[activity_name]["participants"]
        
        # ACT: Remove
        remove_response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # ASSERT remove
        assert remove_response.status_code == 200
        
        # Verify removed
        activities_after_remove = client.get("/activities").json()
        assert email not in activities_after_remove[activity_name]["participants"]

    def test_multiple_signups_same_activity(self, client, fresh_activities):
        """
        ARRANGE: Multiple different emails
        ACT: Sign up all to same activity
        ASSERT: All added successfully
        """
        # ARRANGE
        emails = ["student1@test.edu", "student2@test.edu", "student3@test.edu"]
        activity_name = "Science Club"
        
        # ACT: Sign up all
        for email in emails:
            response = client.post(
                f"/activities/{activity_name}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # ASSERT: All present
        final_activities = client.get("/activities").json()
        participants = final_activities[activity_name]["participants"]
        
        for email in emails:
            assert email in participants
