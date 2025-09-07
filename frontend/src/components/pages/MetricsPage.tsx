import React, { useState, useEffect } from 'react';
import { JuniorMetrics, LoadingState, ErrorState } from '../../types';
import { apiService } from '../../services/api';
import MetricsCard from '../metrics/MetricsCard';
import SearchFilter from '../metrics/SearchFilter';
import { Users, TrendingUp, Clock, Target } from 'lucide-react';

interface MetricsPageProps {
  viewType: 'junior' | 'manager';
}

const MetricsPage: React.FC<MetricsPageProps> = ({ viewType }) => {
  const [metrics, setMetrics] = useState<JuniorMetrics[]>([]);
  const [filteredMetrics, setFilteredMetrics] = useState<JuniorMetrics[]>([]);
  const [loading, setLoading] = useState<LoadingState>({ isLoading: true });
  const [error, setError] = useState<ErrorState>({ hasError: false });
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadMetrics();
  }, []);

  useEffect(() => {
    // Filter metrics based on search term
    if (searchTerm.trim()) {
      const filtered = metrics.filter(junior =>
        junior.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        junior.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        junior.skillsAcquired.some(skill =>
          skill.toLowerCase().includes(searchTerm.toLowerCase())
        )
      );
      setFilteredMetrics(filtered);
    } else {
      setFilteredMetrics(metrics);
    }
  }, [searchTerm, metrics]);

  const loadMetrics = async () => {
    setLoading({ isLoading: true, message: 'Loading junior metrics...' });
    setError({ hasError: false });

    try {
      const data = await apiService.getDashboardMetrics();
      setMetrics(data);
      setFilteredMetrics(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load metrics';
      setError({ hasError: true, message: errorMessage });
    } finally {
      setLoading({ isLoading: false });
    }
  };

  // Calculate summary statistics
  const summaryStats = React.useMemo(() => {
    if (filteredMetrics.length === 0) {
      return {
        totalJuniors: 0,
        averageSkills: 0,
        totalSessions: 0,
        averageSessionTime: 0
      };
    }

    if (viewType === 'junior') {
      // For junior view, show only current user's stats
      const userMetrics = filteredMetrics[0]; // Assuming first item is current user
      return {
        totalJuniors: 1,
        averageSkills: userMetrics.skillsAcquired.length,
        totalSessions: userMetrics.totalSessions,
        averageSessionTime: userMetrics.averageSessionTime
      };
    }

    const totalSessions = filteredMetrics.reduce((sum, junior) => sum + junior.totalSessions, 0);
    const totalSkills = filteredMetrics.reduce((sum, junior) => sum + junior.skillsAcquired.length, 0);
    const totalSessionTime = filteredMetrics.reduce((sum, junior) => sum + junior.averageSessionTime, 0);

    return {
      totalJuniors: filteredMetrics.length,
      averageSkills: Math.round(totalSkills / filteredMetrics.length),
      totalSessions,
      averageSessionTime: Math.round(totalSessionTime / filteredMetrics.length)
    };
  }, [filteredMetrics, viewType]);

  if (loading.isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">{loading.message}</p>
        </div>
      </div>
    );
  }

  if (error.hasError) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Metrics</h2>
          <p className="text-gray-600 mb-4">{error.message}</p>
          <button
            onClick={loadMetrics}
            className="btn-primary"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {viewType === 'junior' ? 'My Progress' : 'Manager Dashboard'}
          </h1>
          <p className="text-gray-600">
            {viewType === 'junior'
              ? 'Track your learning progress and achievements'
              : 'Track progress and performance of junior developers'
            }
          </p>
        </div>

        {/* Summary Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Juniors</p>
                <p className="text-2xl font-bold text-gray-900">{summaryStats.totalJuniors}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <Target className="w-6 h-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Avg Skills/Junior</p>
                <p className="text-2xl font-bold text-gray-900">{summaryStats.averageSkills}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <TrendingUp className="w-6 h-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Sessions</p>
                <p className="text-2xl font-bold text-gray-900">{summaryStats.totalSessions}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 rounded-lg">
                <Clock className="w-6 h-6 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Avg Session Time</p>
                <p className="text-2xl font-bold text-gray-900">{summaryStats.averageSessionTime}m</p>
              </div>
            </div>
          </div>
        </div>

        {/* Search and Filter - Only show for Manager view */}
        {viewType === 'manager' && (
          <div className="mb-6">
            <SearchFilter
              searchTerm={searchTerm}
              onSearchChange={setSearchTerm}
              placeholder="Search by name, email, or skills..."
            />
          </div>
        )}

        {/* Metrics Grid */}
        {filteredMetrics.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 text-6xl mb-4">📊</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {viewType === 'junior'
                ? 'No progress data available'
                : searchTerm ? 'No matching juniors found' : 'No junior developers yet'
              }
            </h3>
            <p className="text-gray-600">
              {viewType === 'junior'
                ? 'Start using the mentor system to track your progress'
                : searchTerm
                  ? 'Try adjusting your search terms'
                  : 'Junior developers will appear here once they start using the mentor system'
              }
            </p>
          </div>
        ) : (
          <div className={`grid gap-6 ${viewType === 'junior' ? 'grid-cols-1 max-w-4xl mx-auto' : 'grid-cols-1 lg:grid-cols-2 xl:grid-cols-3'}`}>
            {(viewType === 'junior' ? filteredMetrics.slice(0, 1) : filteredMetrics).map((junior) => (
              <MetricsCard key={junior.id} junior={junior} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MetricsPage;
