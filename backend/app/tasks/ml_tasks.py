"""
ML-related async tasks.
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def recalculate_all_scores(self):
    """
    Recalculate AI scores for all existing offers.
    This is useful when ML model is updated or rules change.
    
    Returns:
        dict: Recalculation statistics
    """
    from app.database import SessionLocal
    from app.models.models import Offer, Company
    from app.services.ml_service import ml_service
    
    logger.info("Starting recalculation of all AI scores")
    
    db = SessionLocal()
    results = {"updated": 0, "failed": 0}
    
    try:
        offers = db.query(Offer).all()
        
        for offer in offers:
            try:
                # Get company's industry risk factor
                company = db.query(Company).filter(Company.id == offer.company_id).first()
                industry_risk = 0.5
                if company and company.industry:
                    industry_risk = company.industry.risk_factor
                
                # Recalculate ML score
                new_ml_score = ml_service.predict(
                    employees_count=offer.employees_count,
                    region=offer.region,
                    premium=offer.premium_48h,
                    avg_order_value=offer.final_price,  # Use final price as proxy
                    offers_count=1,
                    industry_risk_factor=industry_risk
                )
                
                # Calculate rule score
                rule_score = 50
                if offer.employees_count >= 100:
                    rule_score += 15
                if offer.premium_48h:
                    rule_score += 10
                if offer.region == "Mazowieckie":
                    rule_score += 5
                rule_score = min(100, max(0, rule_score))
                
                # Hybrid score
                new_ai_score = (0.7 * new_ml_score) + (0.3 * rule_score)
                
                # Update priority
                if new_ai_score <= 40:
                    new_priority = "LOW"
                elif new_ai_score <= 70:
                    new_priority = "STANDARD"
                else:
                    new_priority = "VIP"
                
                # Update offer
                offer.ml_score = new_ml_score
                offer.rule_score = rule_score
                offer.ai_score = new_ai_score
                offer.priority_level = new_priority
                
                results["updated"] += 1
                
            except Exception as e:
                logger.error(f"Failed to recalculate offer {offer.id}: {e}")
                results["failed"] += 1
        
        db.commit()
        logger.info(f"Recalculation completed: {results['updated']} updated, {results['failed']} failed")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Recalculation task failed: {e}")
        raise self.retry(exc=e)
    finally:
        db.close()
    
    return results


@shared_task
def retrain_model():
    """
    Retrain the ML model with latest data.
    This should be run periodically or when enough new data is available.
    
    Returns:
        dict: Training results
    """
    from app.services.ml_service import ml_service
    
    logger.info("Starting model retraining")
    
    try:
        # Force retraining
        ml_service._train_model()
        
        logger.info("Model retraining completed successfully")
        return {
            "status": "success",
            "message": "Model retrained successfully"
        }
        
    except Exception as e:
        logger.error(f"Model retraining failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


@shared_task
def evaluate_model_performance():
    """
    Evaluate current model performance metrics.
    
    Returns:
        dict: Performance metrics
    """
    from app.services.ml_service import ml_service
    import numpy as np
    
    logger.info("Evaluating model performance")
    
    try:
        # Generate test predictions
        test_cases = [
            {"employees_count": 50, "region": "Mazowieckie", "premium": True, 
             "avg_order_value": 20000, "offers_count": 5, "industry_risk_factor": 0.3},
            {"employees_count": 200, "region": "Inne", "premium": False,
             "avg_order_value": 10000, "offers_count": 1, "industry_risk_factor": 0.7},
            {"employees_count": 10, "region": "Śląskie", "premium": False,
             "avg_order_value": 5000, "offers_count": 0, "industry_risk_factor": 0.5},
        ]
        
        predictions = []
        for case in test_cases:
            pred = ml_service.predict(**case)
            predictions.append(pred)
        
        return {
            "model_loaded": ml_service.model is not None,
            "encoder_loaded": ml_service.encoder is not None,
            "test_predictions": predictions,
            "prediction_range": [min(predictions), max(predictions)],
            "prediction_mean": np.mean(predictions)
        }
        
    except Exception as e:
        logger.error(f"Model evaluation failed: {e}")
        return {"status": "failed", "error": str(e)}
