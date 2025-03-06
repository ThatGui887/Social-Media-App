import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import or_, text, and_

app = Flask(__name__)

# Get the absolute path for the database file
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'social_media.db')

print(f"Database location: {db_path}")  # This will show us exactly where it's looking for the file

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your-secret-key-here'

db = SQLAlchemy(app)

# Models
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def is_friend(self, user_id):
        return Friend.query.filter(
            ((Friend.user_id == self.id) & (Friend.friend_id == user_id) |
             (Friend.user_id == user_id) & (Friend.friend_id == self.id)) &
            (Friend.status == 'accepted')
        ).first() is not None

    def get_friends(self):
        friends = []
        friendships = Friend.query.filter(
            ((Friend.user_id == self.id) | (Friend.friend_id == self.id)) &
            (Friend.status == 'accepted')
        ).all()
        
        for friendship in friendships:
            friend_id = friendship.friend_id if friendship.user_id == self.id else friendship.user_id
            friend = User.query.get(friend_id)
            if friend:
                friends.append(friend)
        return friends

class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('posts', lazy=True))
    likes = db.relationship('Like', backref='post', lazy=True)
    comments = db.relationship('Comment', backref='post', lazy=True)

    def is_liked_by(self, user_id):
        return any(like.user_id == user_id for like in self.likes)

class Like(db.Model):
    __tablename__ = 'like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure a user can only like a post once
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id'),)

class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('comments', lazy=True))

class Friend(db.Model):
    __tablename__ = 'friend'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Add these relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='friend_requests_sent')
    friend = db.relationship('User', foreign_keys=[friend_id], backref='friend_requests_received')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'friend_id'),)

class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    delivered = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='messages_sent')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='messages_received')

class MessageCache(db.Model):
    __tablename__ = 'message_cache'
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cached_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    message = db.relationship('Message')
    user = db.relationship('User')

    @staticmethod
    def cache_message(message_id, user_id):
        cache = MessageCache(message_id=message_id, user_id=user_id)
        db.session.add(cache)
        db.session.commit()

    @staticmethod
    def clear_cache(user_id):
        old_cache = MessageCache.query.filter_by(user_id=user_id).all()
        for cache in old_cache:
            db.session.delete(cache)
        db.session.commit()

class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'message' or 'friend_request'
    content = db.Column(db.Text, nullable=False)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='notifications_received')
    from_user = db.relationship('User', foreign_keys=[from_user_id])

def init_db():
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Verify tables exist
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        print("Existing tables:", existing_tables)  # Debug print
        
        # Verify Message table structure
        if 'message' in existing_tables:
            columns = inspector.get_columns('message')
            print("Message table columns:", columns)  # Debug print
        
        # Verify MessageCache table structure
        if 'message_cache' in existing_tables:
            columns = inspector.get_columns('message_cache')
            print("MessageCache table columns:", columns)  # Debug print

