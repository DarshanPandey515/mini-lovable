# mini-lovable

**mini-lovable** is a full-stack application that leverages an AI agent to build and modify React web applications based on natural language prompts. It features a Django backend, a React frontend, and a multi-step AI agent powered by the Groq API. The agent can plan an implementation, generate code, scaffold a project, run build checks, and automatically debug errors.

## Features

- **AI-Powered Code Generation**: Describe a web app, and the AI agent builds a React + Vite + Tailwind CSS implementation.
- **Multi-Step Agent Workflow**: The process is broken down into planning, code generation, building, and automated fixing.
- **Interactive Development**: The agent streams its progress in real-time, showing its plan, live build steps, and any errors it encounters.
- **Automatic Error Correction**: If an initial build fails, a "fixer" agent attempts to diagnose and correct the errors by reading files, editing code, and re-running the build.
- **Follow-up Edits**: After a project is built, you can ask the agent to make further modifications in plain language.
- **Live Preview**: See the generated React application in a live preview pane that updates as the agent works.
- **User Authentication**: Supports email/password credentials as well as OAuth 2.0 for Google and GitHub.
- **Conversation History**: Past sessions are saved, allowing users to review and resume their work.

## Architecture

The application is composed of three main parts: a React frontend, a Django backend, and the AI agent system.

- **Frontend**: A React application built with Vite and styled with Tailwind CSS. It provides the UI for authentication, starting new projects, interacting with the agent via a chat interface, and viewing the live preview.

- **Backend**: A Django and Django REST Framework application that manages:
  - User authentication (JWT, OAuth 2.0).
  - Conversation and message state, stored in a PostgreSQL database.
  - API endpoints for the frontend to interact with the agent.
  - Streaming agent progress to the client using Server-Sent Events (SSE).

- **AI Agent**: A multi-component system using `pydantic-ai` and the Groq API to understand prompts and generate code.
  - **Planner**: Analyzes the initial prompt to create a summary and a list of concrete implementation steps. It can also ask for clarification if the prompt is ambiguous.
  - **CodeGen**: Generates React, JSX, and CSS files based on the planner's output.
  - **Fixer**: A tool-using agent that can `read`, `write`, `edit` files and run `bash` commands (like `npm run build`) to debug the generated project.



## Getting Started

### Prerequisites

- Python 3.10+
- Node.js and npm
- PostgreSQL

### 1. Clone the Repository

```bash
git clone https://github.com/DarshanPandey515/mini-lovable.git
cd mini-lovable
```

### 2. Environment Configuration

Create a `.env` file in the root directory and add the following environment variables.

```env
# Django
DJANGO_SECRET_KEY=your-django-secret-key
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=lovable
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

# AI Agent
GROQ_API_KEY=your-groq-api-key

# OAuth (Optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# URLs
FRONTEND_URL=http://localhost:5173
```

### 3. Backend Setup

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Start the Django server
python manage.py runserver
```

The backend will be running at `http://127.0.0.1:8000`.

### 4. Frontend Setup

Open a new terminal window.

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the Vite development server
npm run dev
```

The frontend will be running at `http://localhost:5173`. You can now open this URL in your browser to use the application.

## Agent Workflow

The core of this project is the autonomous agent's workflow for building an application.

1.  **Prompt**: A user submits a prompt, such as "build a simple todo app".
2.  **Planning**: The `Planner` agent analyzes the prompt. If it's clear, it generates a one-sentence summary and a list of implementation steps (e.g., "Create a state for tasks", "Render a list of tasks", "Add an input field and button to add tasks").
3.  **Scaffolding**: The system programmatically creates a new project directory and scaffolds a standard Vite + React project inside it.
4.  **Code Generation**: The `CodeGen` agent receives the plan and generates the content for all necessary files (`App.jsx`, `index.css`, etc.) as a single structured JSON object.
5.  **Build**: The system writes the generated files to the project directory and runs `npm run build` to check for errors.
6.  **Fixing**: If the build fails, the `Fixer` agent is triggered. It is provided with the build error output and uses its tools (`read`, `edit`, `bash`) to attempt to fix the code, with a limited number of steps. It will re-run `npm run build` to verify its fix.
7.  **Completion**: Once the build is successful, the process is complete, and the live preview is updated. All steps are streamed to the user in real-time.
