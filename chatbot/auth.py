from flask import Blueprint, flash, redirect, render_template, request, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from chatbot.models import RecentChats, db, User,OAuth
from datetime import datetime
from . import oauth


auth = Blueprint('auth', __name__)
# Flask-Dance Google OAuth setup
google = oauth.google

# Register the blueprint in your main application (e.g., app.py)
@auth.route('/login/google')
def login_google():
    redirect_uri = url_for('auth.google_login', _external=True)
    return google.authorize_redirect(redirect_uri)


@auth.route('/login', methods=['POST', 'GET'])
def login():
    print("came here")
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": 'missing required parameter'}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Login failed! Please Signup first", category='error')
            logout_user()  # Ensure user is logged out if they are not authenticated
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
        elif not user.password_hash:
            flash("Login failed! Please use google Login", category='error')
            logout_user()  # Ensure user is logged out if they are not authenticated
            return jsonify({'success': False, 'error': 'Password is required'}), 400
        elif not user or not check_password_hash(user.password_hash, password):
            flash("Login failed! Please try again", category='error')
            logout_user()  # Ensure user is logged out if they are not authenticated
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

        # Log the user in
        login_user(user)

        # Create new recent chat
        new_recent = RecentChats(user_id=user.id, recent_time=datetime.utcnow(), title="New Chat")
        db.session.add(new_recent)
        db.session.commit()

        # Set session with recent_id
        session['user_id'] = user.id
        flash("Logged in successfully", category="success")

        return jsonify({
            'success': True,
            'message': 'Login successful',
            'recent_id': new_recent.recent_id  # Send recent_id for frontend use
        }), 200
    return render_template('login.html')


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()  # Get JSON data from the body of the request
            email = data.get('email')
            password = data.get('password')
            name = data.get('name')

            # Check if the email already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email already registered', category='error')
                return jsonify({'success': False, 'message': 'Email already registered'}), 400

            # Validate and hash the password
            allowed_domains = ["@gmail.com", "@outlook.com", "@yahoo.com", "@hotmail.com"]
            if not any(email.endswith(domain) for domain in allowed_domains):
                flash("Invalid email domain. Please use a Gmail, Outlook, Yahoo, or Hotmail account", category='error')
                return jsonify({'success': False, 'error': 'Invalid email domain'}), 400
            user = User(email=email, password_hash=generate_password_hash(password), name=name)
            db.session.add(user)
            db.session.commit()
            print("Created new user")

            flash("User created successfully", category="success")
            return jsonify({'success': True, 'message': 'User created successfully'}), 200
        else:
            return jsonify({'success': False, 'message': 'Request must be JSON'}), 400
    return render_template('signup.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", category="success")
    return redirect(url_for('auth.login'))

@auth.route('/login/google/authorized')
def google_login():

    try:
        print("Request Args:", request.args) 
        token = google.authorize_access_token()
        print("Token:",token)
        resp = google.get('https://www.googleapis.com/oauth2/v2/userinfo')
        user_info = resp.json()
        if user_info:
            email = user_info.get("email")
            name = user_info.get("name")
            profile_picture = user_info.get("picture")
            provider_id = user_info.get("id")
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User.query.filter_by(provider="google", provider_id=provider_id).first()

            if not user:
                # If no user found, create a new user
                user = User(
                    email=email,
                    name=name,
                    profile_picture=profile_picture,
                    provider="google",
                    provider_id=provider_id
                )
                db.session.add(user)
                db.session.commit()  # Commit the new user to the database

            # Log the user in
            login_user(user)

            # Create or update the OAuth token association
            oauth = OAuth.query.filter_by(provider="google", provider_user_id=provider_id).first()
            if not oauth:
                oauth = OAuth(
                    provider="google",
                    provider_user_id=provider_id,
                    token= token,
                    user_id=user.id
                )
                db.session.add(oauth)
                db.session.commit()
            new_recent = RecentChats(user_id=user.id, recent_time=datetime.utcnow(), title="New Chat") 
            db.session.add(new_recent)
            db.session.commit()
            session['user_id'] = user.id

            flash("Logged in successfully!")
            return redirect(url_for('auth.handle_google_login',recent_id=new_recent.recent_id))
    except Exception as e: # Print detailed exception 
        print(f"An error occurred: {e}") 
        flash("An error occurred during Google login.","error")
        return redirect(url_for("auth.login"))

@auth.route('/handle_google_login')
def handle_google_login():
    recent_id=request.args.get('recent_id')
    return render_template('handle_google_login.html',recent_id=recent_id)