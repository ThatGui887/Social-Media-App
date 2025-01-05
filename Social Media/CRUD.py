import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import or_, text

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

def init_db():
    with app.app_context():
        inspector = db.inspect(db.engine)
        
        # Check if the database needs to be created
        if not os.path.exists(db_path):
            print("Creating new database...")
            db.create_all()
            print("Database created successfully!")
            return

        # If database exists, check for missing columns
        if 'user' in inspector.get_table_names():
            columns = [column['name'] for column in inspector.get_columns('user')]
            
            # If new columns are missing, recreate the tables
            if 'first_name' not in columns or 'last_name' not in columns:
                print("Updating database schema...")
                try:
                    # Get existing users without the new columns using text()
                    sql = text('SELECT id, username, email, password FROM user')
                    existing_users = db.session.execute(sql).fetchall()
                    
                    # Drop and recreate tables
                    db.session.commit()  # Commit any pending transactions
                    db.drop_all()
                    db.create_all()
                    
                    # Restore users with new schema
                    for user in existing_users:
                        new_user = User(
                            username=user[1],
                            email=user[2],
                            password=user[3],
                            first_name='',  # Default value
                            last_name=''    # Default value
                        )
                        db.session.add(new_user)
                    
                    db.session.commit()
                    print("Database schema updated successfully!")
                except Exception as e:
                    db.session.rollback()
                    print(f"Error updating database: {str(e)}")
                    raise
            else:
                print("Database schema is up to date.")
        else:
            print("Creating new tables...")
            db.create_all()
            print("Tables created successfully!")

# Make sure all models are defined before initializing
init_db()

# Routes
@app.route('/')
def index():
    # Clear any existing session data when returning to index
    session.clear()
    return render_template('index.html', clear_form=True)

@app.route('/register', methods=['POST'])
def register():
    try:
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name', '')
        last_name = request.form.get('last_name', '')
        
        # First READ to check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return redirect(url_for('index'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('index'))
        
        # WRITE to database
        print(f"Writing to database: Creating new user with username {username}")
        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            first_name=first_name,
            last_name=last_name
        )
        
        db.session.add(new_user)
        db.session.commit()
        print(f"Successfully wrote new user to database: {username}")
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Database write error during registration: {str(e)}")
        flash(f'An error occurred during registration: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    try:
        # Get form data without any defaults
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        # Debug print to check exact values being used
        print(f"Login attempt - Email: {email}")
        
        # READ from database - explicitly query for this exact email
        user = User.query.filter(User.email == email).first()
        
        if user and check_password_hash(user.password, password):
            # Clear any existing session data before setting new
            session.clear()
            session['user_id'] = user.id
            print(f"Login successful for user: {user.username}")
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            print("Login failed - Invalid credentials")
            flash('Invalid email or password!', 'error')
            return redirect(url_for('index'))
            
    except Exception as e:
        print(f"Login error: {str(e)}")
        flash('An error occurred during login.', 'error')
        return redirect(url_for('index'))

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

@app.route('/create_post', methods=['POST'])
def create_post():
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
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
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

@app.route('/accept_request/<int:request_id>', methods=['POST'])
def accept_request(request_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
        
    try:
        friend_request = Friend.query.get(request_id)
        if not friend_request:
            return jsonify({'error': 'Request not found'}), 404
            
        if friend_request.friend_id != session['user_id']:
            return jsonify({'error': 'Not authorized'}), 403
            
        friend_request.status = 'accepted'
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Friend request accepted'})
    except Exception as e:
        db.session.rollback()
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
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('index'))
        
    query = request.args.get('query', '').strip()
    if query:
        # Search across multiple fields using OR conditions
        users = User.query.filter(
            db.or_(
                User.username.ilike(f'%{query}%'),
                User.first_name.ilike(f'%{query}%'),
                User.last_name.ilike(f'%{query}%')
            )
        ).filter(User.id != session['user_id']).all()  # Exclude current user from results
        
        # Debug print
        print(f"Search query: {query}")
        print(f"Found users: {[f'{user.username} ({user.first_name} {user.last_name})' for user in users]}")
    else:
        users = []
    
    return render_template('search.html', users=users, query=query)

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

if __name__ == '__main__':
    app.run(debug=True)
