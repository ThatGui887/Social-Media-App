from flask import Flask, request, jsonify, session, current_app, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash

# Init app
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for sessions
basedir = os.path.abspath(os.path.dirname(__file__))

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'social_media.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Init extensions
db = SQLAlchemy(app)
ma = Marshmallow(app)
bcrypt = Bcrypt(app)

with app.app_context():
    db.drop_all()
    db.create_all()

# Models
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Add relationship to User model
    user = db.relationship('User', backref=db.backref('posts', lazy=True))

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

# Schemas
class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'username', 'email')

class PostSchema(ma.Schema):
    class Meta:
        fields = ('id', 'content', 'media_url', 'media_type', 'timestamp', 'user_id')

class CommentSchema(ma.Schema):
    class Meta:
        fields = ('id', 'content', 'timestamp', 'user_id', 'post_id')

class LikeSchema(ma.Schema):
    class Meta:
        fields = ('id', 'user_id', 'post_id')

# Init schemas
user_schema = UserSchema()
users_schema = UserSchema(many=True)
post_schema = PostSchema()
posts_schema = PostSchema(many=True)
comment_schema = CommentSchema()
comments_schema = CommentSchema(many=True)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

def log_registration(user_data):
    """Helper function to log registration details"""
    log_file = "registered_users.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] New user registered:\n")
        f.write(f"Username: {user_data['username']}\n")
        f.write(f"Email: {user_data['email']}\n")
        f.write("-" * 50 + "\n")

@app.route('/register', methods=['POST'])
def register():
    try:
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('index'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return redirect(url_for('index'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('index'))
        
        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Log the registration
        log_registration({
            'username': username,
            'email': email
        })
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Error during registration: {str(e)}")
        flash(f'An error occurred during registration: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'error')
            return redirect(url_for('index'))
            
    except Exception as e:
        print(f"Login error: {str(e)}")
        flash('An error occurred during login.', 'error')
        return redirect(url_for('index'))

@app.route('/post', methods=['POST'])
def create_post():
    if 'user_id' not in session:
        return jsonify({'message': 'Please login'}), 401
        
    content = request.json.get('content')
    media_url = request.json.get('media_url')
    media_type = request.json.get('media_type')
    
    new_post = Post(content=content, media_url=media_url, media_type=media_type, user_id=session['user_id'])
    db.session.add(new_post)
    db.session.commit()
    
    return post_schema.jsonify(new_post)

@app.route('/posts', methods=['GET'])
def get_posts():
    all_posts = Post.query.order_by(Post.timestamp.desc()).all()
    return posts_schema.jsonify(all_posts)

@app.route('/post/<post_id>/like', methods=['POST'])
def like_post(post_id):
    if 'user_id' not in session:
        return jsonify({'message': 'Please login'}), 401
        
    existing_like = Like.query.filter_by(user_id=session['user_id'], post_id=post_id).first()
    if existing_like:
        db.session.delete(existing_like)
    else:
        new_like = Like(user_id=session['user_id'], post_id=post_id)
        db.session.add(new_like)
    db.session.commit()
    
    return jsonify({'message': 'Success'})

@app.route('/post/<post_id>/comment', methods=['POST'])
def add_comment(post_id):
    if 'user_id' not in session:
        return jsonify({'message': 'Please login'}), 401
        
    content = request.json['content']
    new_comment = Comment(content=content, user_id=session['user_id'], post_id=post_id)
    db.session.add(new_comment)
    db.session.commit()
    
    return comment_schema.jsonify(new_comment)

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
    
    # Get all posts, ordered by newest first
    posts = Post.query.order_by(Post.created_at.desc()).all()
    
    return render_template('dashboard.html', username=user.username, posts=posts)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run(debug=True)
