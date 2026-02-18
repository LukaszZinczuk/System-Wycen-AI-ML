"""
Pricing-related async tasks.
"""
from celery import shared_task
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_bulk_pricing(self, company_ids: list, offer_params: dict):
    """
    Process pricing calculations for multiple companies in bulk.
    Useful for batch operations and large-scale pricing updates.
    
    Args:
        company_ids: List of company IDs to process
        offer_params: Common offer parameters for all companies
    
    Returns:
        dict: Results of bulk processing
    """
    from app.database import SessionLocal
    from app.services.pricing_service import pricing_service
    from app.schemas.schemas import OfferCreate
    from app.models.models import Offer
    
    logger.info(f"Starting bulk pricing for {len(company_ids)} companies")
    
    db = SessionLocal()
    results = {"success": [], "failed": []}
    
    try:
        for company_id in company_ids:
            try:
                offer_data = OfferCreate(
                    company_id=company_id,
                    **offer_params
                )
                pricing = pricing_service.calculate_price_and_score(offer_data, db)
                
                new_offer = Offer(
                    company_id=company_id,
                    employees_count=offer_params.get("employees_count", 1),
                    region=offer_params.get("region", "Inne"),
                    premium_48h=offer_params.get("premium_48h", False),
                    base_price=pricing.base_price,
                    final_price=pricing.final_price,
                    ai_score=pricing.ai_score,
                    priority_level=pricing.priority_level,
                    ml_score=pricing.ml_score,
                    rule_score=pricing.rule_score
                )
                db.add(new_offer)
                results["success"].append(company_id)
                
            except Exception as e:
                logger.error(f"Failed to process company {company_id}: {e}")
                results["failed"].append({"company_id": company_id, "error": str(e)})
        
        db.commit()
        logger.info(f"Bulk pricing completed: {len(results['success'])} success, {len(results['failed'])} failed")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Bulk pricing task failed: {e}")
        raise self.retry(exc=e)
    finally:
        db.close()
    
    return results


@shared_task
def cleanup_old_offers(days_threshold: int = 365):
    """
    Clean up offers older than specified threshold.
    This is a maintenance task to keep the database clean.
    
    Args:
        days_threshold: Number of days after which offers are considered old
    
    Returns:
        dict: Cleanup statistics
    """
    from app.database import SessionLocal
    from app.models.models import Offer
    
    logger.info(f"Starting cleanup of offers older than {days_threshold} days")
    
    db = SessionLocal()
    cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
    
    try:
        # Count offers to be deleted
        count = db.query(Offer).filter(Offer.created_at < cutoff_date).count()
        
        if count > 0:
            # Archive before deleting (in production, you'd move to archive table)
            db.query(Offer).filter(Offer.created_at < cutoff_date).delete()
            db.commit()
            logger.info(f"Cleaned up {count} old offers")
        else:
            logger.info("No old offers to clean up")
        
        return {"deleted_count": count, "cutoff_date": str(cutoff_date)}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Cleanup task failed: {e}")
        raise
    finally:
        db.close()


@shared_task
def health_check():
    """
    Periodic health check task.
    Verifies database connectivity and other system components.
    
    Returns:
        dict: Health check results
    """
    from app.database import SessionLocal
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "database": False,
        "ml_model": False,
    }
    
    # Check database
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        results["database"] = True
        db.close()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    # Check ML model
    try:
        from app.services.ml_service import ml_service
        if ml_service.model is not None:
            results["ml_model"] = True
    except Exception as e:
        logger.error(f"ML model health check failed: {e}")
    
    logger.info(f"Health check completed: {results}")
    return results


@shared_task(bind=True, max_retries=5)
def async_calculate_offer(self, offer_data: dict):
    """
    Async task for calculating a single offer.
    Useful for high-traffic scenarios where immediate response isn't required.
    
    Args:
        offer_data: Offer data dictionary
    
    Returns:
        dict: Calculated offer result
    """
    from app.database import SessionLocal
    from app.services.pricing_service import pricing_service
    from app.schemas.schemas import OfferCreate
    from app.models.models import Offer
    
    logger.info(f"Processing async offer calculation")
    
    db = SessionLocal()
    
    try:
        offer_create = OfferCreate(**offer_data)
        pricing = pricing_service.calculate_price_and_score(offer_create, db)
        
        new_offer = Offer(
            company_id=offer_data["company_id"],
            employees_count=offer_data["employees_count"],
            region=offer_data["region"],
            premium_48h=offer_data.get("premium_48h", False),
            base_price=pricing.base_price,
            final_price=pricing.final_price,
            ai_score=pricing.ai_score,
            priority_level=pricing.priority_level,
            ml_score=pricing.ml_score,
            rule_score=pricing.rule_score
        )
        db.add(new_offer)
        db.commit()
        db.refresh(new_offer)
        
        logger.info(f"Async offer created: ID={new_offer.id}")
        
        return {
            "offer_id": new_offer.id,
            "final_price": new_offer.final_price,
            "ai_score": new_offer.ai_score,
            "priority_level": new_offer.priority_level
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Async offer calculation failed: {e}")
        raise self.retry(exc=e, countdown=60)
    finally:
        db.close()
