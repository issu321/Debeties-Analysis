#!/usr/bin/env python3
"""
Debeties Analysis V2 - Standalone Model Training Script
Can be run independently: python train_model.py
"""
import os
import sys
import json
import pickle
import warnings
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'diabetes.csv')
MODELS_DIR = os.path.join(BASE_DIR, 'models')


def load_data(data_path=None):
    path = data_path if data_path else DATA_PATH
    if not os.path.exists(path):
        print(f"[ERROR] Dataset not found at {path}")
        sys.exit(1)
    df = pd.read_csv(path)
    print(f"[INFO] Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"[INFO] Class Distribution:\n{df['Outcome'].value_counts()}")
    return df


def preprocess_data(df):
    X = df.drop('Outcome', axis=1)
    y = df['Outcome']
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    print(f"[INFO] Training set: {X_train.shape[0]} samples")
    print(f"[INFO] Testing set: {X_test.shape[0]} samples")
    return X_train_scaled, X_test_scaled, y_train, y_test, scaler, list(X.columns)


def get_models():
    return {
        'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
        'Random Forest': RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42),
        'Support Vector Machine': SVC(probability=True, random_state=42),
        'K-Nearest Neighbors': KNeighborsClassifier(n_neighbors=5),
        'Decision Tree': DecisionTreeClassifier(max_depth=8, random_state=42),
        'Gradient Boosting': GradientBoostingClassifier(n_estimators=150, random_state=42),
        'Naive Bayes': GaussianNB()
    }


def train_models(X_train, X_test, y_train, y_test):
    models = get_models()
    results = {}
    trained_models = {}
    print("\n" + "="*60)
    print("MODEL TRAINING & EVALUATION")
    print("="*60)
    for name, model in models.items():
        print(f"\n[TRAINING] {name}...")
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        auc = roc_auc_score(y_test, y_prob)
        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
        results[name] = {
            'Accuracy': round(float(acc), 4),
            'Precision': round(float(prec), 4),
            'Recall': round(float(rec), 4),
            'F1-Score': round(float(f1), 4),
            'AUC-ROC': round(float(auc), 4),
            'CV Mean': round(float(cv_scores.mean()), 4),
            'CV Std': round(float(cv_scores.std()), 4)
        }
        trained_models[name] = model
        print(f"  Accuracy:  {acc:.4f}")
        print(f"  F1-Score:  {f1:.4f}")
        print(f"  AUC-ROC:   {auc:.4f}")
    return trained_models, results


def save_models(trained_models, scaler, feature_names, results, models_dir=None):
    mdir = models_dir if models_dir else MODELS_DIR
    os.makedirs(mdir, exist_ok=True)
    for name, model in trained_models.items():
        safe_name = name.replace(' ', '_').replace('-', '_')
        filepath = os.path.join(mdir, f"{safe_name}.pkl")
        with open(filepath, 'wb') as f:
            pickle.dump(model, f)
        print(f"[SAVED] {name} -> {filepath}")
    with open(os.path.join(mdir, "scaler.pkl"), 'wb') as f:
        pickle.dump(scaler, f)
    with open(os.path.join(mdir, "feature_names.json"), 'w') as f:
        json.dump(feature_names, f)
    with open(os.path.join(mdir, "model_results.json"), 'w') as f:
        json.dump(results, f, indent=4)
    best_model_name = max(results, key=lambda x: results[x]['F1-Score'])
    best_info = {
        'best_model': best_model_name,
        'metrics': results[best_model_name],
        'all_results': results
    }
    with open(os.path.join(mdir, "best_model.json"), 'w') as f:
        json.dump(best_info, f, indent=4)
    print(f"[SAVED] Best Model Info -> {os.path.join(mdir, 'best_model.json')}")
    return best_model_name


def print_summary(results, best_model_name):
    print("\n" + "="*80)
    print("FINAL RESULTS SUMMARY")
    print("="*80)
    print(f"{'Model':<25} {'Accuracy':<10} {'Precision':<10} {'Recall':<10} {'F1':<10} {'AUC':<10}")
    print("-"*80)
    for name, metrics in results.items():
        marker = " ★ BEST" if name == best_model_name else ""
        print(f"{name:<25} {metrics['Accuracy']:<10.4f} {metrics['Precision']:<10.4f} "
              f"{metrics['Recall']:<10.4f} {metrics['F1-Score']:<10.4f} {metrics['AUC-ROC']:<10.4f}{marker}")
    print("="*80)
    print(f"\n🏆 BEST MODEL: {best_model_name}")
    print(f"   F1-Score: {results[best_model_name]['F1-Score']:.4f}")
    print("\n✅ Training completed successfully!")


def main():
    print("="*80)
    print("  DIABETES PREDICTION USING DATA MINING - V2")
    print("="*80)
    df = load_data()
    X_train, X_test, y_train, y_test, scaler, feature_names = preprocess_data(df)
    trained_models, results = train_models(X_train, X_test, y_train, y_test)
    best_model_name = save_models(trained_models, scaler, feature_names, results)
    print_summary(results, best_model_name)


if __name__ == "__main__":
    main()
