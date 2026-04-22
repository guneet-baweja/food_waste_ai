import React from 'react';
import { Canvas } from '@react-three/fiber';
import SceneManager from './scenes/SceneManager';
import './index.css';

const App: React.FC = () => {
  return (
    <div className="App">
      <Canvas>
        <SceneManager />
      </Canvas>
    </div>
  );
};

export default App;