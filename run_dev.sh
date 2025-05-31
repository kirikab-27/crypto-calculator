#!/bin/bash

# Development startup script for Crypto Calculator
# This script starts both the backend and frontend servers

echo "Starting Crypto Calculator Development Servers..."
echo "============================================="

# Function to cleanup on exit
cleanup() {
    echo -e "\n\nStopping servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

# Set trap to cleanup on Ctrl+C
trap cleanup INT

# Start backend server
echo "Starting backend server on http://localhost:8000..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 3

# Start frontend server
echo "Starting frontend server on http://localhost:3000..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo -e "\n============================================="
echo "Both servers are running!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "Backend API docs: http://localhost:8000/docs"
echo -e "\nPress Ctrl+C to stop both servers"
echo "============================================="

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID