"""
Monte Carlo Simulation Service for Price Risk Analysis

This service provides statistical analysis of pricing uncertainty using
Monte Carlo simulation methods. It generates probability distributions
for prices and calculates risk metrics like VaR (Value at Risk).

Author: System Wycen AI+ML
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)


@dataclass
class MonteCarloResult:
    """Results from Monte Carlo simulation"""
    # Price distribution
    mean_price: float
    median_price: float
    std_dev: float
    
    # Percentiles
    p5: float   # 5th percentile (pessimistic)
    p25: float  # 25th percentile
    p50: float  # 50th percentile (median)
    p75: float  # 75th percentile
    p95: float  # 95th percentile (optimistic)
    
    # Risk metrics
    var_95: float  # Value at Risk at 95% confidence
    cvar_95: float  # Conditional VaR (Expected Shortfall)
    
    # Confidence interval
    ci_lower: float  # 95% CI lower bound
    ci_upper: float  # 95% CI upper bound
    
    # Simulation metadata
    n_simulations: int
    convergence_score: float  # How stable the simulation is
    
    # Distribution for visualization
    histogram_bins: List[float]
    histogram_counts: List[int]
    
    def to_dict(self) -> Dict:
        return {
            "mean_price": round(self.mean_price, 2),
            "median_price": round(self.median_price, 2),
            "std_dev": round(self.std_dev, 2),
            "percentiles": {
                "p5": round(self.p5, 2),
                "p25": round(self.p25, 2),
                "p50": round(self.p50, 2),
                "p75": round(self.p75, 2),
                "p95": round(self.p95, 2),
            },
            "risk_metrics": {
                "var_95": round(self.var_95, 2),
                "cvar_95": round(self.cvar_95, 2),
                "interpretation": self._get_risk_interpretation()
            },
            "confidence_interval_95": {
                "lower": round(self.ci_lower, 2),
                "upper": round(self.ci_upper, 2)
            },
            "simulation_quality": {
                "n_simulations": self.n_simulations,
                "convergence_score": round(self.convergence_score, 4)
            },
            "histogram": {
                "bins": [round(b, 2) for b in self.histogram_bins],
                "counts": self.histogram_counts
            }
        }
    
    def _get_risk_interpretation(self) -> str:
        """Interpret risk level based on coefficient of variation"""
        cv = self.std_dev / self.mean_price if self.mean_price > 0 else 0
        if cv < 0.1:
            return "LOW_RISK - High pricing confidence"
        elif cv < 0.2:
            return "MODERATE_RISK - Normal pricing variance"
        elif cv < 0.3:
            return "ELEVATED_RISK - Consider price review"
        else:
            return "HIGH_RISK - Significant uncertainty"


class MonteCarloService:
    """
    Monte Carlo simulation service for pricing analysis.
    
    Uses stochastic modeling to estimate price distributions
    under various market conditions and input uncertainties.
    """
    
    # Default simulation parameters
    DEFAULT_SIMULATIONS = 10_000
    DEFAULT_RANDOM_SEED = None  # None for true randomness
    
    # Market uncertainty factors (can be adjusted)
    MARKET_VOLATILITY = 0.15  # 15% market price volatility
    DEMAND_UNCERTAINTY = 0.10  # 10% demand uncertainty
    COST_UNCERTAINTY = 0.08   # 8% cost uncertainty
    
    # Regional risk factors
    REGION_VOLATILITY = {
        "Mazowieckie": 0.12,   # Stable market
        "Śląskie": 0.18,       # Industrial volatility
        "Małopolskie": 0.15,   # Moderate
        "Inne": 0.20           # Higher uncertainty
    }
    
    # Industry risk adjustments
    INDUSTRY_VOLATILITY_MULTIPLIER = 1.5  # High-risk industries have 1.5x volatility
    
    def __init__(self, n_simulations: int = DEFAULT_SIMULATIONS, seed: Optional[int] = None):
        self.n_simulations = n_simulations
        self.rng = np.random.default_rng(seed)
        logger.info(f"MonteCarloService initialized with {n_simulations} simulations")
    
    def simulate_price(
        self,
        base_price: float,
        employees_count: int,
        region: str,
        premium: bool,
        industry_risk_factor: float = 0.5,
        ai_score: float = 50.0,
        custom_volatility: Optional[float] = None
    ) -> MonteCarloResult:
        """
        Run Monte Carlo simulation for price estimation.
        
        Args:
            base_price: The deterministic calculated price
            employees_count: Number of employees (affects volume discount uncertainty)
            region: Geographic region
            premium: Whether premium service is requested
            industry_risk_factor: Risk factor from industry (0-1)
            ai_score: AI-generated score (affects confidence)
            custom_volatility: Override default volatility
            
        Returns:
            MonteCarloResult with full statistical analysis
        """
        logger.info(f"Running Monte Carlo simulation for base_price={base_price}")
        
        # Calculate combined volatility
        volatility = self._calculate_volatility(
            region, industry_risk_factor, ai_score, custom_volatility
        )
        
        # Generate correlated random factors
        simulated_prices = self._run_simulation(
            base_price=base_price,
            employees_count=employees_count,
            premium=premium,
            volatility=volatility
        )
        
        # Calculate statistics
        result = self._calculate_statistics(simulated_prices)
        
        logger.info(f"Simulation complete: mean={result.mean_price:.2f}, std={result.std_dev:.2f}")
        
        return result
    
    def _calculate_volatility(
        self,
        region: str,
        industry_risk_factor: float,
        ai_score: float,
        custom_volatility: Optional[float]
    ) -> float:
        """Calculate combined volatility from multiple factors"""
        
        if custom_volatility is not None:
            return custom_volatility
        
        # Base market volatility
        base_vol = self.MARKET_VOLATILITY
        
        # Add regional volatility
        regional_vol = self.REGION_VOLATILITY.get(region, 0.20)
        
        # Industry risk adjustment
        industry_vol = industry_risk_factor * self.INDUSTRY_VOLATILITY_MULTIPLIER * 0.1
        
        # AI confidence adjustment (lower score = higher uncertainty)
        ai_confidence = ai_score / 100.0
        ai_uncertainty = (1 - ai_confidence) * 0.15
        
        # Combined volatility using square root of sum of squares (assuming independence)
        combined_vol = np.sqrt(
            base_vol**2 + 
            regional_vol**2 + 
            industry_vol**2 + 
            ai_uncertainty**2
        )
        
        # Cap at reasonable levels
        return min(combined_vol, 0.5)
    
    def _run_simulation(
        self,
        base_price: float,
        employees_count: int,
        premium: bool,
        volatility: float
    ) -> np.ndarray:
        """
        Run the core Monte Carlo simulation.
        
        Uses Geometric Brownian Motion (GBM) inspired model
        with multiple uncertainty sources.
        """
        
        # 1. Market uncertainty (log-normal distribution)
        # This models general market price fluctuations
        market_shocks = self.rng.lognormal(
            mean=0, 
            sigma=volatility, 
            size=self.n_simulations
        )
        
        # 2. Demand uncertainty (affects volume pricing)
        # Larger companies have more stable demand
        demand_vol = self.DEMAND_UNCERTAINTY / (1 + np.log1p(employees_count) / 10)
        demand_shocks = self.rng.normal(1.0, demand_vol, self.n_simulations)
        
        # 3. Cost uncertainty (affects base costs)
        cost_shocks = self.rng.normal(1.0, self.COST_UNCERTAINTY, self.n_simulations)
        
        # 4. Premium service uncertainty (if applicable)
        if premium:
            # Premium has tighter margins, less uncertainty
            premium_shocks = self.rng.normal(1.0, 0.03, self.n_simulations)
        else:
            premium_shocks = np.ones(self.n_simulations)
        
        # 5. Rare events (fat tails) - occasional large deviations
        # Use mixture model: 95% normal, 5% stressed conditions
        stress_mask = self.rng.random(self.n_simulations) < 0.05
        stress_multiplier = np.where(
            stress_mask,
            self.rng.uniform(0.7, 1.3, self.n_simulations),
            1.0
        )
        
        # Combine all factors
        simulated_prices = (
            base_price * 
            market_shocks * 
            demand_shocks * 
            cost_shocks * 
            premium_shocks *
            stress_multiplier
        )
        
        # Ensure non-negative prices
        simulated_prices = np.maximum(simulated_prices, base_price * 0.1)
        
        return simulated_prices
    
    def _calculate_statistics(self, prices: np.ndarray) -> MonteCarloResult:
        """Calculate comprehensive statistics from simulated prices"""
        
        # Basic statistics
        mean_price = np.mean(prices)
        median_price = np.median(prices)
        std_dev = np.std(prices)
        
        # Percentiles
        percentiles = np.percentile(prices, [5, 25, 50, 75, 95])
        
        # Value at Risk (VaR) - worst 5% of outcomes
        var_95 = mean_price - percentiles[0]  # Loss from mean to P5
        
        # Conditional VaR (Expected Shortfall) - average of worst 5%
        worst_5_pct = prices[prices <= percentiles[0]]
        cvar_95 = mean_price - np.mean(worst_5_pct) if len(worst_5_pct) > 0 else var_95
        
        # 95% Confidence Interval for the mean
        se = std_dev / np.sqrt(len(prices))
        ci_lower = mean_price - 1.96 * se
        ci_upper = mean_price + 1.96 * se
        
        # Convergence score (stability check)
        # Compare first half vs second half means
        half_n = len(prices) // 2
        first_half_mean = np.mean(prices[:half_n])
        second_half_mean = np.mean(prices[half_n:])
        convergence_score = 1 - abs(first_half_mean - second_half_mean) / mean_price
        
        # Histogram for visualization
        hist_counts, hist_edges = np.histogram(prices, bins=30)
        histogram_bins = list(hist_edges)
        histogram_counts = list(hist_counts)
        
        return MonteCarloResult(
            mean_price=mean_price,
            median_price=median_price,
            std_dev=std_dev,
            p5=percentiles[0],
            p25=percentiles[1],
            p50=percentiles[2],
            p75=percentiles[3],
            p95=percentiles[4],
            var_95=var_95,
            cvar_95=cvar_95,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            n_simulations=len(prices),
            convergence_score=convergence_score,
            histogram_bins=histogram_bins,
            histogram_counts=histogram_counts
        )
    
    def sensitivity_analysis(
        self,
        base_price: float,
        employees_count: int,
        region: str,
        premium: bool,
        industry_risk_factor: float = 0.5,
        ai_score: float = 50.0
    ) -> Dict:
        """
        Perform sensitivity analysis by varying input parameters.
        
        Returns impact of each parameter on price variance.
        """
        
        baseline = self.simulate_price(
            base_price, employees_count, region, premium, 
            industry_risk_factor, ai_score
        )
        
        results = {
            "baseline": baseline.to_dict(),
            "sensitivities": {}
        }
        
        # Test employee count sensitivity (+/- 20%)
        for change in [-0.2, 0.2]:
            new_employees = max(1, int(employees_count * (1 + change)))
            new_base = base_price * (1 + change * 0.8)  # Approximate price scaling
            sim = self.simulate_price(
                new_base, new_employees, region, premium,
                industry_risk_factor, ai_score
            )
            key = f"employees_{'+' if change > 0 else ''}{int(change*100)}%"
            results["sensitivities"][key] = {
                "mean_change": round((sim.mean_price - baseline.mean_price) / baseline.mean_price * 100, 2),
                "std_change": round((sim.std_dev - baseline.std_dev) / baseline.std_dev * 100, 2)
            }
        
        # Test volatility sensitivity
        for vol in [0.1, 0.3]:
            sim = self.simulate_price(
                base_price, employees_count, region, premium,
                industry_risk_factor, ai_score, custom_volatility=vol
            )
            key = f"volatility_{int(vol*100)}%"
            results["sensitivities"][key] = {
                "mean_change": round((sim.mean_price - baseline.mean_price) / baseline.mean_price * 100, 2),
                "std_change": round((sim.std_dev - baseline.std_dev) / baseline.std_dev * 100, 2)
            }
        
        return results
    
    def scenario_analysis(
        self,
        base_price: float,
        employees_count: int,
        region: str,
        premium: bool,
        industry_risk_factor: float = 0.5,
        ai_score: float = 50.0
    ) -> Dict:
        """
        Generate best/worst/expected case scenarios.
        """
        
        simulation = self.simulate_price(
            base_price, employees_count, region, premium,
            industry_risk_factor, ai_score
        )
        
        return {
            "best_case": {
                "price": round(simulation.p95, 2),
                "probability": "5%",
                "description": "Optimistic scenario - favorable market conditions"
            },
            "expected_case": {
                "price": round(simulation.mean_price, 2),
                "probability": "Most likely",
                "description": "Expected outcome based on current parameters"
            },
            "worst_case": {
                "price": round(simulation.p5, 2),
                "probability": "5%",
                "description": "Pessimistic scenario - adverse conditions"
            },
            "price_range": {
                "min": round(simulation.p5, 2),
                "max": round(simulation.p95, 2),
                "spread": round(simulation.p95 - simulation.p5, 2),
                "spread_pct": round((simulation.p95 - simulation.p5) / simulation.mean_price * 100, 1)
            }
        }


# Singleton instance
monte_carlo_service = MonteCarloService()
