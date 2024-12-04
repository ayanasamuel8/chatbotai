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


# Initialize the database and migrate
db = SQLAlchemy()
migrate = Migrate()
load_dotenv()

DB_NAME = 'database.db'

# Initialize OAuth
oauth = OAuth()
socketio=SocketIO()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] =os.getenv('SECRET_KEY')   # Replace with a strong secret key
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Optional but recommended
    app.config["REDIS_URL"] = "redis://localhost:6379/0" # Redis is required for SSE app.register_blueprint(sse, url_prefix='/stream'

    # Initialize the extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    oauth.init_app(app)  # Initialize OAuth
    socketio.init_app(app)  # Initialize SocketIO

    # Google OAuth configuration within create_app
    oauth.register(
        name='google',
        client_id=os.getenv('CLIENT_ID'),
        client_secret=os.getenv('CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )
    app.register_blueprint(sse, url_prefix='/stream')

    # Import and register Blueprints
    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # Create the database if it doesn't exist (Only if necessary, use Flask-Migrate for migrations)
    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    # Use a function to load the user to prevent circular imports
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User  # Import inside function to avoid circular import
        return User.query.get(int(user_id))

    return app

def create_database(app):
    # Check if the database exists before creating it (only for initial setup)
    if not path.exists('chatbot/' + DB_NAME):
        with app.app_context():
            db.create_all()  # Create tables if they don't exist yet
