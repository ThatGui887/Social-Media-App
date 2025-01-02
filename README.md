# Social Media Application

A Flask-based social media application with basic user authentication and posting capabilities.

## Features

### User Authentication
- **Registration System**
  - Username and email uniqueness validation
  - Password confirmation
  - Secure password hashing
  - Registration logging system for developers

- **Login System**
  - Email and password authentication
  - Session management
  - Secure login state maintenance

- **Logout Functionality**
  - Session clearing
  - Redirect to login page

### Post Management
- Create new posts
- View all posts in chronological order
- Posts display:
  - Author username
  - Creation timestamp
  - Content
  - Action buttons (Like/Comment - functionality pending)

### Developer Features
- Registration logging to text file
- Debug mode enabled
- Error handling and flash messages
- Database management with SQLAlchemy

## Technical Details

### Database Models

#### User Model
- id (Primary Key)
- username (Unique)
- email (Unique)
- password (Hashed)

#### Post Model
- id (Primary Key)
- content
- created_at
- user_id (Foreign Key)

### File Structure
