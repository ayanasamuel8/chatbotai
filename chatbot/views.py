from flask import Blueprint, flash, redirect, render_template, request, jsonify, session, url_for
import openai
from datetime import datetime
import google.generativeai as genai
from chatbot.models import RecentChats, ChatMessages, User  # Assuming you have a ChatMessages model
from chatbot import db
from dotenv import load_dotenv
import os
from flask_login import login_required,current_user

# Load environment variables from .env file
load_dotenv()

# Access the API key from the environment
api_key = os.getenv('API_KEY')

# Explicitly configure the API key for the Generative AI library
genai.configure(api_key=api_key)

views = Blueprint('views', __name__)

@views.route('/')
def welcome():
    return render_template('welcome.html')
@views.route('/about')
def about():
    return render_template('about.html')
@views.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Retrieve form data
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        
        # Optionally process the data (e.g., save to DB or send an email)
        
        # Flash a success message
        flash('Thanks for your message!', 'success')
        
        # Redirect to the welcome page
        return redirect(url_for('views.welcome'))
    return render_template('contact.html')


@views.route('/chat', methods=['GET'])
@login_required
def home():
    user_id = session.get('user_id')
    print(user_id)
    if user_id:
        user = User.query.get(user_id)
        recent_chats = RecentChats.query.filter_by(user_id=user.id).all()
        return render_template('form.html', recent_chats=recent_chats)
    return redirect(url_for('auth.login'))  # Redirect to login if not authenticated
@views.route('/save/title', methods=['POST'])
def saved():
    recieved=request.get_json()
    chat_title=recieved.get('chat_title')
    recent_id = recieved.get('recent_id')
    if chat_title and recent_id:
        recent_chat = RecentChats.query.filter_by(recent_id=recent_id).first()
        recent_chat.title = chat_title
        db.session.commit()
        return jsonify({"success": True, "chat_title": chat_title})

@views.route('/chat', methods=['POST'])
def chat():
    access_token = request.get_json()
    message = access_token.get('message')
    recent_id = access_token.get('recent_id')

    if message and recent_id:
        # Save user message
        new_message = ChatMessages(recent_id=recent_id, sender='user', message=message, timestamp=datetime.now())
        db.session.add(new_message)
        db.session.commit()

        # Generate AI response
        ai_reply = chat_with_google_ai(message)

        # Save AI response
        new_message = ChatMessages(recent_id=recent_id, sender='ai', message=ai_reply, timestamp=datetime.now())
        db.session.add(new_message)
        db.session.commit()

        # Fetch the updated chat messages
        messages = ChatMessages.query.filter_by(recent_id=recent_id).order_by(ChatMessages.timestamp.asc()).all()
        chat_history = [{"sender": msg.sender, "message": msg.message} for msg in messages]

        return jsonify({"response": ai_reply, "chat_history": chat_history})
    else:
        flash({"error": "Unknown error please relaod and try agin!"}), 400

@views.route('/api/new_recent', methods=['POST'])
def create_new_chat():
    # Get the title from request arguments or set a default value
    title = request.json.get('title', 'New Chat')  # Default to "New Chat" if title is not provided

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "User not logged in"}), 401

    try:
        new_recent = RecentChats(user_id=user_id, recent_time=datetime.now(), title=title)
        db.session.add(new_recent)
        db.session.commit()
        return jsonify({"success": True, "recent_id": new_recent.recent_id}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@views.route('/api/load_chat/<int:recent_id>', methods=['GET'])
def load_chat(recent_id):
    # Retrieve all messages for the given recent_id
    messages = ChatMessages.query.filter_by(recent_id=recent_id).order_by(ChatMessages.timestamp.asc()).all()
    
    chat_history = [{"sender": msg.sender, "message": msg.message} for msg in messages]
    
    return jsonify({"chat_history": chat_history})

    
def chat_with_google_ai(message):
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    response = model.generate_content(message)
    return response.text

@views.route("/generate/title", methods=["POST"])
def generate_title():
    data = request.json
    ai_response = data.get("response", "")

    if not ai_response:
        return jsonify({"success": False, "title": None})

    # Prepare the prompt for title generation
    prompt = (
        f"Generate a concise title of at most 20 characters and just single sentence just the title no other thing for the following conversation response if its not greeting or error message else just return 'error' no anything else :\n\n"
        f"Response: {ai_response}\n\n"
    )

    try:
        # Use the `chat_with_google_ai` function to generate the title
        generated_response = chat_with_google_ai(prompt)

        # Clean and extract the title
        title = generated_response.strip()

        # Validate the title
        if len(title) <= 20 and title.lower() !='error':
            return jsonify({"success": True, "title": title})
        else:
            return jsonify({"success": False, "title": None})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
