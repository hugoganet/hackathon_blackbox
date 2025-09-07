import React, { useState } from 'react';
import { TabType } from '../types';
import Navbar from './Navbar';
import MentorPage from './pages/MentorPage';
import MetricsPage from './pages/MetricsPage';
import QuizzesPage from './pages/QuizzesPage';

type ViewType = 'junior' | 'manager';

const Layout: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('mentor');
  const [viewType, setViewType] = useState<ViewType>('junior');

  const renderContent = () => {
    // Manager view only shows metrics dashboards
    if (viewType === 'manager') {
      return <MetricsPage viewType={viewType} />;
    }

    // Junior view shows all tabs
    switch (activeTab) {
      case 'mentor':
        return <MentorPage />;
      case 'metrics':
        return <MetricsPage viewType={viewType} />;
      case 'quizzes':
        return <QuizzesPage />;
      default:
        return <MentorPage />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        viewType={viewType}
        onViewChange={setViewType}
      />
      <main className="pt-16">
        {renderContent()}
      </main>
    </div>
  );
};

export default Layout;