# Call this when starting the application
init_db()

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    first_name = request.form['first_name']
    last_name = request.form['last_name']

    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash('Email already registered.', 'error')
        return redirect(url_for('index'))

    # Create new user
    hashed_password = generate_password_hash(password)
    new_user = User(
        username=username,
        email=email,
        password=hashed_password,
        first_name=first_name,
        last_name=last_name
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        
        # Save user info to text file
        with open('registered_users.txt', 'a') as f:
            f.write(f"Username: {username}, Email: {email}, Name: {first_name} {last_name}\n")
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred during registration.', 'error')
        print(f"Registration error: {str(e)}")
        return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    
    # Debug print
    print(f"Login attempt for email: {email}")
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        print("No user found")  # Debug print
        flash('No account found with that email.', 'error')
        return redirect(url_for('index'))
        
    if not check_password_hash(user.password, password):
        print("Invalid password")  # Debug print
        flash('Invalid password. Please try again.', 'error')
        return redirect(url_for('index'))
    
    # Clear any existing session data before setting new user
    session.clear()
    session['user_id'] = user.id
    flash('Successfully logged in!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('index'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
        flash('User not found.', 'error')
        return redirect(url_for('index'))
    
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('dashboard.html', username=user.username, posts=posts)

@app.route('/create_post_page', methods=['POST'])
def create_post_page():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('index'))
    
    try:
        content = request.form.get('content')
        if not content:
            flash('Post content cannot be empty!', 'error')
            return redirect(url_for('dashboard'))
        
        new_post = Post(
            content=content,
            user_id=session['user_id']
        )
        
        db.session.add(new_post)
        db.session.commit()
        
        flash('Post created successfully!', 'success')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating post: {str(e)}")
        flash('An error occurred while creating the post.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    # Use session.clear() directly
    session.clear()
    return redirect(url_for('index'))

def log_registration(user_data):
    """Helper function to log registration details"""
    log_file = "registered_users.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] New user registered:\n")
        f.write(f"Username: {user_data['username']}\n")
        f.write(f"Email: {user_data['email']}\n")
        f.write(f"First Name: {user_data['first_name']}\n")
        f.write(f"Last Name: {user_data['last_name']}\n")
        f.write("-" * 50 + "\n")

@app.route('/like/<int:post_id>', methods=['POST'])
def like_post(post_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        existing_like = Like.query.filter_by(
            user_id=session['user_id'],
            post_id=post_id
        ).first()
        
        if existing_like:
            db.session.delete(existing_like)
            action = 'unliked'
        else:
            new_like = Like(user_id=session['user_id'], post_id=post_id)
            db.session.add(new_like)
            action = 'liked'
            
        db.session.commit()
        likes_count = Like.query.filter_by(post_id=post_id).count()
        
        return jsonify({
            'status': 'success',
            'action': action,
            'likes_count': likes_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        content = request.form.get('content')
        if not content:
            return jsonify({'error': 'Comment cannot be empty'}), 400
            
        new_comment = Comment(
            content=content,
            user_id=session['user_id'],
            post_id=post_id
        )
        
        db.session.add(new_comment)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'comment_id': new_comment.id,
            'username': new_comment.user.username,
            'content': content,
            'created_at': new_comment.created_at.strftime('%Y-%m-%d %H:%M')
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/send_request/<int:to_user_id>', methods=['POST'])
def send_request(to_user_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
        
    from_user_id = session['user_id']
    
    # Check if request already exists
    existing_request = Friend.query.filter(
        ((Friend.user_id == from_user_id) & (Friend.friend_id == to_user_id)) |
        ((Friend.user_id == to_user_id) & (Friend.friend_id == from_user_id))
    ).first()
    
    if existing_request:
        return jsonify({'error': 'Friend request already exists'}), 400
        
    try:
        new_request = Friend(
            user_id=from_user_id,
            friend_id=to_user_id,
            status='pending'
        )
        db.session.add(new_request)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Friend request sent'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/accept_request/<int:friendship_id>', methods=['POST'])
def accept_request(friendship_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        # Find the pending friend request by its ID
        friend_request = Friend.query.get(friendship_id)
        
        if not friend_request:
            print("No friend request found with that ID")  # Debug print
            return jsonify({'error': 'Friend request not found'}), 404
        
        # Ensure the current user is the recipient
        if friend_request.friend_id != session['user_id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if friend_request.status != 'pending':
            return jsonify({'error': 'Request already processed'}), 400
        
        # Update the status to accepted
        friend_request.status = 'accepted'
        
        # Create notification for the sender
        notification = Notification(
            user_id=friend_request.user_id,
            type='friend_accepted',
            content=f'Your friend request was accepted!',
            from_user_id=session['user_id']
        )
        db.session.add(notification)
        
        db.session.commit()
        print(f"Friend request {friendship_id} accepted")  # Debug print
        return jsonify({'status': 'success'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error accepting friend request: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500

@app.route('/friends')
def friends():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('index'))
        
    user_id = session['user_id']
    
    # Get friend requests received
    received_requests = Friend.query.filter_by(
        friend_id=user_id,
        status='pending'
    ).all()
    
    # Get accepted friends
    friends = Friend.query.filter(
        ((Friend.user_id == user_id) | (Friend.friend_id == user_id)) &
        (Friend.status == 'accepted')
    ).all()
    
    return render_template('friends.html', 
                         received_requests=received_requests,
                         friends=friends)

@app.route('/search')
def search():
    query = request.args.get('query', '').strip()
    if not query:
        return render_template('search.html', users=[])
    
    current_user_id = session.get('user_id')
    if not current_user_id:
        return redirect(url_for('index'))
    
    # Find users matching the search query
    users = User.query.filter(
        User.id != current_user_id,  # Exclude current user
        (User.username.ilike(f'%{query}%') |
         User.email.ilike(f'%{query}%') |
         User.first_name.ilike(f'%{query}%') |
         User.last_name.ilike(f'%{query}%'))
    ).all()
    
    # Get friendship status for each user
    for user in users:
        friendship = Friend.query.filter(
            ((Friend.user_id == current_user_id) & (Friend.friend_id == user.id)) |
            ((Friend.user_id == user.id) & (Friend.friend_id == current_user_id))
        ).first()
        
        if friendship:
            user.friendship_status = friendship.status
            user.is_sender = friendship.user_id == current_user_id
        else:
            user.friendship_status = None
            user.is_sender = False
    
    return render_template('search.html', users=users)

@app.route('/check_db')
def check_db():
    try:
        # Check if database file exists
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            users = User.query.all()
            return f"""
            Database file exists at: {db_path}
            Size: {size} bytes
            Number of users: {len(users)}
            Users: {[user.username for user in users]}
            """
        else:
            return f"Database file not found at: {db_path}"
    except Exception as e:
        return f"Error checking database: {str(e)}"

@app.route('/profile/<int:user_id>')
def profile(user_id):
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('index'))
    
    # Get the profile user
    profile_user = User.query.get_or_404(user_id)
    current_user = User.query.get(session['user_id'])
    
    # Get friendship status
    friendship = Friend.query.filter(
        ((Friend.user_id == session['user_id']) & (Friend.friend_id == user_id)) |
        ((Friend.user_id == user_id) & (Friend.friend_id == session['user_id']))
    ).first()
    
    # Get user's posts
    posts = Post.query.filter_by(user_id=user_id)\
        .order_by(Post.created_at.desc())\
        .all()
    
    return render_template('profile.html',
                         profile_user=profile_user,
                         current_user=current_user,
                         friendship=friendship,
                         posts=posts)

@app.route('/chat/<int:friend_id>')
def chat(friend_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    # Verify friendship
    friendship = Friend.query.filter(
        or_(
            and_(Friend.user_id == session['user_id'], Friend.friend_id == friend_id),
            and_(Friend.user_id == friend_id, Friend.friend_id == session['user_id'])
        )
    ).first()
    
    if not friendship or friendship.status != 'accepted':
        return jsonify({'error': 'Not friends with this user'}), 403
    
    # Get unread messages
    unread_messages = Message.query.filter_by(
        sender_id=friend_id,
        receiver_id=session['user_id'],
        read=False
    ).all()
    
    # Mark messages as read
    for message in unread_messages:
        message.read = True
        message.read_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'messages': [{
            'id': message.id,
            'content': message.content,
            'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_sender': message.sender_id == session['user_id'],
            'read': message.read,
            'delivered': message.delivered
        } for message in unread_messages]
    })

@app.route('/send_message/<int:friend_id>', methods=['POST'])
def send_message(friend_id):
    print(f"Received message request for friend_id: {friend_id}")  # Debug print
    
    if 'user_id' not in session:
        print("No user in session")  # Debug print
        return jsonify({'error': 'Not logged in'}), 401
    
    current_user_id = session['user_id']
    
    # Return empty success for self-messages instead of error
    if friend_id == current_user_id:
        print("Attempted to send message to self")  # Debug print
        return jsonify({
            'status': 'success',
            'message': None
        })
    
    content = request.form.get('content', '').strip()
    print(f"Message content: {content}")  # Debug print
    
    if not content:
        print("Empty content")  # Debug print
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    try:
        # Create message
        message = Message(
            sender_id=current_user_id,
            receiver_id=friend_id,
            content=content,
            delivered=False,
            read=False
        )
        db.session.add(message)
        
        # Create notification
        sender = User.query.get(current_user_id)
        notification = Notification(
            user_id=friend_id,
            type='message',
            content=f'New message from {sender.username}',
            from_user_id=current_user_id
        )
        db.session.add(notification)
        
        db.session.commit()
        print(f"Message saved with ID: {message.id}")  # Debug print
        
        # Cache the message for the receiver
        MessageCache.cache_message(message.id, friend_id)
        print("Message cached for receiver")  # Debug print
        
        # Return complete message details including timestamp
        return jsonify({
            'status': 'success',
            'message': {
                'id': message.id,
                'content': message.content,
                'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'sender_id': message.sender_id,
                'receiver_id': message.receiver_id,
                'is_sender': True,  # This helps the UI know it's a sent message
                'delivered': message.delivered,
                'read': message.read
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error saving message: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500

@app.route('/get_new_messages/<int:friend_id>')
def get_new_messages(friend_id):
    if 'user_id' not in session:
        print("User not logged in")  # Debug print
        return jsonify({'error': 'Not logged in'}), 401
    
    current_user_id = session['user_id']
    print(f"Current user: {current_user_id}, Friend: {friend_id}")  # Debug print
    
    # First verify the friend exists
    friend = User.query.get(friend_id)
    if not friend:
        print(f"Friend with ID {friend_id} not found")  # Debug print
        return jsonify({'error': 'Friend not found'}), 404
    
    # Check friendship status
    friendship = Friend.query.filter(
        and_(
            or_(
                and_(Friend.user_id == current_user_id, Friend.friend_id == friend_id),
                and_(Friend.user_id == friend_id, Friend.friend_id == current_user_id)
            ),
            Friend.status == 'accepted'
        )
    ).first()
    
    if not friendship:
        print(f"No accepted friendship between {current_user_id} and {friend_id}")  # Debug print
        return jsonify({'error': 'Not friends with this user'}), 403
    
    try:
        # Get messages only between the current user and their friend
        messages = Message.query.filter(
            or_(
                and_(Message.sender_id == current_user_id, Message.receiver_id == friend_id),
                and_(Message.sender_id == friend_id, Message.receiver_id == current_user_id)
            )
        ).order_by(Message.created_at).all()
        
        print(f"Found {len(messages)} messages")  # Debug print
        
        messages_data = []
        current_time = datetime.utcnow()
        
        for message in messages:
            # Mark messages as delivered and read if current user is receiver
            if message.receiver_id == current_user_id:
                message.delivered = True
                if not message.read:
                    message.read = True
                    message.read_at = current_time
            
            messages_data.append({
                'id': message.id,
                'content': message.content,
                'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'sender_id': message.sender_id,
                'receiver_id': message.receiver_id,
                'is_sender': message.sender_id == current_user_id,
                'delivered': message.delivered,
                'read': message.read
            })
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'messages': messages_data,
            'friend': {
                'id': friend.id,
                'username': friend.username,
                'full_name': friend.get_full_name()
            }
        })
        
    except Exception as e:
        print(f"Error in get_new_messages: {str(e)}")  # Debug print
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/mark_messages_read/<int:friend_id>', methods=['POST'])
def mark_messages_read(friend_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        # Mark all unread messages from this friend as read
        unread_messages = Message.query.filter_by(
            sender_id=friend_id,
            receiver_id=session['user_id'],
            read=False
        ).all()
        
        current_time = datetime.utcnow()
        for message in unread_messages:
            message.read = True
            message.read_at = current_time
        
        db.session.commit()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/get_notifications')
def get_notifications():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
        
    notifications = Notification.query.filter_by(
        user_id=session['user_id'],
        read=False
    ).order_by(Notification.created_at.desc()).all()
    
    return jsonify({
        'status': 'success',
        'notifications': [{
            'id': n.id,
            'type': n.type,
            'content': n.content,
            'from_user': n.from_user.username,
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for n in notifications]
    })

@app.route('/mark_notification_read/<int:notification_id>', methods=['POST'])
def mark_notification_read(notification_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
        
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    notification.read = True
    db.session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/send_friend_request/<int:user_id>', methods=['POST'])
def send_friend_request(user_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
        
    # Prevent self-friending
    if user_id == session['user_id']:
        return jsonify({'error': 'Cannot send friend request to yourself'}), 400
    
    # Check if request already exists
    existing_request = Friend.query.filter(
        ((Friend.user_id == session['user_id']) & (Friend.friend_id == user_id)) |
        ((Friend.user_id == user_id) & (Friend.friend_id == session['user_id']))
    ).first()
    
    if existing_request:
        if existing_request.status == 'pending':
            return jsonify({'error': 'Friend request already sent'}), 400
        elif existing_request.status == 'accepted':
            return jsonify({'error': 'Already friends'}), 400
    
    try:
        # Create new friend request
        friend_request = Friend(
            user_id=session['user_id'],
            friend_id=user_id,
            status='pending'
        )
        db.session.add(friend_request)
        
        # Create notification for recipient
        sender = User.query.get(session['user_id'])
        notification = Notification(
            user_id=user_id,
            type='friend_request',
            content=f'{sender.username} sent you a friend request',
            from_user_id=session['user_id']
        )
        db.session.add(notification)
        
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/get_user/<int:user_id>')
def get_user(user_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
        
    user = User.query.get_or_404(user_id)
    return jsonify({
        'status': 'success',
        'user': {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
    })

@app.route('/get_chat_history/<int:friend_id>')
def get_chat_history(friend_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    messages = Message.query.filter(
        ((Message.sender_id == session['user_id']) & (Message.receiver_id == friend_id)) |
        ((Message.sender_id == friend_id) & (Message.receiver_id == session['user_id']))
    ).order_by(Message.created_at).all()
    
    return jsonify({
        'status': 'success',
        'messages': [{
            'id': msg.id,
            'content': msg.content,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_sender': msg.sender_id == session['user_id']
        } for msg in messages]
    })

@app.route('/unfriend/<int:friend_id>', methods=['POST'])
def unfriend(friend_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        # Find and delete the friendship
        friendship = Friend.query.filter(
            or_(
                and_(Friend.user_id == session['user_id'], Friend.friend_id == friend_id),
                and_(Friend.user_id == friend_id, Friend.friend_id == session['user_id'])
            )
        ).first()
        
        if friendship:
            db.session.delete(friendship)
            db.session.commit()
            return jsonify({'status': 'success'})
        else:
            return jsonify({'error': 'Friendship not found'}), 404
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
