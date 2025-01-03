# Social Media App

A Flask-based social media application with user authentication, friend management, and post sharing capabilities. This project demonstrates a full-stack web application using Python, SQLite, and modern web technologies.

## Features

- **User Authentication**
  - Secure registration and login
  - Password hashing
  - Session management

- **Profile Management**
  - User profiles with username and full name
  - Profile customization options

- **Friend System**
  - Send friend requests
  - Accept/manage friend requests
  - View friends list

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

- **Friends**
  - id (Primary Key)
  - user_id (Foreign Key)
  - friend_id (Foreign Key)
  - status
  - created_at

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



