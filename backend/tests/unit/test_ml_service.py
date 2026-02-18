"""
Unit tests for ML Service.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock


class TestMLService:
    """Test suite for MLService class."""

    def test_predict_returns_float(self):
        """Test that predict returns a float value."""
        from app.services.ml_service import ml_service
        
        result = ml_service.predict(
            employees_count=100,
            region="Mazowieckie",
            premium=True,
            avg_order_value=25000,
            offers_count=5,
            industry_risk_factor=0.3
        )
        
        assert isinstance(result, float)
        assert 0 <= result <= 100

    def test_predict_high_employees_high_score(self):
        """Test that more employees generally leads to higher score."""
        from app.services.ml_service import ml_service
        
        low_employees_score = ml_service.predict(
            employees_count=10,
            region="Inne",
            premium=False,
            avg_order_value=5000,
            offers_count=0,
            industry_risk_factor=0.5
        )
        
        high_employees_score = ml_service.predict(
            employees_count=400,
            region="Inne",
            premium=False,
            avg_order_value=5000,
            offers_count=0,
            industry_risk_factor=0.5
        )
        
        assert high_employees_score > low_employees_score

    def test_predict_premium_increases_score(self):
        """Test that premium service increases score."""
        from app.services.ml_service import ml_service
        
        non_premium_score = ml_service.predict(
            employees_count=100,
            region="Mazowieckie",
            premium=False,
            avg_order_value=20000,
            offers_count=3,
            industry_risk_factor=0.3
        )
        
        premium_score = ml_service.predict(
            employees_count=100,
            region="Mazowieckie",
            premium=True,
            avg_order_value=20000,
            offers_count=3,
            industry_risk_factor=0.3
        )
        
        assert premium_score > non_premium_score

    def test_predict_high_risk_lowers_score(self):
        """Test that higher industry risk lowers score."""
        from app.services.ml_service import ml_service
        
        low_risk_score = ml_service.predict(
            employees_count=100,
            region="Mazowieckie",
            premium=True,
            avg_order_value=20000,
            offers_count=3,
            industry_risk_factor=0.1
        )
        
        high_risk_score = ml_service.predict(
            employees_count=100,
            region="Mazowieckie",
            premium=True,
            avg_order_value=20000,
            offers_count=3,
            industry_risk_factor=0.9
        )
        
        assert low_risk_score > high_risk_score

    def test_predict_unknown_region_handled(self):
        """Test that unknown region doesn't cause error."""
        from app.services.ml_service import ml_service
        
        result = ml_service.predict(
            employees_count=100,
            region="UnknownRegion",
            premium=True,
            avg_order_value=20000,
            offers_count=3,
            industry_risk_factor=0.3
        )
        
        assert isinstance(result, float)
        assert 0 <= result <= 100

    def test_predict_edge_case_zero_employees(self):
        """Test prediction with edge case values."""
        from app.services.ml_service import ml_service
        
        result = ml_service.predict(
            employees_count=1,
            region="Mazowieckie",
            premium=False,
            avg_order_value=0,
            offers_count=0,
            industry_risk_factor=0.0
        )
        
        assert isinstance(result, float)

    def test_predict_edge_case_max_values(self):
        """Test prediction with maximum values."""
        from app.services.ml_service import ml_service
        
        result = ml_service.predict(
            employees_count=1000,
            region="Mazowieckie",
            premium=True,
            avg_order_value=100000,
            offers_count=50,
            industry_risk_factor=1.0
        )
        
        assert isinstance(result, float)


class TestMLServiceModelTraining:
    """Test suite for ML model training."""

    def test_model_is_loaded_or_trained(self):
        """Test that model is available after initialization."""
        from app.services.ml_service import ml_service
        
        assert ml_service.model is not None
        assert ml_service.encoder is not None

    def test_encoder_has_known_regions(self):
        """Test that encoder knows expected regions."""
        from app.services.ml_service import ml_service
        
        expected_regions = ['Mazowieckie', 'Slaskie', 'Malopolskie', 'Inne']
        for region in expected_regions:
            assert region in ml_service.encoder.classes_
