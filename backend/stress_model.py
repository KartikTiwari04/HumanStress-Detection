import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import json
import os
from typing import Dict, Any

class StressPredictor:
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.feature_names = [
            'typing_speed',
            'key_press_variance',
            'mouse_randomness',
            'click_frequency',
            'backspace_ratio',
            'mouse_speed_variance'
        ]
        self.stress_levels = ['Calm', 'Mild Stress', 'Moderate Stress', 'High Stress', 'Extreme Stress']
        
        # Load or initialize model
        self.load_model()
    
    def train_with_sample_data(self):
        """Train with simulated data for demonstration"""
        # Generate synthetic training data
        np.random.seed(42)
        n_samples = 1000
        
        # Features for different stress levels
        X = []
        y = []
        
        for level in range(5):
            for _ in range(n_samples // 5):
                if level == 0:  # Calm
                    features = [
                        np.random.normal(60, 10),  # typing_speed
                        np.random.normal(0.05, 0.01),  # key_press_variance
                        np.random.normal(0.1, 0.02),  # mouse_randomness
                        np.random.normal(2, 0.5),  # click_frequency
                        np.random.normal(0.02, 0.005),  # backspace_ratio
                        np.random.normal(5, 1)  # mouse_speed_variance
                    ]
                elif level == 1:  # Mild Stress
                    features = [
                        np.random.normal(70, 15),
                        np.random.normal(0.08, 0.02),
                        np.random.normal(0.15, 0.03),
                        np.random.normal(3, 0.8),
                        np.random.normal(0.05, 0.01),
                        np.random.normal(8, 2)
                    ]
                elif level == 2:  # Moderate Stress
                    features = [
                        np.random.normal(85, 20),
                        np.random.normal(0.12, 0.03),
                        np.random.normal(0.25, 0.05),
                        np.random.normal(5, 1.2),
                        np.random.normal(0.1, 0.02),
                        np.random.normal(15, 3)
                    ]
                elif level == 3:  # High Stress
                    features = [
                        np.random.normal(95, 25),
                        np.random.normal(0.2, 0.05),
                        np.random.normal(0.4, 0.08),
                        np.random.normal(8, 2),
                        np.random.normal(0.2, 0.05),
                        np.random.normal(25, 5)
                    ]
                else:  # Extreme Stress
                    features = [
                        np.random.normal(110, 30),
                        np.random.normal(0.3, 0.08),
                        np.random.normal(0.6, 0.12),
                        np.random.normal(12, 3),
                        np.random.normal(0.3, 0.08),
                        np.random.normal(40, 8)
                    ]
                
                X.append(features)
                y.append(level)
        
        X = np.array(X)
        y = np.array(y)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        
        # Save model
        self.save_model()
    
    def predict_stress(self, features: Dict[str, float]) -> Dict[str, Any]:
        # Convert features to array in correct order
        feature_array = np.array([[features.get(f, 0) for f in self.feature_names]])
        
        # Scale features
        feature_array_scaled = self.scaler.transform(feature_array)
        
        # Make prediction
        prediction = self.model.predict(feature_array_scaled)[0]
        probabilities = self.model.predict_proba(feature_array_scaled)[0]
        
        # Get confidence
        confidence = probabilities[prediction]
        
        return {
            'stress_level': self.stress_levels[prediction],
            'level_index': int(prediction),
            'confidence': float(confidence),
            'probabilities': {self.stress_levels[i]: float(prob) 
                            for i, prob in enumerate(probabilities)}
        }
    
    def save_model(self):
        """Save trained model and scaler"""
        os.makedirs('models', exist_ok=True)
        joblib.dump(self.model, 'models/stress_model.pkl')
        joblib.dump(self.scaler, 'models/scaler.pkl')
        
        # Save feature names and stress levels
        with open('models/model_info.json', 'w') as f:
            json.dump({
                'feature_names': self.feature_names,
                'stress_levels': self.stress_levels
            }, f)
    
    def load_model(self):
        """Load trained model and scaler if exists"""
        try:
            self.model = joblib.load('models/stress_model.pkl')
            self.scaler = joblib.load('models/scaler.pkl')
            
            with open('models/model_info.json', 'r') as f:
                info = json.load(f)
                self.feature_names = info['feature_names']
                self.stress_levels = info['stress_levels']
            
            print("Model loaded successfully")
        except:
            print("No trained model found. Training with sample data...")
            self.train_with_sample_data()