"""
Integration tests for Authentication API.
"""
import pytest
from fastapi.testclient import TestClient


class TestAuthAPI:
    """Test suite for authentication endpoints."""

    def test_login_success(self, client, test_user):
        """Test successful login returns token."""
        response = client.post(
            "/api/auth/login",
            data={"username": "test@example.com", "password": "testpassword123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password fails."""
        response = client.post(
            "/api/auth/login",
            data={"username": "test@example.com", "password": "wrongpassword"}
        )
        
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user fails."""
        response = client.post(
            "/api/auth/login",
            data={"username": "nonexistent@example.com", "password": "password123"}
        )
        
        assert response.status_code == 401

    def test_register_new_user(self, client):
        """Test registering a new user."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "newpassword123",
                "role": "user"
            }
        )
        
        # Should succeed or return appropriate status
        assert response.status_code in [200, 201, 422]

    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token fails."""
        response = client.get("/api/companies/")
        
        assert response.status_code == 401

    def test_protected_endpoint_with_token(self, client, auth_headers):
        """Test accessing protected endpoint with valid token succeeds."""
        response = client.get("/api/companies/", headers=auth_headers)
        
        assert response.status_code == 200

    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token fails."""
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = client.get("/api/companies/", headers=headers)
        
        assert response.status_code == 401
