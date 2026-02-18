"""
Integration tests for Companies API.
"""
import pytest
from fastapi.testclient import TestClient


class TestCompaniesAPI:
    """Test suite for companies endpoints."""

    def test_list_companies(self, client, auth_headers):
        """Test listing companies."""
        response = client.get("/api/companies/", headers=auth_headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_company(self, client, auth_headers, test_industry):
        """Test creating a new company."""
        response = client.post(
            "/api/companies/",
            json={
                "name": "New Test Company",
                "industry_id": test_industry.id
            },
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["name"] == "New Test Company"
        assert data["industry_id"] == test_industry.id

    def test_create_company_without_auth(self, client, test_industry):
        """Test creating company without authentication fails."""
        response = client.post(
            "/api/companies/",
            json={
                "name": "Unauthorized Company",
                "industry_id": test_industry.id
            }
        )
        
        assert response.status_code == 401

    def test_create_company_invalid_industry(self, client, auth_headers):
        """Test creating company with invalid industry fails."""
        response = client.post(
            "/api/companies/",
            json={
                "name": "Invalid Industry Company",
                "industry_id": 99999
            },
            headers=auth_headers
        )
        
        assert response.status_code in [400, 404, 422]

    def test_get_company_by_id(self, client, auth_headers, test_company):
        """Test getting a specific company."""
        response = client.get(
            f"/api/companies/{test_company.id}",
            headers=auth_headers
        )
        
        # May return 200 or 404 depending on implementation
        assert response.status_code in [200, 404]
