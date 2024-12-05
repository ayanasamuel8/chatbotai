from datetime import datetime
from chatbot import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class User(UserMixin, db.Model):
    """
    User model for managing user information.

    Attributes:
        id (int): Primary key for the user.
        email (str): User's email, must be unique.
        password_hash (str): Hashed password for the user.
        name (str): Name of the user.
        provider (str): OAuth provider (e.g., Google, Facebook).
        provider_id (str): OAuth provider's unique user ID.
        profile_picture (str): URL to the user's profile picture.
        created_at (datetime): Timestamp when the user was created.
        updated_at (datetime): Timestamp of the last user update.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    name = db.Column(db.String(255), nullable=True)
    provider = db.Column(db.String(50), nullable=True)
    provider_id = db.Column(db.String(255), nullable=True)
    profile_picture = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())

    # Relationship to RecentChats
    recent_chats = db.relationship('RecentChats', back_populates='user', lazy=True)
    oauth_tokens = db.relationship('OAuth', back_populates='user', lazy=True)

class RecentChats(db.Model):
    """
    RecentChats model for storing information about the user's recent chats.

    Attributes:
        recent_id (int): Primary key for the chat.
        recent_time (datetime): Timestamp when the chat was started.
        user_id (int): Foreign key referencing the user.
        title (str): Title of the recent chat.
    """
    __tablename__ = 'recent_chats'

    recent_id = db.Column(db.Integer, primary_key=True)
    recent_time = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(20), nullable=False)

    # Relationship to User
    user = db.relationship('User', back_populates='recent_chats')

    # Relationship to ChatMessages
    messages = db.relationship('ChatMessages', backref='recent_chat', lazy=True)

class ChatMessages(db.Model):
    """
    ChatMessages model for storing individual messages within a chat.

    Attributes:
        id (int): Primary key for the message.
        recent_id (int): Foreign key referencing the recent chat.
        sender (str): Sender of the message ('user' or 'ai').
        message (str): The content of the message.
        timestamp (datetime): Timestamp when the message was sent.
    """
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    recent_id = db.Column(db.Integer, db.ForeignKey('recent_chats.recent_id'), nullable=False)
    sender = db.Column(db.String(50), nullable=False)  # 'user' or 'ai'
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class OAuth(db.Model):
    """
    OAuth model for managing OAuth tokens linked to users.

    Attributes:
        id (int): Primary key for the OAuth token.
        provider (str): OAuth provider (e.g., Google).
        provider_user_id (str): Unique ID for the user from the OAuth provider.
        token (dict): OAuth token data.
        user_id (int): Foreign key referencing the user.
    """
    __tablename__ = 'oauth'

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), nullable=False)
    provider_user_id = db.Column(db.String(255), unique=True, nullable=False)
    token = db.Column(db.JSON, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', back_populates='oauth_tokens')
