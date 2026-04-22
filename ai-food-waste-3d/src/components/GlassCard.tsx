import React from 'react';

interface GlassCardProps {
  title: string;
  description: string;
  image: string;
}

const GlassCard: React.FC<GlassCardProps> = ({ title, description, image }) => {
  return (
    <div className="glass-card">
      <img src={image} alt={title} className="glass-card-image" />
      <div className="glass-card-content">
        <h3 className="glass-card-title">{title}</h3>
        <p className="glass-card-description">{description}</p>
      </div>
    </div>
  );
};

export default GlassCard;