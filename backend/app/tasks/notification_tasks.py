"""
Notification-related async tasks.
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_vip_notification(offer_id: int, company_name: str, ai_score: float):
    """
    Send notification when a VIP offer is created.
    In production, this would integrate with email/Slack/Teams.
    
    Args:
        offer_id: The offer ID
        company_name: Company name
        ai_score: The AI score
    
    Returns:
        dict: Notification result
    """
    logger.info(f"VIP Notification: Offer #{offer_id} for {company_name} (Score: {ai_score})")
    
    # In production, implement actual notification logic:
    # - Send email to sales team
    # - Post to Slack channel
    # - Create task in CRM system
    
    notification_payload = {
        "type": "VIP_OFFER",
        "offer_id": offer_id,
        "company_name": company_name,
        "ai_score": ai_score,
        "message": f"New VIP offer created for {company_name} with AI score {ai_score}"
    }
    
    # Simulate sending notification
    logger.info(f"Notification sent: {notification_payload}")
    
    return {
        "status": "sent",
        "payload": notification_payload
    }


@shared_task
def send_daily_report(admin_email: str):
    """
    Send daily report to admin with key metrics.
    
    Args:
        admin_email: Admin email address
    
    Returns:
        dict: Report generation result
    """
    from app.database import SessionLocal
    from app.models.models import Offer, Company
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    logger.info(f"Generating daily report for {admin_email}")
    
    db = SessionLocal()
    
    try:
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        # Gather metrics
        total_offers_today = db.query(Offer).filter(
            func.date(Offer.created_at) == today
        ).count()
        
        total_revenue_today = db.query(func.sum(Offer.final_price)).filter(
            func.date(Offer.created_at) == today
        ).scalar() or 0
        
        vip_offers_today = db.query(Offer).filter(
            func.date(Offer.created_at) == today,
            Offer.priority_level == "VIP"
        ).count()
        
        avg_ai_score = db.query(func.avg(Offer.ai_score)).filter(
            func.date(Offer.created_at) == today
        ).scalar() or 0
        
        report = {
            "date": str(today),
            "total_offers": total_offers_today,
            "total_revenue": float(total_revenue_today),
            "vip_offers": vip_offers_today,
            "average_ai_score": float(avg_ai_score),
            "recipient": admin_email
        }
        
        # In production, send actual email
        logger.info(f"Daily report generated: {report}")
        
        return report
        
    except Exception as e:
        logger.error(f"Failed to generate daily report: {e}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


@shared_task
def send_low_score_alert(offer_id: int, company_id: int, ai_score: float):
    """
    Alert when an offer has unusually low AI score.
    This might indicate a data issue or special case requiring attention.
    
    Args:
        offer_id: The offer ID
        company_id: The company ID
        ai_score: The low AI score
    
    Returns:
        dict: Alert result
    """
    logger.warning(f"Low Score Alert: Offer #{offer_id} for Company #{company_id} has score {ai_score}")
    
    alert_payload = {
        "type": "LOW_SCORE_ALERT",
        "offer_id": offer_id,
        "company_id": company_id,
        "ai_score": ai_score,
        "message": f"Offer #{offer_id} has unusually low AI score ({ai_score}). Please review."
    }
    
    logger.info(f"Alert dispatched: {alert_payload}")
    
    return {
        "status": "alerted",
        "payload": alert_payload
    }


@shared_task
def batch_send_offer_confirmations(offer_ids: list):
    """
    Send batch confirmation emails for multiple offers.
    
    Args:
        offer_ids: List of offer IDs
    
    Returns:
        dict: Batch send results
    """
    from app.database import SessionLocal
    from app.models.models import Offer
    
    logger.info(f"Sending batch confirmations for {len(offer_ids)} offers")
    
    db = SessionLocal()
    results = {"sent": 0, "failed": 0}
    
    try:
        for offer_id in offer_ids:
            offer = db.query(Offer).filter(Offer.id == offer_id).first()
            
            if offer:
                # Simulate sending confirmation
                logger.info(f"Confirmation sent for offer #{offer_id}")
                results["sent"] += 1
            else:
                results["failed"] += 1
        
        return results
        
    except Exception as e:
        logger.error(f"Batch confirmation failed: {e}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()
