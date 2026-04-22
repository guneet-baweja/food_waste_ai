import React, { useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { useScroll } from '@react-three/drei';
import GlassCard from '../components/GlassCard';
import UiPanel3D from '../components/UiPanel3D';
import { useMouseInteraction } from '../hooks/useMouseInteraction';
import { useScrollTimeline } from '../hooks/useScrollTimeline';

const ProductScene = () => {
  const { scrollYProgress } = useScroll();
  const { handleMouseMove } = useMouseInteraction();
  const { timeline } = useScrollTimeline();

  useEffect(() => {
    const unsubscribe = scrollYProgress.onChange(() => {
      // Update animations based on scroll position
      timeline.update(scrollYProgress.get());
    });

    return () => unsubscribe();
  }, [scrollYProgress, timeline]);

  return (
    <Canvas onMouseMove={handleMouseMove}>
      {/* Background and other scene elements can be added here */}
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} />
      
      {/* Example of a rotating product card */}
      <GlassCard position={[-1.5, 0, 0]} />
      <GlassCard position={[1.5, 0, 0]} rotation={[0, Math.PI / 4, 0]} />
      
      {/* 3D UI panels */}
      <UiPanel3D position={[0, 1, -2]} />
    </Canvas>
  );
};

export default ProductScene;