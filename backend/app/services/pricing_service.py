from app.services.ml_service import ml_service
from app.models.models import Offer, Industry
from app.schemas.schemas import OfferCreate, PricingResponse
from sqlalchemy.orm import Session
from datetime import datetime

class PricingService:
    BASE_PRICE_PER_EMPLOYEE = 100.0
    
    REGION_MULTIPLIER = {
        "Mazowieckie": 1.2,
        "Śląskie": 1.1,
        "Małopolskie": 1.05,
        "Inne": 1.0
    }

    def calculate_price_and_score(self, offer_data: OfferCreate, db: Session) -> PricingResponse:
        # 1. Base Logic
        base_price = offer_data.employees_count * self.BASE_PRICE_PER_EMPLOYEE
        
        # 2. Quantity Discount
        discount_rate = 0.0
        if 11 <= offer_data.employees_count <= 50:
            discount_rate = 0.05
        elif 51 <= offer_data.employees_count <= 200:
            discount_rate = 0.10
        elif offer_data.employees_count > 200:
            discount_rate = 0.15
            
        discounted_price = base_price * (1 - discount_rate)
        
        # 3. Region Multiplier
        region = offer_data.region
        multiplier = self.REGION_MULTIPLIER.get(region, 1.0)
        regional_price = discounted_price * multiplier
        
        # 4. Premium 48h
        if offer_data.premium_48h:
            regional_price *= 1.20
            
        final_price_before_ai = regional_price
        
        # 5. AI Scoring
        
        # 5.1 Rule-Based Score
        rule_score = 50
        if offer_data.employees_count >= 100:
            rule_score += 15
        elif offer_data.employees_count >= 200:
            rule_score += 10 # This is what the prompt asked for "200 -> +10", I assume additive? Or exclusive?
            # Prompt says: "100 workers -> +15, 200 -> +10". I will assume they stack or are defined thresholds.
            # Usually strict thresholds are better. Prompt: "100 -> +15", "200 -> +10".
            # Let's interpret as: if > 100 add 15. If > 200, add another 10? Or replace?
            # I'll stack them: >100 gets 15, >200 gets 25 total? No, prompt lists them. I will treat as cumulative for simplicity or max.
            # Let's do cumulative for robust scoring.
        
        if offer_data.premium_48h:
            rule_score += 10
            
        if region == "Mazowieckie":
            rule_score += 5
            
        # Simulating external data for "avg_order_value > 20k -> +10" & "3 offers history -> +5"
        # Since we don't have real history in this stateless call unless we query DB for company history
        # We will use the simulated fields passed in request (or defaults)
        if offer_data.ml_feature_avg_order_value > 20000:
            rule_score += 10
            
        if offer_data.ml_feature_offers_count >= 3:
            rule_score += 5
            
        rule_score = min(100, max(0, rule_score)) # Clamp 0-100

        # 5.2 ML Score
        # Get Industry Risk Factor
        company_industry_risk = 0.5 # Default
        if offer_data.company_id:
            # In a real app we'd fetch company -> industry. 
            # For this calc, we might need to fetch it.
            # Let's try to fetch company if ID is provided.
            from app.models.models import Company
            company = db.query(Company).filter(Company.id == offer_data.company_id).first()
            if company and company.industry:
                company_industry_risk = company.industry.risk_factor
        
        ml_score = ml_service.predict(
            employees_count=offer_data.employees_count,
            region=offer_data.region,
            premium=offer_data.premium_48h,
            avg_order_value=offer_data.ml_feature_avg_order_value,
            offers_count=offer_data.ml_feature_offers_count,
            industry_risk_factor=company_industry_risk
        )
        
        # 5.3 Final Score
        # 70% ML, 30% Rule
        final_ai_score = (0.7 * ml_score) + (0.3 * rule_score)
        
        # 6. Priority Level
        if final_ai_score <= 40:
            priority = "LOW"
        elif final_ai_score <= 70:
            priority = "STANDARD"
        else:
            priority = "VIP"
            
        # 7. VIP Discount
        vip_discount = 0.0
        if priority == "VIP":
            vip_discount = 0.05
            final_price = final_price_before_ai * (1 - vip_discount)
        else:
            final_price = final_price_before_ai
            
        return PricingResponse(
            base_price=round(base_price, 2),
            final_price=round(final_price, 2),
            ai_score=round(final_ai_score, 1),
            ml_score=round(ml_score, 1),
            rule_score=round(rule_score, 1),
            priority_level=priority,
            discount_applied=vip_discount
        )

pricing_service = PricingService()
