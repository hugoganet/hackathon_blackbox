import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ProgressDataPoint } from '../../types';

interface ProgressChartProps {
  data: ProgressDataPoint[];
}

const ProgressChart: React.FC<ProgressChartProps> = ({ data }) => {
  // Format data for the chart
  const chartData = data.map((point, index) => ({
    ...point,
    day: `Day ${index + 1}`,
    date: new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="text-sm font-medium text-gray-900 mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-xs" style={{ color: entry.color }}>
              {entry.name}: {entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="h-32 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="date"
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 10, fill: '#6b7280' }}
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 10, fill: '#6b7280' }}
            width={20}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="skillsLearned"
            stroke="#10b981"
            strokeWidth={2}
            dot={{ fill: '#10b981', strokeWidth: 0, r: 3 }}
            name="Skills Learned"
          />
          <Line
            type="monotone"
            dataKey="questionsAsked"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ fill: '#3b82f6', strokeWidth: 0, r: 3 }}
            name="Questions Asked"
          />
          <Line
            type="monotone"
            dataKey="mistakesMade"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={{ fill: '#f59e0b', strokeWidth: 0, r: 3 }}
            name="Mistakes Made"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ProgressChart;
