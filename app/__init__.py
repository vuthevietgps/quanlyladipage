import os
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    # Explicit template/static folders because templates/ & static/ nằm ngoài package 'app'
    app = Flask(
        __name__,
        template_folder=os.path.join(os.getcwd(), 'templates'),
        static_folder=os.path.join(os.getcwd(), 'static')
    )
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
    app.config['DATABASE'] = os.path.join(os.getcwd(), 'database.db')  # Changed filename
    app.config['PUBLISHED_ROOT'] = os.environ.get('PUBLISHED_ROOT', os.path.join(os.getcwd(), 'published'))
    app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16777216))  # 16MB
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', os.path.join(os.getcwd(), 'uploads'))
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['ADMIN_SECRET_PATH'] = os.environ.get('ADMIN_SECRET_PATH', 'admin-panel-xyz123')
    app.config['WILDCARD_DOMAIN'] = os.environ.get('WILDCARD_DOMAIN', 'localhost:8080')
    
    # Subdomain support (commented out for now)
    # app.config['SERVER_NAME'] = 'localhost:5000'

    # Ensure publish root exists
    os.makedirs(app.config['PUBLISHED_ROOT'], exist_ok=True)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Vui lòng đăng nhập để truy cập trang này.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from .auth import User
        return User.get(user_id)
    
    # Make config available in templates
    @app.context_processor
    def inject_config():
        return {'config': app.config}

    from .db import init_db
    init_db(app)
    
    # Initialize users table
    from .auth import init_users_table
    init_users_table()

    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app
