import React, { useEffect, useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { useScrollTimeline } from '../hooks/useScrollTimeline';
import { ParticlesSystem } from '../systems/ParticlesSystem';
import { VolumetricFog } from '../systems/VolumetricFog';
import { GeometryField } from '../systems/GeometryField';
import { useMouseInteraction } from '../hooks/useMouseInteraction';
import { Brain } from '../components/Brain'; // Assuming a Brain component is created for the neural visualization

const BrainScene = () => {
  const canvasRef = useRef(null);
  const { scrollRef } = useScrollTimeline();
  const { handleMouseMove } = useMouseInteraction();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas) {
      // Initialize systems
      const particles = new ParticlesSystem(canvas);
      const fog = new VolumetricFog(canvas);
      const geometryField = new GeometryField(canvas);

      // Cleanup on unmount
      return () => {
        particles.dispose();
        fog.dispose();
        geometryField.dispose();
      };
    }
  }, []);

  return (
    <div ref={scrollRef} onMouseMove={handleMouseMove}>
      <Canvas ref={canvasRef} style={{ height: '100vh', width: '100vw' }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
        <Brain />
        {/* Add other components or systems as needed */}
      </Canvas>
    </div>
  );
};

export default BrainScene;