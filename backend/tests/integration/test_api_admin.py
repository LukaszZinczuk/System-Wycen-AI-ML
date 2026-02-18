"""
Integration tests for Admin API.
"""
import pytest
from fastapi.testclient import TestClient


class TestAdminDashboardAPI:
    """Test suite for admin dashboard endpoints."""

    def test_dashboard_admin_access(self, client, admin_auth_headers):
        """Test admin can access dashboard."""
        response = client.get("/api/admin/dashboard", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify dashboard stats structure
        assert "companies_count" in data
        assert "offers_count" in data
        assert "avg_offer_value" in data
        assert "top_5_companies" in data
        assert "industry_distribution" in data
        assert "avg_score_per_region" in data

    def test_dashboard_user_forbidden(self, client, auth_headers):
        """Test regular user cannot access admin dashboard."""
        response = client.get("/api/admin/dashboard", headers=auth_headers)
        
        assert response.status_code == 403

    def test_dashboard_unauthenticated(self, client):
        """Test unauthenticated user cannot access dashboard."""
        response = client.get("/api/admin/dashboard")
        
        assert response.status_code == 401

    def test_dashboard_stats_types(self, client, admin_auth_headers):
        """Test dashboard stats have correct types."""
        response = client.get("/api/admin/dashboard", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data["companies_count"], int)
        assert isinstance(data["offers_count"], int)
        assert isinstance(data["avg_offer_value"], (int, float))
        assert isinstance(data["top_5_companies"], list)
        assert isinstance(data["industry_distribution"], dict)
        assert isinstance(data["avg_score_per_region"], dict)


class TestAdminRecalculation:
    """Test suite for admin recalculation endpoints."""

    def test_recalc_scores_endpoint(self, client, admin_auth_headers):
        """Test recalculation endpoint exists and responds."""
        response = client.post("/api/admin/recalc_scores", headers=admin_auth_headers)
        
        # Should return success message
        assert response.status_code in [200, 202]
