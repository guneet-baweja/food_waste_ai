import React from 'react';

const Loader: React.FC = () => {
  return (
    <div className="loader">
      <div className="loader-content">
        <div className="loader-globe">
          <div className="globe-ring ring1"></div>
          <div className="globe-ring ring2"></div>
          <div className="globe-ring ring3"></div>
          <div className="loader-brand">Loading...</div>
        </div>
        <div className="loader-bar-wrap">
          <div className="loader-bar-fill"></div>
        </div>
        <div className="loader-text">Please wait while we prepare your experience.</div>
      </div>
    </div>
  );
};

export default Loader;