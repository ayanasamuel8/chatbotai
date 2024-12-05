from flask import Blueprint, flash, redirect, render_template, request, jsonify, session, url_for
import google.generativeai as genai
from datetime import datetime
from chatbot.models import RecentChats, ChatMessages, User  # Models for managing chat and user data
from chatbot import db
from dotenv import load_dotenv
import os
from flask_login import login_required, current_user

# Load environment variables from .env file
load_dotenv()

# Configure API key for the Generative AI library
api_key = os.getenv('API_KEY')
genai.configure(api_key=api_key)

# Blueprint for views
views = Blueprint('views', __name__)

@views.route('/')
def welcome():
    """Renders the welcome page."""
    return render_template('welcome.html')

@views.route('/about')
def about():
    """Renders the about page."""
    return render_template('about.html')

@views.route('/contact', methods=['GET', 'POST'])
def contact():
    """Handles the contact form submission."""
    if request.method == 'POST':
        try:
            # Retrieve form data
            name = request.form['name']
            email = request.form['email']
            message = request.form['message']
            
            # Optionally process the data (e.g., save to DB or send an email)
            
            # Flash a success message
            flash('Thanks for your message!', 'success')
            
            # Redirect to the welcome page
            return redirect(url_for('views.welcome'))
        except Exception as e:
            # Handle errors in form submission
            flash(f"Error occurred: {str(e)}", 'error')
            return redirect(url_for('views.contact'))
    return render_template('contact.html')

@views.route('/chat', methods=['GET'])
@login_required
def home():
    """Renders the chat page with recent chats for the logged-in user."""
    try:
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            recent_chats = RecentChats.query.filter_by(user_id=user.id).all()
            return render_template('form.html', recent_chats=recent_chats)
        else:
            return redirect(url_for('auth.login'))  # Redirect to login if not authenticated
    except Exception as e:
        # Handle errors during fetching recent chats
        flash(f"Error occurred while loading chats: {str(e)}", 'error')
        return redirect(url_for('views.welcome'))

@views.route('/save/title', methods=['POST'])
def saved():
    """Updates the title of a recent chat."""
    try:
        received = request.get_json()
        chat_title = received.get('chat_title')
        recent_id = received.get('recent_id')

        if chat_title and recent_id:
            # Retrieve the recent chat and update its title
            recent_chat = RecentChats.query.filter_by(recent_id=recent_id).first()
            if recent_chat:
                recent_chat.title = chat_title
                db.session.commit()
                return jsonify({"success": True, "chat_title": chat_title})
            else:
                return jsonify({"success": False, "message": "Chat not found"}), 404
        else:
            return jsonify({"success": False, "message": "Missing chat title or recent_id"}), 400
    except Exception as e:
        # Handle any errors during title saving
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@views.route('/chat', methods=['POST'])
def chat():
    """Handles user chat by saving the message and generating an AI response."""
    try:
        access_token = request.get_json()
        message = access_token.get('message')
        recent_id = access_token.get('recent_id')

        if message and recent_id:
            # Save user message to the database
            new_message = ChatMessages(recent_id=recent_id, sender='user', message=message, timestamp=datetime.now())
            db.session.add(new_message)
            db.session.commit()

            # Generate AI response using Google AI model
            ai_reply = chat_with_google_ai(message)

            # Save AI response to the database
            new_message = ChatMessages(recent_id=recent_id, sender='ai', message=ai_reply, timestamp=datetime.now())
            db.session.add(new_message)
            db.session.commit()

            # Fetch updated chat history
            messages = ChatMessages.query.filter_by(recent_id=recent_id).order_by(ChatMessages.timestamp.asc()).all()
            chat_history = [{"sender": msg.sender, "message": msg.message} for msg in messages]

            return jsonify({"response": ai_reply, "chat_history": chat_history})
        else:
            return jsonify({"success": False, "message": "Invalid message or recent_id"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@views.route('/api/new_recent', methods=['POST'])
def create_new_chat():
    """Creates a new chat and stores it in the database."""
    try:
        title = request.json.get('title', 'New Chat')  # Default to "New Chat" if no title is provided
        user_id = session.get('user_id')

        if not user_id:
            return jsonify({"success": False, "error": "User not logged in"}), 401

        new_recent = RecentChats(user_id=user_id, recent_time=datetime.now(), title=title)
        db.session.add(new_recent)
        db.session.commit()
        return jsonify({"success": True, "recent_id": new_recent.recent_id}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@views.route('/api/load_chat/<int:recent_id>', methods=['GET'])
def load_chat(recent_id):
    """Loads the chat history for a given recent_id."""
    try:
        # Retrieve all messages for the given recent_id
        messages = ChatMessages.query.filter_by(recent_id=recent_id).order_by(ChatMessages.timestamp.asc()).all()
        chat_history = [{"sender": msg.sender, "message": msg.message} for msg in messages]

        return jsonify({"chat_history": chat_history})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def chat_with_google_ai(message):
    """Generates an AI response using Google Generative AI model."""
    try:
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        response = model.generate_content(message)
        return response.text
    except Exception as e:
        return f"Error generating AI response: {str(e)}"

@views.route("/generate/title", methods=["POST"])
def generate_title():
    """Generates a concise title for the conversation based on the AI response."""
    try:
        data = request.json
        ai_response = data.get("response", "")

        if not ai_response:
            return jsonify({"success": False, "title": None})

        # Prepare the prompt for title generation
        prompt = (
        f"Generate a concise title of at most 20 characters and just single sentence just the title no other thing for the following conversation response if its not greeting or error message or asking for clarification else just return 'error' no anything else :\n\n"
        f"Response: {ai_response}\n\n"
    )

        generated_response = chat_with_google_ai(prompt)
        title = generated_response.strip()

        # Validate the title length
        if len(title) <= 20 and title.lower() != 'error':
            return jsonify({"success": True, "title": title})
        else:
            return jsonify({"success": False, "title": None})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@views.route('/api/delete_chat/<recent_id>', methods=['DELETE'])
def delete_chat(recent_id):
    """Deletes the specified chat and its messages from the database."""
    try:
        # Delete all chat messages related to the given recent_id
        chat_messages = ChatMessages.query.filter_by(recent_id=recent_id).all()
        for chat_message in chat_messages:
            db.session.delete(chat_message)
        
        # Delete the recent chat record
        recent_chat = RecentChats.query.filter_by(recent_id=recent_id).first()
        db.session.delete(recent_chat)
        db.session.commit()

        return jsonify({"success": True, "message": "Successfully Deleted"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500