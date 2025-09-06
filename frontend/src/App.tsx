import React from 'react';
import Header from './components/Layout/Header';
import ChatInterface from './components/Chat/ChatInterface';

function App() {
  // In a real app, you might get user ID from authentication
  const userId = 'demo-user';

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />
      
      <main className="flex-1 container mx-auto px-4 py-6 safe-area-bottom">
        <div className="max-w-5xl mx-auto">
          {/* Welcome Section */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Welcome to Dev Mentor AI
            </h1>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Get personalized mentoring from AI agents designed to help you learn and grow as a developer. 
              Choose between comprehensive guidance or discovery-based learning.
            </p>
          </div>

          {/* Chat Interface */}
          <ChatInterface userId={userId} />
        </div>
      </main>

      {/* Skip link for accessibility */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
    </div>
  );
}

export default App;