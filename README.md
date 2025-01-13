# Social Media App

A Flask-based social media application with user authentication, friend management, and post sharing capabilities. This project demonstrates a full-stack web application using Python, SQLite, and modern web technologies.

# Features

- **User Authentication**
  - Secure registration and login
  - Password hashing
  - Session management

- **Profile Management**
  - User profiles with username and full name
  - Profile customization options
  - User registration with email verification
  - Secure login/logout functionality
  - Profile management
  - Session handling for multiple accounts

- **Messaging System**
  - Real-time chat between friends
  - Message status tracking (delivered/read)
  - Chat history
  - FIFO message caching
  - Message notifications

- **Notification sytem**
  - Real-time notifications
  - Friend request notifications
  - New message alerts
  - Notification badge counter
  - Clickable notifications that open relevant content

- **Friend System**
  - Send friend requests
  - Accept/manage friend requests
  - View friends list
  - Unfriend functionality
  - Friend list Management
  - User search functionality

- **Post Management**
  - Create and view posts
  - Like system
  - Comment functionality

- **Search Functionality**
  - Search users by username or full name
  - Filter search results

## Technology Stack

- **Backend**
  - Python 3.x
  - Flask
  - SQLAlchemy
  - SQLite

- **Frontend**
  - HTML5
  - CSS3
  - JavaScript
  - Font Awesome

- **Database**
  - SQLite3

## Installation

1. Clone the repository
2. 
2. Create a virtual environment
3. 
3. Install dependencies
4. 
4. Run the application
5. 
5. Access the application at `http://localhost:5000`

## Project Structure
├── CRUD.py # Main application file
├── requirements.txt # Project dependencies
├── social_media.db # SQLite database
│
├── static/
│ └── css/
│ └── style.css # Application styles
│
├── templates/
│ ├── index.html # Login/Register page
│ ├── dashboard.html # User dashboard
│ ├── friends.html # Friends management
│ └── search.html # User search


## Database Schema

- **Users**
  - id (Primary Key)
  - username
  - email
  - password (hashed)
  - first_name
  - last_name
  - created_at

- **Friends**
  - id (Primary Key)
  - user_id (Foreign Key)
  - friend_id (Foreign Key)
  - status
  - created_at
 
- **Message**
  - id (Primary Key)
  - sender_id (Foreign Key)
  - receiver_id (Foreign Key)
  - content
  - created_at
  - delivered (Boolean)
  - read (Boolean)
  - read_at (Timestamp)
 
- **Notifications**
  - id (Primary Key)
  - user_id (Foreign Key)
  - type (message/friend_request)
  - content
  - from_user_id (Foreign Key)
  - created_at
  - read (Boolean)

- **MessageCache**
  - id (Primary Key)
  - message_id (Foreign Key)
  - user_id (Foreign Key)
  - cached_at

- **Posts**
  - id (Primary Key)
  - content
  - user_id (Foreign Key)
  - created_at

- **Likes**
  - id (Primary Key)
  - user_id (Foreign Key)
  - post_id (Foreign Key)
  - created_at

- **Comments**
  - id (Primary Key)
  - content
  - user_id (Foreign Key)
  - post_id (Foreign Key)
  - created_at

- **Real-time Updates**
  - Polling system for new messages (5-second interval)
  - Notification checking (10-second interval)
  - Optimized to reduce server load
  - Visibility state management

- **Message Handling**
  - FIFO message caching system
  - Read receipts
  - Delivery confirmation
  - Message history preservation

- **Friend Management**
  - Bidirectional friendship system
  - Request validation
  - Friendship status tracking
  - Immediate UI updates

- **Security Features**
  - Password hashing
  - Session management
  - CSRF protection
  - Input validation
  - XSS prevention
  - Multiple account isolation

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/improvement`)
3. Make changes
4. Commit your changes (`git commit -am 'Add new feature'`)
5. Push to the branch (`git push origin feature/improvement`)
6. Create a Pull Request

## License

None

## Acknowledgments

- Flask documentation and community
- SQLAlchemy documentation
- Font Awesome for icons

# Bug Report Log

## Fixed Bugs

### Database Issues
1. **Database Creation Loop** *(Fixed: 2024-03-XX)*
   - **Issue**: Database being recreated on every app restart
   - **Fix**: Modified init_db() to check for existing database
   - **File**: CRUD.py
   - **Status**: ✅ Resolved

2. **Login Field Auto-Population** *(Fixed: 2024-03-XX)*
   - **Issue**: Default values appearing in login fields
   - **Fix**: Added autocomplete="off" and form clearing on page load
   - **File**: templates/index.html
   - **Status**: ✅ Resolved

3. **Database Reading/Writing** *(Fixed: 2024-03-XX)*
   - **Issue**: Inconsistent database access
   - **Fix**: Implemented proper READ/WRITE operations
   - **File**: CRUD.py
   - **Status**: ✅ Resolved

### Friend System Issues
1. **Friend Model Relationship** *(Fixed: 2024-03-XX)*
   - **Issue**: UndefinedError: 'Friend object' has no attribute 'user'
   - **Fix**: Added proper relationships to Friend model
   - **File**: CRUD.py
   - **Status**: ✅ Resolved

### Authentication Issues
1. **Session Management** *(Fixed: 2024-03-XX)*
   - **Issue**: Session not clearing on logout
   - **Fix**: Added session.clear() to logout route
   - **File**: CRUD.py
   - **Status**: ✅ Resolved

## Known Issues

### UI/UX Issues
1. **Search Results Pagination**
   - **Issue**: All search results shown on one page
   - **Impact**: Performance issues with large user base
   - **Status**: 🔄 Pending
   - **Proposed Fix**: Implement pagination for search results

2. **Friend Request Notifications**
   - **Issue**: No real-time notifications for friend requests
   - **Impact**: Users must refresh to see new requests
   - **Status**: 🔄 Pending
   - **Proposed Fix**: Implement WebSocket for real-time updates

### Performance Issues
1. **Database Query Optimization**
   - **Issue**: N+1 query problem in friend list
   - **Impact**: Slow loading of friends page with many connections
   - **Status**: 🔄 Pending
   - **Proposed Fix**: Implement eager loading for friend relationships

### Security Issues
1. **Password Reset**
   - **Issue**: No password reset functionality
   - **Impact**: Users can't recover lost accounts
   - **Status**: 🔄 Pending
   - **Proposed Fix**: Implement email-based password reset



