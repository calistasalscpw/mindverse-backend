#  Mindverse Backend

Mindverse Backend is the server-side application for the KADA Capstone Project, providing RESTful APIs for user authentication, forum posts, comments, and task management. It is built with Node.js, Express, MongoDB, and Passport.js for authentication.

## Table of Contents
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [Running the Project](#running-the-project)
- [API Endpoints](#api-endpoints)
- [Authentication](#authentication)
- [Docker Support](#docker-support)
- [Contributing](#contributing)
- [License](#license)

## Features
* **User Management:** Supports user registration with both email/password and Google accounts. It also includes email verification for new users to ensure valid accounts.
* **Secure Authentication:** Uses JSON Web Tokens (JWT) to secure the API, ensuring that only authenticated users can access protected data.
* **Forum and Comments:** Provides complete functionality for creating, reading, updating, and deleting forum posts and comments.
* **Task Management:** Allows for creating, assigning, and updating tasks. It also supports changing the status of a task (e.g., from "To Do" to "Done").
* **Role-Based Permissions:** Implements a permission system where certain roles (like "Lead" or "HR") have special privileges, such as creating or assigning tasks.
* **API Design:** Follows RESTful principles for a structured and predictable API. It also includes CORS support so the frontend application can make requests to it.

## 💻 Tech Stack
- Node.js 🟩
- Express.js ⚡
- MongoDB (via Mongoose) 🍃
- Passport.js (Local, JWT, Google OAuth2) 🛂
- Nodemailer (for email verification) ✉️
- bcrypt (for password hashing) 🔒
- Docker (for containerization) 🐳

## 📁 Project Structure
mindverse-frontend/
├── public/                 # Static assets
├── src/
│   ├── assets/             # Images and other static assets
│   ├── components/         # Reusable UI components 🧩
│   │   ├── ChatBot.jsx
│   │   ├── ForumPostCard.jsx
│   │   ├── LoginForm.jsx
│   │   ├── Navbar.jsx
│   │   ├── TaskCreate.jsx
│   │   └── TaskEdit.jsx
│   ├── contexts/           # React Context API providers & hooks 🎣
│   │   └── AuthContext.jsx
│   ├── pages/              # Top-level page components (views) 📄
│   │   ├── CreatePost.jsx
│   │   ├── Forum.jsx
│   │   ├── ForumPostDetail.jsx
│   │   ├── Home.jsx
│   │   ├── Login.jsx
│   │   └── Signup.jsx
│   ├── App.css             # Global CSS styles
│   ├── App.jsx             # Main application component & routing 🌐
│   ├── index.css           # Root CSS
│   ├── main.jsx            # Entry point of the React application
│   └── api.js              # (Presumed) Centralized API client/utilities
├── .gitignore              # Files/folders ignored by Git
├── index.html              # Main HTML file
├── package.json            # Project dependencies and scripts
├── vite.config.js          # Vite configuration
└── README.md               # You are here! 📍

---

## 🧩 Core Components & Pages

### Components (`src/components/`)

* **`Navbar.jsx`** 🧭
    * **Description:** The fixed top navigation bar, providing quick access to **Dashboard** and **Forum**, integrated search functionality, and a user profile dropdown menu.
* **`ChatBot.jsx`** 🤖
    * **Description:** A discreet floating chatbot assistant, offering animated UI feedback and maintaining a history of user interactions for seamless query resolution.
* **`LoginForm.jsx`** 🔒
    * **Description:** The essential form component for user authentication, featuring email and password input fields, styled with Ant Design's elegant components.
* **`ForumPostCard.jsx`** 📬
    * **Description:** A reusable card component to visually represent a forum post summary, including the author's information and the total comment count.
* **`TaskCreate.jsx`** ➕
    * **Description:** A modal form interface allowing users to **create new tasks**. This includes fields for task assignment, due dates, and detailed descriptions.
* **`TaskEdit.jsx`** ✏️
    * **Description:** A modal form designed for **editing existing tasks**, providing a similar intuitive interface and functionality to the `TaskCreate` component.

### Contexts (`src/contexts/`)

* **`AuthContext.jsx`** 🔑
    * **Description:** Implements the **React Context API** to provide global authentication state throughout the application. It includes user information (`user`) and methods for managing authentication status (`login`, `logout`).

### Pages (`src/pages/`)

* **`Home.jsx`** 🏠
    * **Description:** The central personal dashboard. It features interactive, draggable task columns for organizing workflow and a dynamic list of team members.
* **`Forum.jsx`** 💬
    * **Description:** The main community forum page, displaying a comprehensive listing of posts, equipped with search capabilities and pagination for easy navigation.
* **`ForumPostDetail.jsx`** 📖
    * **Description:** Provides a detailed view of an individual forum post, allowing users to read the full content and associated comments.
* **`CreatePost.jsx`** ✍️
    * **Description:** A modal interface facilitating the creation of new forum posts, enabling users to contribute to the community discussion seamlessly.
* **`Login.jsx`** ➡️
    * **Description:** The dedicated login page, serving as a container that renders the `LoginForm` component for user authentication.
* **`Signup.jsx`** ✅
    * **Description:** The user registration page, offering options for profile image uploads and integrating Google login for convenience.

---

## 🚦 Frontend Routing

The application's navigation is managed by React Router DOM, providing clean and intuitive URLs:

* `/` ➡️ Home Dashboard
* `/auth/signup` ➡️ User Registration Page
* `/auth/login` ➡️ User Login Page
* `/addtask` ➡️ Opens the Task Creation Modal (popup)
* `/edittask` ➡️ Opens the Task Editing Modal (popup)
* `/forum` ➡️ Community Forum Main Page
* `/forum/:postId` ➡️ Detailed View for a Specific Forum Post

---

## ⚙️ Getting Started (Frontend)

To run the MindVerse frontend locally:

1.  **Clone the repository:**
    ```bash
    git clone <YOUR_FRONTEND_REPO_URL>
    ```
2.  **Navigate to the frontend directory:**
    ```bash
    cd mindverse-frontend
    ```
3.  **Install dependencies:**
    ```bash
    npm install
    # or yarn install
    ```
4.  **Start the development server:**
    ```bash
    npm run dev
    # or yarn dev
    ```
    The application will typically be accessible at [http://localhost:5173/](http://localhost:5173/).

---

**Note:** For questions or issues, please open an [issue](https://github.com/calistasalscpw/mindverse-backend/issues).
