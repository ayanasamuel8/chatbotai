from os import path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
import os
from flask_sse import sse

# Initialize the database, migration, and other extensions
db = SQLAlchemy()
migrate = Migrate()
load_dotenv()

DB_NAME = 'database.db'

# Initialize OAuth for authentication
oauth = OAuth()
socketio = SocketIO()

def create_app():
    """
    Create and configure the Flask app with all necessary extensions.
    """
    app = Flask(__name__)

    # Set configuration variables from environment variables
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  # Secret key for session management
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'  # URI for the SQLite database
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking (optional)
    app.config["REDIS_URL"] = "redis://localhost:6379/0"  # Redis URL for Server-Sent Events (SSE)
    
    # Initialize extensions with the Flask app
    db.init_app(app)
    migrate.init_app(app, db)
    oauth.init_app(app)  # Initialize OAuth for Google authentication
    socketio.init_app(app)  # Initialize SocketIO for real-time communication

    # Register Google OAuth client
    oauth.register(
        name='google',
        client_id=os.getenv('CLIENT_ID'),
        client_secret=os.getenv('CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    # Register Server-Sent Events (SSE) blueprint
    app.register_blueprint(sse, url_prefix='/stream')

    # Import and register Blueprints for views and authentication
    from .views import views
    from .auth import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # Create the database if it doesn't exist
    create_database(app)

    # Set up the login manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'  # Redirect to login if not authenticated
    login_manager.init_app(app)

    # Load user function to prevent circular imports
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User  # Import inside function to avoid circular import
        return User.query.get(int(user_id))

    return app

def create_database(app):
    """
    Create the database if it doesn't exist yet. This is a one-time setup.
    """
    if not path.exists('chatbot/' + DB_NAME):
        with app.app_context():
            db.create_all()  # Create tables for all models if they don't exist yet
