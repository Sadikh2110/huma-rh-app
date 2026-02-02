from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from app.config import config
from app.models import db, User
import json

login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()

def create_app(config_name='default'):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config[config_name])
    
    # Initialiser les extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db) 

    return app
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '🔐 Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'error'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Filtre personnalisé pour parser JSON dans les templates
    @app.template_filter('from_json')
    def from_json_filter(value):
        try:
            return json.loads(value) if value else {}
        except:
            return {}
    
    # Enregistrer les blueprints
    from app.routes.auth import auth_bp
    from app.routes.employees import employees_bp
    from app.routes.stats import stats_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(stats_bp)
    
    # Créer les tables et l'admin par défaut
    with app.app_context():
        db.create_all()
        create_default_admin()
    
    return app

def create_default_admin():
    """Crée un admin par défaut si aucun n'existe"""
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@huma-rh.local',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin par défaut créé (admin / admin123)")