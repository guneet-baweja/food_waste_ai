import React, { useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import ParticlesSystem from '../systems/ParticlesSystem';
import VolumetricFog from '../systems/VolumetricFog';
import NebulaGPU from '../systems/NebulaGPU';
import GeometryField from '../systems/GeometryField';

const BackgroundSystem: React.FC = () => {
  useEffect(() => {
    // Initialize any necessary systems or effects here
  }, []);

  return (
    <Canvas>
      <ParticlesSystem />
      <VolumetricFog />
      <NebulaGPU />
      <GeometryField />
    </Canvas>
  );
};

export default BackgroundSystem;