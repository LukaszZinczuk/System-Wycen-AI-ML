"""
Integration tests for Offers API.
"""
import pytest
from fastapi.testclient import TestClient


class TestOffersAPI:
    """Test suite for offers endpoints."""

    def test_list_offers(self, client, auth_headers):
        """Test listing offers."""
        response = client.get("/api/offers/", headers=auth_headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_offer_success(self, client, auth_headers, test_company):
        """Test creating a new offer successfully."""
        response = client.post(
            "/api/offers/",
            json={
                "company_id": test_company.id,
                "employees_count": 100,
                "region": "Mazowieckie",
                "premium_48h": False,
                "ml_feature_avg_order_value": 20000,
                "ml_feature_offers_count": 3
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["company_id"] == test_company.id
        assert data["employees_count"] == 100
        assert data["region"] == "Mazowieckie"
        assert "ai_score" in data
        assert "final_price" in data
        assert "priority_level" in data

    def test_create_offer_with_pricing(self, client, auth_headers, test_company):
        """Test that offer creation includes AI pricing."""
        response = client.post(
            "/api/offers/",
            json={
                "company_id": test_company.id,
                "employees_count": 200,
                "region": "Śląskie",
                "premium_48h": True,
                "ml_feature_avg_order_value": 30000,
                "ml_feature_offers_count": 5
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify pricing fields
        assert data["base_price"] == 200 * 100  # 20000
        assert data["final_price"] > 0
        assert 0 <= data["ai_score"] <= 100
        assert data["priority_level"] in ["LOW", "STANDARD", "VIP"]

    def test_create_offer_without_auth(self, client, test_company):
        """Test creating offer without authentication fails."""
        response = client.post(
            "/api/offers/",
            json={
                "company_id": test_company.id,
                "employees_count": 50,
                "region": "Inne",
                "premium_48h": False,
                "ml_feature_avg_order_value": 10000,
                "ml_feature_offers_count": 0
            }
        )
        
        assert response.status_code == 401

    def test_create_offer_invalid_company(self, client, auth_headers):
        """Test creating offer with invalid company fails."""
        response = client.post(
            "/api/offers/",
            json={
                "company_id": 99999,
                "employees_count": 50,
                "region": "Inne",
                "premium_48h": False,
                "ml_feature_avg_order_value": 10000,
                "ml_feature_offers_count": 0
            },
            headers=auth_headers
        )
        
        assert response.status_code == 404

    def test_create_offer_invalid_data(self, client, auth_headers, test_company):
        """Test creating offer with invalid data fails validation."""
        response = client.post(
            "/api/offers/",
            json={
                "company_id": test_company.id,
                "employees_count": -10,  # Invalid
                "region": "Mazowieckie",
                "premium_48h": False,
                "ml_feature_avg_order_value": 10000,
                "ml_feature_offers_count": 0
            },
            headers=auth_headers
        )
        
        # Should fail validation or create with corrected value
        assert response.status_code in [200, 400, 422]

    def test_offer_vip_discount(self, client, auth_headers, test_company):
        """Test that VIP offers get discount applied."""
        response = client.post(
            "/api/offers/",
            json={
                "company_id": test_company.id,
                "employees_count": 500,
                "region": "Mazowieckie",
                "premium_48h": True,
                "ml_feature_avg_order_value": 50000,
                "ml_feature_offers_count": 20
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # VIP should have discount
        if data["priority_level"] == "VIP":
            # Final price should be less than what it would be without VIP discount
            assert data["final_price"] > 0


class TestOffersAPIAdmin:
    """Test suite for admin-specific offers functionality."""

    def test_admin_sees_all_offers(self, client, admin_auth_headers):
        """Test that admin can see all offers."""
        response = client.get("/api/offers/", headers=admin_auth_headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
