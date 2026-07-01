"""
Debeties Analysis V2 - Flask Application
Complete upgrade from Streamlit to Flask
Glassmorphism UI | Animated | SQLAlchemy Auth | ML Predictions
"""
import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Prediction
from ml_engine import ml_engine

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==================== CONTEXT PROCESSORS ====================
@app.context_processor
def inject_globals():
    return {
        'brand_name': Config.BRAND_NAME,
        'brand_tagline': Config.BRAND_TAGLINE,
        'brand_author': Config.BRAND_AUTHOR,
        'brand_github': Config.BRAND_GITHUB,
        'brand_portfolio': Config.BRAND_PORTFOLIO,
        'current_year': datetime.now().year
    }


# ==================== AUTH ROUTES ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()

        # Validation
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('register.html')

        if len(username) < 3:
            flash('Username must be at least 3 characters.', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('register.html')

        if email and User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')

        # Create user
        user = User(username=username, email=email or None, full_name=full_name or None)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


# ==================== MAIN PAGES ====================
@app.route('/')
def home():
    stats = ml_engine.get_feature_stats() if ml_engine.is_ready() else None
    return render_template('home.html', stats=stats, ml_ready=ml_engine.is_ready())


@app.route('/features')
def features():
    model_results = ml_engine.get_model_results_table() if ml_engine.is_ready() else []
    best_model = ml_engine.best_info.get('best_model', 'N/A') if ml_engine.is_ready() else 'N/A'
    return render_template('features.html', 
                         model_results=model_results, 
                         best_model=best_model,
                         ml_ready=ml_engine.is_ready())


@app.route('/dashboard')
@login_required
def dashboard():
    if not ml_engine.is_ready():
        flash('Models are not loaded. Please upload a dataset and train models first.', 'warning')
        return redirect(url_for('home'))

    stats = ml_engine.get_feature_stats()
    model_names = list(ml_engine.models.keys())
    best_model = ml_engine.best_info.get('best_model', 'N/A')

    # Get user's recent predictions
    recent_predictions = Prediction.query.filter_by(user_id=current_user.id)        .order_by(Prediction.created_at.desc()).limit(10).all()

    return render_template('dashboard.html',
                         stats=stats,
                         model_names=model_names,
                         best_model=best_model,
                         recent_predictions=recent_predictions,
                         feature_names=ml_engine.feature_names)


@app.route('/profile')
@login_required
def profile():
    predictions = Prediction.query.filter_by(user_id=current_user.id)        .order_by(Prediction.created_at.desc()).all()
    return render_template('profile.html', predictions=predictions)


@app.route('/about')
def about():
    return render_template('about.html')


# ==================== API ENDPOINTS ====================
@app.route('/api/predict', methods=['POST'])
@login_required
def api_predict():
    if not ml_engine.is_ready():
        return jsonify({'success': False, 'error': 'Models not loaded'}), 400

    try:
        data = request.get_json()

        # Extract input values
        input_data = {
            'Pregnancies': float(data.get('pregnancies', 0)),
            'Glucose': float(data.get('glucose', 0)),
            'BloodPressure': float(data.get('blood_pressure', 0)),
            'SkinThickness': float(data.get('skin_thickness', 0)),
            'Insulin': float(data.get('insulin', 0)),
            'BMI': float(data.get('bmi', 0)),
            'DiabetesPedigreeFunction': float(data.get('diabetes_pedigree', 0)),
            'Age': float(data.get('age', 0))
        }

        selected_model = data.get('selected_model', 'All Models (Ensemble)')

        # Make predictions
        predictions, probabilities = ml_engine.predict(input_data)

        # Ensemble result
        ensemble_pred, ensemble_prob = ml_engine.get_ensemble_result(predictions, probabilities)
        risk_level, risk_color = ml_engine.get_risk_level(ensemble_prob)

        # If specific model selected
        if selected_model != 'All Models (Ensemble)' and selected_model in probabilities:
            ensemble_prob = probabilities[selected_model]
            ensemble_pred = predictions[selected_model]
            risk_level, risk_color = ml_engine.get_risk_level(ensemble_prob)

        # Save to database
        pred_record = Prediction(
            user_id=current_user.id,
            pregnancies=input_data['Pregnancies'],
            glucose=input_data['Glucose'],
            blood_pressure=input_data['BloodPressure'],
            skin_thickness=input_data['SkinThickness'],
            insulin=input_data['Insulin'],
            bmi=input_data['BMI'],
            diabetes_pedigree=input_data['DiabetesPedigreeFunction'],
            age=input_data['Age'],
            selected_model=selected_model,
            ensemble_probability=ensemble_prob,
            ensemble_prediction=ensemble_pred,
            risk_level=risk_level,
            model_results=json.dumps(probabilities)
        )
        db.session.add(pred_record)
        db.session.commit()

        # Build response
        model_probs = {name: round(prob * 100, 2) for name, prob in probabilities.items()}
        model_preds = {name: int(pred) for name, pred in predictions.items()}

        return jsonify({
            'success': True,
            'ensemble_prediction': ensemble_pred,
            'ensemble_probability': round(ensemble_prob * 100, 2),
            'risk_level': risk_level,
            'risk_color': risk_color,
            'model_probabilities': model_probs,
            'model_predictions': model_preds,
            'selected_model': selected_model
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/upload-dataset', methods=['POST'])
@login_required
def api_upload_dataset():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if not file.filename.endswith('.csv'):
        return jsonify({'success': False, 'error': 'Only CSV files are allowed'}), 400

    try:
        # Save uploaded file temporarily
        temp_path = os.path.join(Config.MODELS_DIR, 'temp_upload.csv')
        file.save(temp_path)

        # Train models
        success, message, best_model = ml_engine.train_from_upload(temp_path)

        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if success:
            return jsonify({
                'success': True,
                'message': message,
                'best_model': best_model,
                'stats': ml_engine.get_feature_stats()
            })
        else:
            return jsonify({'success': False, 'error': message}), 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/model-results')
@login_required
def api_model_results():
    if not ml_engine.is_ready():
        return jsonify({'success': False, 'error': 'Models not loaded'}), 400
    return jsonify({
        'success': True,
        'results': ml_engine.results,
        'best_model': ml_engine.best_info
    })


@app.route('/api/correlation')
@login_required
def api_correlation():
    data = ml_engine.get_correlation_data()
    if data is None:
        return jsonify({'success': False, 'error': 'No dataset available'}), 400
    return jsonify({'success': True, 'data': data})


@app.route('/api/feature-dist/<feature_name>')
@login_required
def api_feature_dist(feature_name):
    data = ml_engine.get_feature_distribution(feature_name)
    if data is None:
        return jsonify({'success': False, 'error': 'Feature not found'}), 400
    return jsonify({'success': True, 'data': data})


@app.route('/api/delete-account', methods=['POST'])
@login_required
def api_delete_account():
    try:
        user = User.query.get(current_user.id)
        if user:
            db.session.delete(user)
            db.session.commit()
            logout_user()
            return jsonify({'success': True, 'message': 'Account deleted successfully'})
        return jsonify({'success': False, 'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== ERROR HANDLERS ====================
@app.errorhandler(404)
def not_found(e):
    return render_template('home.html'), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500


# ==================== CLI COMMANDS ====================
@app.cli.command('init-db')
def init_db():
    """Initialize the database."""
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")


@app.cli.command('seed-user')
def seed_user():
    """Seed a demo user."""
    with app.app_context():
        if not User.query.filter_by(username='issu321').first():
            user = User(username='issu321', email='jaafreeusman@gmail.com', full_name='Mohammed Usman')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            print("Demo user created: issu321 / password123")
        else:
            print("User issu321 already exists.")


# ==================== MAIN ====================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
