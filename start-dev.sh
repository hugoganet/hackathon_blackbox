#!/bin/bash

# Dev Mentor AI - Development Start Script
# Starts both backend and frontend in development mode

echo "🚀 Starting Dev Mentor AI Development Environment..."
echo "================================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+"
    exit 1
fi

# Check if Node is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+"
    exit 1
fi

# Function to kill processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    # Kill any remaining processes on common dev ports
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    lsof -ti:3001 | xargs kill -9 2>/dev/null || true
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    exit 0
}

# Set up trap to catch exit signals
trap cleanup EXIT INT TERM

# Clean up any existing processes on dev ports
echo "🧹 Cleaning up existing processes..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:3001 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Start Backend
echo ""
echo "📦 Starting Backend API..."
echo "------------------------"
python3 backend/api.py &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"
echo "   URL: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"

# Wait for backend to be ready
echo ""
echo "⏳ Waiting for backend to be ready..."
sleep 3

# Check if backend is responding
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is ready!"
else
    echo "⚠️  Backend might not be fully ready yet"
fi

# Start Frontend
echo ""
echo "📦 Starting Frontend..."
echo "---------------------"
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Start frontend dev server
npm run dev &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID)"
echo "   URL: http://localhost:3000"

echo ""
echo "================================================"
echo "✨ Dev Mentor AI is running!"
echo ""
echo "📍 Access points:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo "================================================"

# Wait for interrupt
wait