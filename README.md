#  Mindverse Backend

Mindverse Backend is the server-side application for the KADA Capstone Project, providing RESTful APIs for user authentication, forum posts, comments, and task management. It is built with Node.js, Express, MongoDB, and Passport.js for authentication.

## Features
* **User Management:** Supports user registration with both email/password and Google accounts. It also includes email verification for new users to ensure valid accounts.
* **Secure Authentication:** Uses JSON Web Tokens (JWT) to secure the API, ensuring that only authenticated users can access protected data.
* **Forum and Comments:** Provides complete functionality for creating, reading, updating, and deleting forum posts and comments.
* **Task Management:** Allows for creating, assigning, and updating tasks. It also supports changing the status of a task (e.g., from "To Do" to "Done").
* **Role-Based Permissions:** Implements a permission system where certain roles (like "Lead" or "HR") have special privileges, such as creating or assigning tasks.
* **API Design:** Follows RESTful principles for a structured and predictable API. It also includes CORS support so the frontend application can make requests to it.

## 💻 Tech Stack
* **Runtime:** Node.js
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
    Create a `.env` file in the root of the project and add the necessary configuration values (e.g., database connection string, JWT secret).
5.  **Navigate to the chatbot directory:**
    ```bash
    cd chatbot
    ```
6.  **Install python libraries for chatbot:**
    ```bash
    pip install -r requirements.txt
    cd ../
    ```
5.  **Start the server:**
    ```bash
    npm start
    ```
    The server will typically run on `http://localhost:3000`.

---

## API Endpoints

The backend provides several API endpoints for the frontend to use:

### Authentication
* `POST /auth/register`: Creates a new user account.
* `POST /auth/login`: Logs in a user and returns a JWT token.
* `GET /auth/user`: Retrieves the profile of the currently logged-in user.

### Tasks
* `GET /tasks`: Retrieves a list of all tasks.
* `POST /tasks`: Creates a new task (restricted to authorized roles).
* `PUT /tasks/:id`: Updates an existing task.
* `DELETE /tasks/:id`: Deletes a task.
* `PATCH /tasks/:id/status`: Updates the status of a specific task.

### Forum
* `GET /forum/posts`: Retrieves all forum posts.
* `POST /forum/posts`: Creates a new forum post.
* `GET /forum/posts/:id`: Retrieves a single post and its comments.
* `POST /forum/posts/:id/comments`: Adds a new comment to a post.

---

## Authentication

Authentication is managed using Passport.js. When a user logs in, the server generates a JSON Web Token (JWT). This token must be included in the header of all subsequent requests to protected API endpoints to verify the user's identity.