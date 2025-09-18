import os
from flask import Flask
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

    # Ensure publish root exists
    os.makedirs(app.config['PUBLISHED_ROOT'], exist_ok=True)

    from .db import init_db
    init_db(app)

    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app
