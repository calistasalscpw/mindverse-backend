#  Mindverse Backend

Mindverse Backend is the server-side application for the KADA Capstone Project, providing RESTful APIs for user authentication, forum posts, comments, and task management. It is built with Node.js, Express, MongoDB, and Passport.js for authentication.

## Features
* **User Management:** Supports user registration with both email/password and Google accounts. It also includes email verification for new users to ensure valid accounts.
* **Secure Authentication:** Uses JSON Web Tokens (JWT) to secure the API, ensuring that only authenticated users can access protected data.
* **Forum and Comments:** Provides complete functionality for creating, reading, updating, and deleting forum posts and comments.
* **Task Management:** Allows for creating, assigning, and updating tasks. It also supports changing the status of a task (e.g., from "To Do" to "Done").
* **Role-Based Permissions:** Implements a permission system where certain roles (like "Lead") have special privileges, such as creating or assigning tasks.
* **AI Chatbot:** A Python-based AI assistant that can answer questions about tasks, forum posts, and users by querying the database.
* **AI Meeting Scheduler:** A feature that analyzes task details to suggest optimal meeting parameters and sends email invitations.
* **API Design:** Follows RESTful principles for a structured and predictable API. It also includes CORS support so the frontend application can make requests to it.

## Tech Stack
* **Runtime:** Node.js, Python
* **Framework:** Express.js
* **Database:** MongoDB, with Mongoose as the library for interacting with the database.
* **Authentication:** Passport.js is used to handle different authentication strategies (local, JWT, and Google).
* **Email:** Nodemailer is used for sending verification emails to new users.
* **Security:** The bcrypt library is used for securely hashing user passwords before storing them.
* **Containerization:** Docker is supported for running the application in a containerized environment.

---

## Setup and Installation

To run the backend on your local machine, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/calistasalscpw/mindverse-backend.git
    ```
2.  **Navigate to the backend directory:**
    ```bash
    cd mindverse-backend
    ```
3.  **Install dependencies:**
    ```bash
    npm install
    ```
4.  **Set up Environment Variables:**
    Create a `.env` file in the root of the project and add the necessary configuration values (e.g., database connection string, JWT secret). Example:
    ```.env
    MONGO_URL="your-mongodb-string"
    JWT_SECRET_KEY="your-jwt-secret"
    GOOGLE_APP_PASSWORD="your-google-app-password"
    GOOGLE_CLIENT_ID="your-google-client-id"
    GOOGLE_SECRET="your-google-secret"
    OPENAI_API_KEY="your-openai-api-key"
    ```
6.  **Navigate to the chatbot directory:**
    ```bash
    cd chatbot
    ```
7.  **Install python libraries for chatbot:**
    ```bash
    pip install -r requirements.txt
    cd ../
    ```
8.  **Start the server:**
    ```bash
    npm start
    ```
    The server will typically run on `http://localhost:3000`.

---

## API Endpoints

The backend provides several API endpoints for the frontend to use:

### Authentication
* `POST /auth/signup`: Creates a new user account.
* `POST /auth/login`: Logs in a user and returns a JWT token.
* `GET /auth/profile`: Retrieves the profile of the currently logged-in user.
* `GET /auth/verify-email`: Verifies a user's email address.

### Tasks
* `GET /tasks`: Retrieves a list of all tasks.
* `POST /tasks`: Creates a new task (restricted to authorized roles).
* `PUT /tasks/:taskId`: Updates an existing task.
* `DELETE /tasks/:taskId`: Deletes a task.
* `PATCH /tasks/:taskId/status`: Updates the status of a specific task.

### Forum
* `GET /forum`: Retrieves all forum posts.
* `POST /forum`: Creates a new forum post.
* `GET /forum/:postId`: Retrieves a single post and its comments.
* `PUT /forum/:postId`: Updates a post.
* `DELETE /forum/:postId`: Deletes a post.

### Comments
* `POST /forum/:postId/comments`: Adds a new comment to a post.
* `GET /forum/:postId/comments`: Retrieves all comments for a post.

### Chatbot
* `POST /chatbot/chat`: Sends a message to the AI chatbot and gets a response.
* `GET /chatbot/stats`: Retrieves database statistics.
* `GET /chatbot/health`: Checks the health of the chatbot service.

### Meetings
* `POST /meetings/analyze-task`: Analyzes a task to get AI-powered meeting suggestions.
* `POST /meetings/schedule`: Schedules a meeting and sends email invitations.
---

## Authentication

Authentication is managed using Passport.js. When a user logs in, the server generates a JSON Web Token (JWT). This token must be included in the header of all subsequent requests to protected API endpoints to verify the user's identity.
