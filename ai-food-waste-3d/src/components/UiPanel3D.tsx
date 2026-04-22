import React from 'react';
import { Canvas } from '@react-three/fiber';
import { useFrame } from '@react-three/fiber';

const UiPanel3D = () => {
  // State for panel rotation
  const panelRef = React.useRef();

  // Animation loop for panel rotation
  useFrame(() => {
    if (panelRef.current) {
      panelRef.current.rotation.y += 0.01; // Rotate the panel
    }
  });

  return (
    <mesh ref={panelRef} position={[0, 0, -5]}>
      <planeBufferGeometry args={[3, 2]} />
      <meshStandardMaterial color="rgba(255, 255, 255, 0.1)" transparent={true} />
      <mesh>
        <textGeometry args={['AI Powered Food Waste Management', { font: 'helvetiker', size: 0.5, height: 0.1 }]} />
        <meshStandardMaterial color="white" />
      </mesh>
    </mesh>
  );
};

export default UiPanel3D;