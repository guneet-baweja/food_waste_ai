import React from 'react';
import GlassCard from './GlassCard';

const FloatingDashboard: React.FC = () => {
  return (
    <div className="floating-dashboard">
      <GlassCard title="AI Insights" content="Real-time data analysis and predictions." />
      <GlassCard title="Food Waste Stats" content="Track your food waste and impact." />
      <GlassCard title="Recommendations" content="Get personalized suggestions to reduce waste." />
    </div>
  );
};

export default FloatingDashboard;