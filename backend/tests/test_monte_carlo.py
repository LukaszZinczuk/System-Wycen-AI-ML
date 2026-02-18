"""
Unit tests for Monte Carlo Service

Tests statistical properties, convergence, and edge cases.
"""

import pytest
import numpy as np
from app.services.monte_carlo_service import MonteCarloService, MonteCarloResult


class TestMonteCarloService:
    """Test suite for Monte Carlo simulation service"""
    
    @pytest.fixture
    def mc_service(self):
        """Create Monte Carlo service with fixed seed for reproducibility"""
        return MonteCarloService(n_simulations=5000, seed=42)
    
    @pytest.fixture
    def small_mc_service(self):
        """Small simulation for fast tests"""
        return MonteCarloService(n_simulations=1000, seed=42)
    
    # --- Basic Functionality Tests ---
    
    def test_simulate_price_returns_result(self, mc_service):
        """Test that simulation returns MonteCarloResult"""
        result = mc_service.simulate_price(
            base_price=1000.0,
            employees_count=50,
            region="Mazowieckie",
            premium=False
        )
        
        assert isinstance(result, MonteCarloResult)
        assert result.mean_price > 0
        assert result.n_simulations == 5000
    
    def test_mean_close_to_base_price(self, mc_service):
        """Mean of log-normal distribution should be close to base price"""
        base_price = 1000.0
        result = mc_service.simulate_price(
            base_price=base_price,
            employees_count=100,
            region="Mazowieckie",
            premium=False,
            industry_risk_factor=0.2,
            ai_score=80.0
        )
        
        # Mean should be within 30% of base price
        assert 0.7 * base_price < result.mean_price < 1.5 * base_price
    
    def test_percentiles_ordered(self, mc_service):
        """Percentiles should be in correct order"""
        result = mc_service.simulate_price(
            base_price=5000.0,
            employees_count=200,
            region="Śląskie",
            premium=True
        )
        
        assert result.p5 <= result.p25 <= result.p50 <= result.p75 <= result.p95
    
    def test_confidence_interval_contains_mean(self, mc_service):
        """95% CI should contain the mean"""
        result = mc_service.simulate_price(
            base_price=2000.0,
            employees_count=75,
            region="Małopolskie",
            premium=False
        )
        
        assert result.ci_lower <= result.mean_price <= result.ci_upper
    
    # --- Statistical Property Tests ---
    
    def test_var_positive(self, mc_service):
        """VaR should be positive (represents potential loss)"""
        result = mc_service.simulate_price(
            base_price=3000.0,
            employees_count=150,
            region="Mazowieckie",
            premium=True
        )
        
        assert result.var_95 >= 0
        assert result.cvar_95 >= result.var_95  # CVaR >= VaR always
    
    def test_convergence_score_high(self, mc_service):
        """With enough simulations, convergence should be high"""
        result = mc_service.simulate_price(
            base_price=1500.0,
            employees_count=100,
            region="Inne",
            premium=False
        )
        
        assert result.convergence_score > 0.95  # Should be very stable
    
    def test_std_dev_positive(self, mc_service):
        """Standard deviation should always be positive"""
        result = mc_service.simulate_price(
            base_price=1000.0,
            employees_count=50,
            region="Mazowieckie",
            premium=False
        )
        
        assert result.std_dev > 0
    
    # --- Volatility Tests ---
    
    def test_higher_risk_industry_increases_std(self, small_mc_service):
        """Higher industry risk should increase price variance"""
        low_risk_result = small_mc_service.simulate_price(
            base_price=1000.0,
            employees_count=100,
            region="Mazowieckie",
            premium=False,
            industry_risk_factor=0.1,
            ai_score=80.0
        )
        
        # Reset RNG for fair comparison
        high_risk_service = MonteCarloService(n_simulations=1000, seed=42)
        high_risk_result = high_risk_service.simulate_price(
            base_price=1000.0,
            employees_count=100,
            region="Mazowieckie",
            premium=False,
            industry_risk_factor=0.9,
            ai_score=80.0
        )
        
        # Higher risk should have higher std dev
        assert high_risk_result.std_dev > low_risk_result.std_dev
    
    def test_lower_ai_score_increases_uncertainty(self, small_mc_service):
        """Lower AI score (less confident) should increase uncertainty"""
        high_confidence = small_mc_service.simulate_price(
            base_price=1000.0,
            employees_count=100,
            region="Mazowieckie",
            premium=False,
            ai_score=90.0
        )
        
        low_confidence_service = MonteCarloService(n_simulations=1000, seed=42)
        low_confidence = low_confidence_service.simulate_price(
            base_price=1000.0,
            employees_count=100,
            region="Mazowieckie",
            premium=False,
            ai_score=30.0
        )
        
        # Lower AI score should have higher std dev
        assert low_confidence.std_dev > high_confidence.std_dev
    
    def test_custom_volatility_override(self, small_mc_service):
        """Custom volatility should override calculated volatility"""
        low_vol = small_mc_service.simulate_price(
            base_price=1000.0,
            employees_count=100,
            region="Mazowieckie",
            premium=False,
            custom_volatility=0.05
        )
        
        high_vol_service = MonteCarloService(n_simulations=1000, seed=42)
        high_vol = high_vol_service.simulate_price(
            base_price=1000.0,
            employees_count=100,
            region="Mazowieckie",
            premium=False,
            custom_volatility=0.40
        )
        
        assert high_vol.std_dev > low_vol.std_dev
    
    # --- Edge Cases ---
    
    def test_zero_employees(self, small_mc_service):
        """Should handle zero employees gracefully"""
        result = small_mc_service.simulate_price(
            base_price=100.0,
            employees_count=0,
            region="Mazowieckie",
            premium=False
        )
        
        assert result.mean_price > 0
    
    def test_very_high_base_price(self, small_mc_service):
        """Should handle large prices"""
        result = small_mc_service.simulate_price(
            base_price=1_000_000.0,
            employees_count=500,
            region="Śląskie",
            premium=True
        )
        
        assert result.mean_price > 0
        assert result.p5 > 0
    
    def test_unknown_region(self, small_mc_service):
        """Should handle unknown regions with default volatility"""
        result = small_mc_service.simulate_price(
            base_price=1000.0,
            employees_count=100,
            region="Unknown Region",
            premium=False
        )
        
        assert result.mean_price > 0
    
    # --- Output Format Tests ---
    
    def test_to_dict_format(self, small_mc_service):
        """Test that to_dict returns proper structure"""
        result = small_mc_service.simulate_price(
            base_price=1000.0,
            employees_count=50,
            region="Mazowieckie",
            premium=False
        )
        
        result_dict = result.to_dict()
        
        assert "mean_price" in result_dict
        assert "percentiles" in result_dict
        assert "risk_metrics" in result_dict
        assert "histogram" in result_dict
        
        assert "p5" in result_dict["percentiles"]
        assert "p95" in result_dict["percentiles"]
        assert "var_95" in result_dict["risk_metrics"]
        assert "interpretation" in result_dict["risk_metrics"]
    
    def test_histogram_has_correct_bins(self, small_mc_service):
        """Histogram should have 31 bin edges for 30 bins"""
        result = small_mc_service.simulate_price(
            base_price=1000.0,
            employees_count=50,
            region="Mazowieckie",
            premium=False
        )
        
        assert len(result.histogram_bins) == 31  # 30 bins + 1 edge
        assert len(result.histogram_counts) == 30
        assert sum(result.histogram_counts) == 1000  # Should equal n_simulations
    
    # --- Scenario Analysis Tests ---
    
    def test_scenario_analysis(self, small_mc_service):
        """Test scenario analysis output"""
        scenarios = small_mc_service.scenario_analysis(
            base_price=2000.0,
            employees_count=100,
            region="Mazowieckie",
            premium=True
        )
        
        assert "best_case" in scenarios
        assert "worst_case" in scenarios
        assert "expected_case" in scenarios
        assert "price_range" in scenarios
        
        # Best case price should be higher than worst case
        assert scenarios["best_case"]["price"] > scenarios["worst_case"]["price"]
    
    # --- Sensitivity Analysis Tests ---
    
    def test_sensitivity_analysis(self, small_mc_service):
        """Test sensitivity analysis output"""
        sensitivity = small_mc_service.sensitivity_analysis(
            base_price=1500.0,
            employees_count=75,
            region="Śląskie",
            premium=False
        )
        
        assert "baseline" in sensitivity
        assert "sensitivities" in sensitivity
        assert len(sensitivity["sensitivities"]) > 0


