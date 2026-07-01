"""
Debeties Analysis V2 - ML Engine
Handles model loading, predictions, and training
Preserves all original logic from train_model.py and app.py
"""
import os
import json
import pickle
import warnings
import numpy as np
import pandas as pd
from config import Config

warnings.filterwarnings('ignore')

# Lazy imports for training (only when needed)
def _get_train_imports():
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.svm import SVC
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.naive_bayes import GaussianNB
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    return locals()


class MLEngine:
    def __init__(self):
        self.models = {}
        self.scaler = None
        self.feature_names = []
        self.results = {}
        self.best_info = {}
        self.loaded = False
        self.error = None
        self._load_all()

    def _load_all(self):
        """Load all trained models and metadata."""
        try:
            model_files = {
                'Logistic Regression': 'Logistic_Regression.pkl',
                'Random Forest': 'Random_Forest.pkl',
                'Support Vector Machine': 'Support_Vector_Machine.pkl',
                'K-Nearest Neighbors': 'K_Nearest_Neighbors.pkl',
                'Decision Tree': 'Decision_Tree.pkl',
                'Gradient Boosting': 'Gradient_Boosting.pkl',
                'Naive Bayes': 'Naive_Bayes.pkl'
            }

            for name, filename in model_files.items():
                filepath = os.path.join(Config.MODELS_DIR, filename)
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        self.models[name] = pickle.load(f)

            scaler_path = os.path.join(Config.MODELS_DIR, 'scaler.pkl')
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)

            feature_path = os.path.join(Config.MODELS_DIR, 'feature_names.json')
            with open(feature_path, 'r') as f:
                self.feature_names = json.load(f)

            results_path = os.path.join(Config.MODELS_DIR, 'model_results.json')
            with open(results_path, 'r') as f:
                self.results = json.load(f)

            best_path = os.path.join(Config.MODELS_DIR, 'best_model.json')
            with open(best_path, 'r') as f:
                self.best_info = json.load(f)

            self.loaded = True
            print(f"[ML Engine] Loaded {len(self.models)} models. Best: {self.best_info.get('best_model', 'N/A')}")
        except Exception as e:
            self.error = str(e)
            print(f"[ML Engine] Error loading models: {e}")

    def is_ready(self):
        return self.loaded and len(self.models) > 0

    def predict(self, input_data):
        """
        Make predictions using all models.
        input_data: dict with keys matching feature_names
        Returns: (predictions dict, probabilities dict)
        """
        if not self.is_ready():
            raise RuntimeError("Models not loaded properly")

        df_input = pd.DataFrame([input_data], columns=self.feature_names)
        scaled_input = self.scaler.transform(df_input)

        predictions = {}
        probabilities = {}

        for name, model in self.models.items():
            pred = model.predict(scaled_input)[0]
            prob = model.predict_proba(scaled_input)[0]
            predictions[name] = int(pred)
            probabilities[name] = float(prob[1])

        return predictions, probabilities

    def get_ensemble_result(self, predictions, probabilities):
        """Calculate ensemble prediction from all models."""
        avg_prob = np.mean(list(probabilities.values()))
        ensemble_pred = 1 if avg_prob > 0.5 else 0
        return ensemble_pred, avg_prob

    def get_risk_level(self, probability):
        """Determine risk level based on probability."""
        if probability < 0.3:
            return "Low Risk", "#22c55e"
        elif probability < 0.6:
            return "Moderate Risk", "#eab308"
        elif probability < 0.8:
            return "High Risk", "#f97316"
        else:
            return "Very High Risk", "#ef4444"

    def get_model_results_table(self):
        """Return model results as list of dicts for templates."""
        table = []
        for name, metrics in self.results.items():
            row = {'name': name}
            row.update(metrics)
            row['is_best'] = (name == self.best_info.get('best_model', ''))
            table.append(row)
        # Sort by F1-Score descending
        table.sort(key=lambda x: x.get('F1-Score', 0), reverse=True)
        return table

    def get_feature_stats(self):
        """Get dataset statistics for the dashboard."""
        if not os.path.exists(Config.DATA_PATH):
            return None

        df = pd.read_csv(Config.DATA_PATH)
        stats = {
            'total_samples': len(df),
            'features': len(df.columns) - 1,
            'diabetic_cases': int(df['Outcome'].sum()),
            'non_diabetic_cases': len(df) - int(df['Outcome'].sum()),
            'diabetic_pct': round(int(df['Outcome'].sum()) / len(df) * 100, 1),
            'columns': list(df.columns[:-1]),
            'correlation': df.corr()['Outcome'].drop('Outcome').to_dict()
        }
        return stats

    def get_correlation_data(self):
        """Get correlation matrix data for charts."""
        if not os.path.exists(Config.DATA_PATH):
            return None
        df = pd.read_csv(Config.DATA_PATH)
        corr = df.corr()
        return {
            'labels': list(corr.columns),
            'values': corr.values.tolist()
        }

    def get_feature_distribution(self, feature_name):
        """Get distribution data for a feature."""
        if not os.path.exists(Config.DATA_PATH):
            return None
        df = pd.read_csv(Config.DATA_PATH)
        if feature_name not in df.columns:
            return None

        data = df[feature_name].tolist()
        diabetic = df[df['Outcome'] == 1][feature_name].tolist()
        non_diabetic = df[df['Outcome'] == 0][feature_name].tolist()

        return {
            'all': data,
            'diabetic': diabetic,
            'non_diabetic': non_diabetic,
            'bins': 20
        }

    def train_from_upload(self, file_path):
        """Train models from uploaded CSV. Returns (success, message, best_model_name)."""
        try:
            imports = _get_train_imports()
            df = pd.read_csv(file_path)
            required_cols = ['Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness',
                           'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age', 'Outcome']
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                return False, f"Missing required columns: {missing}", None

            # Save the uploaded file
            df.to_csv(Config.DATA_PATH, index=False)

            # Preprocess
            X = df.drop('Outcome', axis=1)
            y = df['Outcome']
            X_train, X_test, y_train, y_test = imports['train_test_split'](
                X, y, test_size=0.2, random_state=42, stratify=y
            )

            scaler = imports['StandardScaler']()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # Define models
            models = {
                'Logistic Regression': imports['LogisticRegression'](max_iter=1000, random_state=42),
                'Random Forest': imports['RandomForestClassifier'](n_estimators=200, max_depth=10, random_state=42),
                'Support Vector Machine': imports['SVC'](probability=True, random_state=42),
                'K-Nearest Neighbors': imports['KNeighborsClassifier'](n_neighbors=5),
                'Decision Tree': imports['DecisionTreeClassifier'](max_depth=8, random_state=42),
                'Gradient Boosting': imports['GradientBoostingClassifier'](n_estimators=150, random_state=42),
                'Naive Bayes': imports['GaussianNB']()
            }

            results = {}
            trained_models = {}

            for name, model in models.items():
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
                y_prob = model.predict_proba(X_test_scaled)[:, 1]

                cv_scores = imports['cross_val_score'](model, X_train_scaled, y_train, cv=5, scoring='accuracy')

                results[name] = {
                    'Accuracy': round(float(imports['accuracy_score'](y_test, y_pred)), 4),
                    'Precision': round(float(imports['precision_score'](y_test, y_pred, zero_division=0)), 4),
                    'Recall': round(float(imports['recall_score'](y_test, y_pred, zero_division=0)), 4),
                    'F1-Score': round(float(imports['f1_score'](y_test, y_pred, zero_division=0)), 4),
                    'AUC-ROC': round(float(imports['roc_auc_score'](y_test, y_prob)), 4),
                    'CV Mean': round(float(cv_scores.mean()), 4),
                    'CV Std': round(float(cv_scores.std()), 4)
                }
                trained_models[name] = model

            # Save all models
            for name, model in trained_models.items():
                safe_name = name.replace(' ', '_').replace('-', '_')
                filepath = os.path.join(Config.MODELS_DIR, f"{safe_name}.pkl")
                with open(filepath, 'wb') as f:
                    pickle.dump(model, f)

            with open(os.path.join(Config.MODELS_DIR, 'scaler.pkl'), 'wb') as f:
                pickle.dump(scaler, f)

            with open(os.path.join(Config.MODELS_DIR, 'feature_names.json'), 'w') as f:
                json.dump(list(X.columns), f)

            with open(os.path.join(Config.MODELS_DIR, 'model_results.json'), 'w') as f:
                json.dump(results, f, indent=4)

            best_model_name = max(results, key=lambda x: results[x]['F1-Score'])
            best_info = {
                'best_model': best_model_name,
                'metrics': results[best_model_name],
                'all_results': results
            }
            with open(os.path.join(Config.MODELS_DIR, 'best_model.json'), 'w') as f:
                json.dump(best_info, f, indent=4)

            # Reload
            self._load_all()

            return True, f"Training complete! Best Model: {best_model_name}", best_model_name

        except Exception as e:
            return False, f"Training failed: {str(e)}", None


# Global instance
ml_engine = MLEngine()
