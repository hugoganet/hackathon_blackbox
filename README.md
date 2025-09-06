# Dev Mentor AI

AI-powered mentoring system for junior developers with an intuitive chat interface. Features dual AI agents (normal and strict mentoring modes) with conversation memory and learning pattern analysis.

## 🚀 Quick Start

### Fastest Setup (Development)

```bash
# 1. Clone and setup
git clone <your-repo>
cd dev_mentor_ai

# 2. Configure environment
cp .env.example .env
# Edit .env and add your BLACKBOX_API_KEY

# 3. Start everything (backend + frontend)
./start-dev.sh
```

Open http://localhost:3000 and start chatting with your AI mentor!

## ✨ Features

- **🤖 Dual Agent System**: Choose between comprehensive answers or guided discovery learning
- **💬 Modern Chat Interface**: Clean, responsive React UI with real-time messaging
- **🧠 Conversation Memory**: Vector-based memory system that remembers past interactions
- **📊 Learning Analytics**: Track progress and identify knowledge patterns
- **🎨 Beautiful Design**: Follows comprehensive UI/UX guidelines
- **♿ Accessible**: WCAG AA compliant with keyboard navigation
- **📱 Responsive**: Works seamlessly on desktop, tablet, and mobile

## 🏗️ Architecture

### Frontend (React + TypeScript)
- Modern React 18 with hooks
- TypeScript for type safety
- Tailwind CSS following design system
- Vite for fast development
- Fully responsive and accessible

### Backend (FastAPI + PostgreSQL)
- FastAPI for high-performance REST API
- PostgreSQL for data persistence
- ChromaDB for vector similarity search
- Blackbox AI integration (Claude Sonnet 4)
- SQLAlchemy ORM with async support

## 📦 Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- Blackbox AI API key ([get one here](https://blackbox.ai/api))

### Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Add your BLACKBOX_API_KEY to .env

# Run the backend
python3 api.py
```

Backend runs on http://localhost:8000
API docs available at http://localhost:8000/docs

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs on http://localhost:3000

## 🎯 Usage

### Choose Your Mentor

1. **Normal Mentor Agent**: Provides complete answers with detailed explanations and code examples. Perfect when you need comprehensive guidance quickly.

2. **Strict Mentor Agent**: Never gives direct answers! Guides you through Socratic questioning and progressive hints. Ideal for deep learning and building problem-solving skills.

### API Endpoints

- `POST /chat` - Send messages to mentor agents
- `GET /agents` - List available mentor types
- `GET /health` - System health check
- `GET /stats` - Usage statistics
- `GET /user/{user_id}/memories` - User's learning patterns

### Example Chat Request

```json
{
  "message": "How do I handle errors in React?",
  "agent_type": "strict",
  "user_id": "developer123"
}
```

## 🚢 Production Deployment

### Railway (Recommended)

```bash
# Push to GitHub
git add .
git commit -m "Deploy to Railway"
git push origin main

# Connect GitHub repo on railway.app
# Add environment variable: BLACKBOX_API_KEY
# Deploy automatically via Procfile
```

### Frontend on Vercel

```bash
cd frontend
npm run build
# Deploy dist folder to Vercel
```

## 📁 Project Structure

```
dev_mentor_ai/
├── frontend/                  # React frontend application
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── hooks/           # Custom React hooks
│   │   ├── services/        # API integration
│   │   └── types/           # TypeScript types
│   └── package.json
├── api.py                    # FastAPI backend server
├── main.py                   # Core Blackbox integration
├── database.py               # PostgreSQL models
├── memory_store.py           # ChromaDB vector store
├── agent-mentor.md           # Normal agent prompt
├── agent-mentor-strict.md    # Strict agent prompt
├── start-dev.sh             # Development start script
└── requirements.txt          # Python dependencies
```

## 🎨 Design System

The frontend follows comprehensive UI guidelines with:
- **Typography**: Inter (primary) and JetBrains Mono (code)
- **Colors**: Primary blue (#0066FF), semantic colors for states
- **Spacing**: 8px grid system
- **Components**: Consistent elevation, border radius, and interactions
- **Accessibility**: WCAG AA compliance, keyboard navigation

## 🧪 Testing

```bash
# Backend tests
pytest tests/ -v

# Frontend tests (coming soon)
cd frontend && npm test
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the coding standards (PEP 8 for Python, ESLint for TypeScript)
4. Ensure all tests pass
5. Submit a pull request

## 📝 License

See LICENSE file for details.

## 🙏 Acknowledgments

- Powered by Blackbox AI and Claude Sonnet 4
- Built with FastAPI, React, and modern web technologies
- Designed following industry-standard UI/UX principles