import os
from flask import Flask
from app.database import init_db
from app.routes.auth import auth_bp
from app.routes.citizen import citizen_bp
from app.routes.admin import admin_bp
from app.routes.police import police_bp
from app.routes.main import main_bp

def create_app():
    app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
    app.secret_key = os.environ.get('SECRET_KEY', 'passport-india-2025-secure-key-xyz')
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max upload
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(citizen_bp, url_prefix='/citizen')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(police_bp, url_prefix='/police')
    with app.app_context():
        init_db()
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
