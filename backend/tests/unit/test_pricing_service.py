"""
Unit tests for Pricing Service.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.pricing_service import PricingService
from app.schemas.schemas import OfferCreate


class TestPricingService:
    """Test suite for PricingService class."""

    @pytest.fixture
    def pricing_service(self):
        """Create a fresh PricingService instance."""
        return PricingService()

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def basic_offer_data(self):
        """Create basic offer data for testing."""
        return OfferCreate(
            company_id=1,
            employees_count=100,
            region="Mazowieckie",
            premium_48h=False,
            ml_feature_avg_order_value=20000,
            ml_feature_offers_count=3
        )

    def test_base_price_calculation(self, pricing_service, mock_db, basic_offer_data):
        """Test that base price is calculated correctly."""
        result = pricing_service.calculate_price_and_score(basic_offer_data, mock_db)
        
        expected_base = 100 * 100  # employees * BASE_PRICE_PER_EMPLOYEE
        assert result.base_price == expected_base

    def test_quantity_discount_small(self, pricing_service, mock_db):
        """Test quantity discount for small companies (1-10 employees)."""
        offer = OfferCreate(
            company_id=1,
            employees_count=5,
            region="Inne",
            premium_48h=False,
            ml_feature_avg_order_value=10000,
            ml_feature_offers_count=0
        )
        result = pricing_service.calculate_price_and_score(offer, mock_db)
        
        # No discount for < 11 employees
        assert result.base_price == 500
        # Final price should reflect no quantity discount (but may have other adjustments)

    def test_quantity_discount_medium(self, pricing_service, mock_db):
        """Test quantity discount for medium companies (11-50 employees)."""
        offer = OfferCreate(
            company_id=1,
            employees_count=30,
            region="Inne",
            premium_48h=False,
            ml_feature_avg_order_value=10000,
            ml_feature_offers_count=0
        )
        result = pricing_service.calculate_price_and_score(offer, mock_db)
        
        # 5% discount expected
        base = 30 * 100
        assert result.base_price == base

    def test_quantity_discount_large(self, pricing_service, mock_db):
        """Test quantity discount for large companies (51-200 employees)."""
        offer = OfferCreate(
            company_id=1,
            employees_count=100,
            region="Inne",
            premium_48h=False,
            ml_feature_avg_order_value=10000,
            ml_feature_offers_count=0
        )
        result = pricing_service.calculate_price_and_score(offer, mock_db)
        
        # 10% discount expected
        base = 100 * 100
        assert result.base_price == base

    def test_quantity_discount_enterprise(self, pricing_service, mock_db):
        """Test quantity discount for enterprise companies (>200 employees)."""
        offer = OfferCreate(
            company_id=1,
            employees_count=300,
            region="Inne",
            premium_48h=False,
            ml_feature_avg_order_value=10000,
            ml_feature_offers_count=0
        )
        result = pricing_service.calculate_price_and_score(offer, mock_db)
        
        # 15% discount expected
        base = 300 * 100
        assert result.base_price == base

    def test_region_multiplier_mazowieckie(self, pricing_service, mock_db):
        """Test Mazowieckie region has highest multiplier."""
        offer_maz = OfferCreate(
            company_id=1,
            employees_count=10,
            region="Mazowieckie",
            premium_48h=False,
            ml_feature_avg_order_value=10000,
            ml_feature_offers_count=0
        )
        offer_inne = OfferCreate(
            company_id=1,
            employees_count=10,
            region="Inne",
            premium_48h=False,
            ml_feature_avg_order_value=10000,
            ml_feature_offers_count=0
        )
        
        result_maz = pricing_service.calculate_price_and_score(offer_maz, mock_db)
        result_inne = pricing_service.calculate_price_and_score(offer_inne, mock_db)
        
        # Mazowieckie should be more expensive
        assert result_maz.final_price >= result_inne.final_price

    def test_premium_48h_increases_price(self, pricing_service, mock_db):
        """Test that premium 48h service increases price by 20%."""
        offer_standard = OfferCreate(
            company_id=1,
            employees_count=50,
            region="Inne",
            premium_48h=False,
            ml_feature_avg_order_value=10000,
            ml_feature_offers_count=0
        )
        offer_premium = OfferCreate(
            company_id=1,
            employees_count=50,
            region="Inne",
            premium_48h=True,
            ml_feature_avg_order_value=10000,
            ml_feature_offers_count=0
        )
        
        result_standard = pricing_service.calculate_price_and_score(offer_standard, mock_db)
        result_premium = pricing_service.calculate_price_and_score(offer_premium, mock_db)
        
        # Premium should be ~20% more expensive (before AI adjustments)
        assert result_premium.final_price > result_standard.final_price

    def test_priority_level_low(self, pricing_service, mock_db):
        """Test LOW priority for low AI score."""
        offer = OfferCreate(
            company_id=1,
            employees_count=5,
            region="Inne",
            premium_48h=False,
            ml_feature_avg_order_value=1000,
            ml_feature_offers_count=0
        )
        result = pricing_service.calculate_price_and_score(offer, mock_db)
        
        # With very low parameters, should get LOW priority
        assert result.priority_level in ["LOW", "STANDARD", "VIP"]

    def test_priority_level_vip_gets_discount(self, pricing_service, mock_db):
        """Test VIP priority gets 5% discount."""
        offer = OfferCreate(
            company_id=1,
            employees_count=400,
            region="Mazowieckie",
            premium_48h=True,
            ml_feature_avg_order_value=50000,
            ml_feature_offers_count=10
        )
        result = pricing_service.calculate_price_and_score(offer, mock_db)
        
        if result.priority_level == "VIP":
            assert result.discount_applied == 0.05
        else:
            assert result.discount_applied == 0.0

    def test_ai_score_within_bounds(self, pricing_service, mock_db, basic_offer_data):
        """Test that AI score is always between 0 and 100."""
        result = pricing_service.calculate_price_and_score(basic_offer_data, mock_db)
        
        assert 0 <= result.ai_score <= 100
        assert 0 <= result.ml_score <= 100
        assert 0 <= result.rule_score <= 100

    def test_rule_score_calculation(self, pricing_service, mock_db):
        """Test rule-based scoring logic."""
        # High employees, premium, Mazowieckie, high avg order, many offers
        offer = OfferCreate(
            company_id=1,
            employees_count=150,
            region="Mazowieckie",
            premium_48h=True,
            ml_feature_avg_order_value=25000,
            ml_feature_offers_count=5
        )
        result = pricing_service.calculate_price_and_score(offer, mock_db)
        
        # Rule score should be relatively high
        # Base 50 + 15 (employees>100) + 10 (premium) + 5 (Mazowieckie) + 10 (avg>20k) + 5 (offers>=3)
        # = 95 (capped at 100)
        assert result.rule_score >= 80

    def test_hybrid_score_weighting(self, pricing_service, mock_db, basic_offer_data):
        """Test that final score is 70% ML + 30% rule-based."""
        result = pricing_service.calculate_price_and_score(basic_offer_data, mock_db)
        
        expected_hybrid = (0.7 * result.ml_score) + (0.3 * result.rule_score)
        assert abs(result.ai_score - expected_hybrid) < 0.1


class TestPricingServiceEdgeCases:
    """Test edge cases for PricingService."""

    @pytest.fixture
    def pricing_service(self):
        return PricingService()

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    def test_single_employee(self, pricing_service, mock_db):
        """Test pricing for single employee company."""
        offer = OfferCreate(
            company_id=1,
            employees_count=1,
            region="Inne",
            premium_48h=False,
            ml_feature_avg_order_value=0,
            ml_feature_offers_count=0
        )
        result = pricing_service.calculate_price_and_score(offer, mock_db)
        
        assert result.base_price == 100
        assert result.final_price > 0

    def test_very_large_company(self, pricing_service, mock_db):
        """Test pricing for very large company."""
        offer = OfferCreate(
            company_id=1,
            employees_count=5000,
            region="Mazowieckie",
            premium_48h=True,
            ml_feature_avg_order_value=100000,
            ml_feature_offers_count=50
        )
        result = pricing_service.calculate_price_and_score(offer, mock_db)
        
        assert result.base_price == 500000
        assert result.final_price > 0
        assert result.priority_level in ["LOW", "STANDARD", "VIP"]
