# FastAPI Admin Dashboard with User and Group Management

This is a **FastAPI** application that provides an admin dashboard for managing users and groups. It uses **Tortoise-ORM** for database management and **UIKit** for frontend styling. The project also includes a sample view for serving static content.

## Features

- **User Authentication**: Login system with support for email-based authentication (configurable via environment variables).
- **Admin Dashboard**: 
  - View a paginated list of all users.
  - Edit user full names and delete users.
  - Change user passwords (only for administrators).
  - Manage user groups: add users to groups, remove users from groups, create new groups, rename groups, and delete groups.
- **User Registration**: Register new users using the provided registration form. Optionally, require an invite code for registration.
- **Group Management**: Users can be in one or multiple groups, and only administrators have permissions to manage groups.
- **Static Content**: A sample view for serving static content available at the root URL.

## Environment Variables

Configure the behavior of the application using the following environment variables:

- `SECRET_KEY`: Your secret key for JWT token generation.
- `INVITE_CODE_ENABLED`: Enable or disable the use of invite codes during registration (`true` or `false`).
- `INVITE_CODE`: The invite code required for user registration (if enabled).
- `REGISTRATION_ENABLED`: Enable or disable user registration (`true` or `false`).
- `DB_URL`: The database URL for Tortoise-ORM (e.g., `sqlite://db.sqlite3` for SQLite).
- `EMAIL_AUTH_ENABLED`: Enable or disable email-based authentication (`true` or `false`).
- `USERS_PER_PAGE`: The number of users to display per page on the dashboard.
- `DASHBOARD_TEXT`: Customizable text for the admin dashboard header.

## How to Run

1. **Clone the Repository**:
   ```
   git clone https://github.com/endlessnights/fastapi-auth.git
   cd fastapi-auth
   ```
2. Create and Activate a Virtual Environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   venv\Scripts\activate     # On Windows
   ```
3. Install Dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Set Environment Variables: Create a .env file in the root directory and add the following:
   ```
   SECRET_KEY=your-secret-key
   INVITE_CODE_ENABLED=true
   INVITE_CODE=my-invite-code
   REGISTRATION_ENABLED=true
   DB_URL=sqlite://db.sqlite3
   EMAIL_AUTH_ENABLED=false
   USERS_PER_PAGE=10
   DASHBOARD_TEXT="This is the admin dashboard."
   ```
5. Run the Application:
   ```
   uvicorn app.main:app --reload
   ```
The application will be available at http://127.0.0.1:8000.
Access the Dashboard:
Admin Login: Visit http://127.0.0.1:8000/admin to log in.
Dashboard: View and manage users and groups at http://127.0.0.1:8000/admin/dashboard
Static Content:
The static content is available at the root URL: http://127.0.0.1:8000/

Notes
Database: By default, the application uses SQLite. You can change the database URL to use other databases supported by Tortoise-ORM.
Secret Key: Make sure to set a secure SECRET_KEY for production.
Invite Code: If INVITE_CODE_ENABLED is set to true, users will need the invite code specified in INVITE_CODE to register.
User Registration: This application provides the ability to register new users, with optional invite code verification.
Admin User: A default admin user is created with username admin and password admin. Change this in a production environment.