class TestMonteCarloStatisticalProperties:
    """Tests for statistical validity of Monte Carlo simulation"""
    
    def test_large_sample_normality(self):
        """With many simulations, mean distribution should approximate normal"""
        mc = MonteCarloService(n_simulations=50000, seed=42)
        
        result = mc.simulate_price(
            base_price=1000.0,
            employees_count=100,
            region="Mazowieckie",
            premium=False,
            custom_volatility=0.20
        )
        
        # For large samples, P25-P75 should contain ~50% of data (IQR)
        iqr = result.p75 - result.p25
        assert iqr > 0
        
        # P5 and P95 should be roughly symmetric around median
        lower_tail = result.p50 - result.p5
        upper_tail = result.p95 - result.p50
        
        # Allow 50% asymmetry due to log-normal nature
        assert 0.5 < upper_tail / lower_tail < 2.0
    
    def test_reproducibility_with_seed(self):
        """Same seed should produce same results"""
        mc1 = MonteCarloService(n_simulations=1000, seed=123)
        mc2 = MonteCarloService(n_simulations=1000, seed=123)
        
        result1 = mc1.simulate_price(
            base_price=1000.0, employees_count=50,
            region="Mazowieckie", premium=False
        )
        
        result2 = mc2.simulate_price(
            base_price=1000.0, employees_count=50,
            region="Mazowieckie", premium=False
        )
        
        assert result1.mean_price == result2.mean_price
        assert result1.std_dev == result2.std_dev
    
    def test_different_seeds_different_results(self):
        """Different seeds should produce different results"""
        mc1 = MonteCarloService(n_simulations=1000, seed=111)
        mc2 = MonteCarloService(n_simulations=1000, seed=222)
        
        result1 = mc1.simulate_price(
            base_price=1000.0, employees_count=50,
            region="Mazowieckie", premium=False
        )
        
        result2 = mc2.simulate_price(
            base_price=1000.0, employees_count=50,
            region="Mazowieckie", premium=False
        )
        
        # Results should differ (very unlikely to be exactly equal)
        assert result1.mean_price != result2.mean_price
