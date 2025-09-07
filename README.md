# 🧠 Socrate - AI Mentor for Junior Developers

> **An AI mentoring system that guides junior developers towards autonomy using the Socratic method**

🌐 **Live Demo**: [https://socrateai.vercel.app/](https://socrateai.vercel.app/)

Socrate is an AI-powered mentoring platform designed to accelerate junior developer growth while giving managers full visibility and control over team progress. Leveraging advanced Socratic pedagogy, Socrate guides juniors through interactive questions and hints instead of providing direct answers, promoting autonomous learning and faster skill acquisition. Meanwhile, managers gain access to a centralized dashboard with real-time analytics, allowing them to track progress, identify skill gaps, and optimize integration and mentoring efforts, all while saving time and reducing repetitive supervision tasks.

## ✨ Key Features

- **🤖 Socratic AI Mentor**: Interactive chat with guided discovery learning
- **📊 Learning Analytics**: Progress tracking and performance insights for managers
- **🎯 Adaptive Flashcards**: Spaced repetition system for knowledge retention
- **💻 IDE Interface**: Monaco Editor integration for code practice
- **🧠 Memory System**: ChromaDB-powered conversation memory

## 🚀 Quick Setup

### Prerequisites

- **Node.js 18+** and **npm**
- **Python 3.11+** and **pip**
- **Blackbox API Key** ([Get one here](https://blackbox.ai/api))

### Installation

```bash

# Clone the repository

git clone git@github.com:hugoganet/hackathon_blackbox.git socrate-mentor-ia

cd socrate-mentor-ia

# Environment setup

cp .env.example .env

# Edit .env and add your BLACKBOX_API_KEY

# Install dependencies

pip install -r requirements.txt

cd frontend && npm install && cd ..

# Start the application

./start-dev.sh

```

- **🌐 Access the application:**
- **Main App**: http://localhost:3000

## 🎮 Usage

### **Socratic Chat**

1. Navigate to http://localhost:3000 → "IDE" tab

2. Ask programming questions in the chat panel

### **Manager Dashboard**

- Switch to "Manager" view in the top navigation
- Track team progress, skills acquired, and learning analytics
- Filter and search through junior developers' metrics

### **Flashcards**

- Access via "Revises" tab
- Auto-generated cards based on your conversations
- Adaptive difficulty with spaced repetition algorithm

### **Landing Page**

Run `./open-landing-page.sh` to automatically open the landing page and see the product value

**## 🏗️ Project Structure**

```

socrate-mentor-ia/

├── frontend/                    # React + TypeScript UI

│   ├── src/components/         # UI components

│   └── package.json

├── backend/                    # FastAPI Python server

│   ├── api.py                 # Main API server

│   ├── main.py                # Blackbox AI integration

│   └── database_operations.py # Database layer

├── landing_page/              # Static landing page

│   ├── index.html            # Main landing page

│   ├── styles.css            # Styling

│   └── script.js             # Interactive features

├── agents/                    # AI prompts and configurations

├── tests/                     # Test suite

├── start-dev.sh              # Development startup script

├── open-landing-page.sh      # Landing page opener script

└── requirements.txt          # Python dependencies

```
