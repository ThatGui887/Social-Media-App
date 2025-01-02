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
project/
├── CRUD.py
├── social_media.db
├── registered_users.txt
├── static/
│ └── css/
│ └── style.css
└── templates/
├── index.html
└── dashboard.html


## Update History

### Version 1.0
- Initial setup
- Basic Flask application structure
- Static files configuration

### Version 1.1
- Added user registration
- Created basic index page
- Implemented CSS styling

### Version 1.2
- Added login functionality
- Created dashboard template
- Implemented session management

### Version 1.3
- Added Post model
- Implemented post creation
- Added post display on dashboard
- Enhanced dashboard styling

### Version 1.4
- Added developer logging system
- Enhanced error handling
- Added flash messages
- Improved form validation

## Pending Features
1. Like system for posts
2. Comment system
3. User profiles
4. Post deletion
5. User avatar support
6. Friend/Follow system
7. Post privacy settings
8. User search functionality

## Technical Requirements
- Python 3.x
- Flask
- Flask-SQLAlchemy
- Werkzeug

## Installation

1. Clone the repository
2. Install required packages:
3. Run the application:
4. Access the application at `http://localhost:5000`

## Development Notes
- Database is automatically created on first run
- Debug mode is enabled for development
- Registration logs are stored in `registered_users.txt`
- All passwords are hashed before storage
- Session management is implemented for security

## Security Features
- Password hashing
- Session management
- Form validation
- SQL injection prevention through SQLAlchemy
- Unique constraint enforcement
- Protected routes requiring authentication

## Contributing
Feel free to fork this project and submit pull requests for any enhancements.

## License
This project is open source and available under the MIT License.
