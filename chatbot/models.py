from datetime import datetime
from chatbot import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class User(UserMixin, db.Model):
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
    __tablename__ = 'recent_chats'

    recent_id = db.Column(db.Integer, primary_key=True)
    recent_time = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title=db.Column(db.String(20),nullable=False)

    # Relationship to User
    user = db.relationship('User', back_populates='recent_chats')

    # Relationship to ChatMessages
    messages = db.relationship('ChatMessages', backref='recent_chat', lazy=True)


class ChatMessages(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    recent_id = db.Column(db.Integer, db.ForeignKey('recent_chats.recent_id'), nullable=False)
    sender = db.Column(db.String(50), nullable=False)  # 'user' or 'ai'
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
class OAuth(db.Model):
    __tablename__ = 'oauth'
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), nullable=False)
    provider_user_id = db.Column(db.String(255), unique=True, nullable=False)
    token = db.Column(db.JSON, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', back_populates='oauth_tokens')

