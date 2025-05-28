# AI Chatbot Platform

An intelligent chatbot platform that combines modern web technologies to deliver interactive conversations and data-driven insights. You can transfer from online research to internal research. It features a **Next.js frontend**, a **Node.js backend** for database communication, **Python services** for OpenAI-powered responses and analytics, and **SQL Server** for persistent storage.

---

## Architecture Overview

```
[Frontend - Next.js]
        |
        v
[Node.js API Server] ───> [SQL Server: users & chat logs]
                                |
                                v
[Python Service: OpenAI + Data Analysis]
```

---

## ⚙️ Tech Stack

| Layer       | Technology        | Purpose                                       |
| ----------- | ----------------- | --------------------------------------------- |
| Frontend    | Next.js (React)   | User interface, chat window, login/register   |
| Backend API | Node.js + Express | Auth, DB access, API bridge to Python service |
| AI Engine   | Python            | Data processing, OpenAI API integration       |
| Database    | SQL Server        | Stores users, chat history                    |
| AI API      | OpenAI GPT API    | Generates intelligent responses and summaries |

---

## Features

* ✅ User login & registration (with SQL Server)
* 💬 Real-time chat interface
* 🤖 GPT-based responses using OpenAI API
* 📊 Python-powered data analysis
* 🧠 Logs all conversations to SQL Server
* 🔗 Modular API communication (Node ↔ Python)

---

## Project Structure

```
project-root/
│
├── frontend/             # Next.js (React-based UI)
│   └── pages/
│
├── backend/              # Node.js API server
│   └── routes/
│
├── python-service/       # Python service for AI & analytics
│   └── app.py
│
├── sql/                  # SQL scripts and schema definitions
│
└── README.md
```

---

## Setup Instructions

### 1. Clone the repository

### 2. Set up SQL Server

### 3. Backend (Node.js API)

```bash
cd API
npm install
# Configure DB credentials in `.env`
node server.js
```

### 4. Python Service (OpenAI + Analysis)

```bash
cd Modelo/src
install the dependencies
# Set OPENAI_API_KEY in .env
python main.py
```

### 5. Frontend (Next.js)

```bash
cd WebInterface/andritz_ai
npm install
npm run dev
```

---

## Environment Variables

### `.env` for Node.js API:

```
DB_HOST=localhost
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=your_db_name
APIs endpoints (routes/web sockets)
```

`.env` for Python:

```
OPENAI_API_KEY=your-openai-api-key
DB_HOST=localhost
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=your_db_name
```

---

## API Communication

### Node.js ↔ SQL Server

* Handles user authentication
* Reads/writes chat logs

### Node.js ↔ Python (via HTTP)

* Forwards user messages to Python
* Python handles:

  * Calling OpenAI API
  * Performing data analysis
  * Returning GPT responses
