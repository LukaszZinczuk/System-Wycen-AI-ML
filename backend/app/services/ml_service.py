import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import joblib
import os

MODEL_PATH = "model.pkl"
ENCODER_PATH = "encoder.pkl"

class MLService:
    def __init__(self):
        self.model = None
        self.encoder = None
        self._load_or_train_model()

    def _load_or_train_model(self):
        if os.path.exists(MODEL_PATH) and os.path.exists(ENCODER_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                self.encoder = joblib.load(ENCODER_PATH)
                print("ML Model loaded successfully.")
            except Exception as e:
                print(f"Error loading model: {e}. Retraining...")
                self._train_model()
        else:
            print("Model not found. Training new model...")
            self._train_model()

    def _train_model(self):
        # 1. Generate Synthetic Dataset (1000 records)
        np.random.seed(42)
        n_samples = 1000
        
        regions = ['Mazowieckie', 'Slaskie', 'Malopolskie', 'Inne']
        
        df = pd.DataFrame({
            'employees_count': np.random.randint(1, 500, n_samples),
            'region': np.random.choice(regions, n_samples),
            'premium': np.random.choice([0, 1], n_samples),
            'avg_order_value': np.random.randint(1000, 50000, n_samples),
            'offers_count': np.random.randint(0, 10, n_samples),
            'industry_risk_factor': np.random.uniform(0, 1, n_samples)
        })

        # Logic for target (profitability score 0-100)
        # More employees -> higher score (bulk)
        # Premium -> higher score
        # High avg value -> higher score
        # High risk -> lower score
        
        score = (
            (df['employees_count'] / 500 * 30) +
            (df['premium'] * 10) + 
            (df['avg_order_value'] / 50000 * 40) +
            (df['offers_count'] * 2) - 
            (df['industry_risk_factor'] * 20) +
            np.random.normal(0, 5, n_samples) # noise
        )
        
        # Normalize to 0-100
        score = np.clip(score, 0, 100)
        df['target'] = score

        # 2. Preprocessing
        le = LabelEncoder()
        df['region_encoded'] = le.fit_transform(df['region'])
        
        X = df[['employees_count', 'region_encoded', 'premium', 'avg_order_value', 'offers_count', 'industry_risk_factor']]
        y = df['target']

        # 3. Train
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model.fit(X, y)
        self.encoder = le

        # 4. Save
        joblib.dump(self.model, MODEL_PATH)
        joblib.dump(self.encoder, ENCODER_PATH)
        print("Model trained and saved.")

    def predict(self, employees_count, region, premium, avg_order_value, offers_count, industry_risk_factor):
        if not self.model:
            return 50.0 # Fallback default
        
        try:
            # Handle unknown regions safely
            if region in self.encoder.classes_:
                region_encoded = self.encoder.transform([region])[0]
            else:
                region_encoded = 0 # Default to first class if unknown
                
            features = pd.DataFrame([[
                employees_count, 
                region_encoded, 
                int(premium), 
                avg_order_value, 
                offers_count, 
                industry_risk_factor
            ]], columns=['employees_count', 'region_encoded', 'premium', 'avg_order_value', 'offers_count', 'industry_risk_factor'])
            
            prediction = self.model.predict(features)[0]
            return float(prediction)
        except Exception as e:
            print(f"Prediction error: {e}")
            return 50.0 # Fallback

ml_service = MLService()
