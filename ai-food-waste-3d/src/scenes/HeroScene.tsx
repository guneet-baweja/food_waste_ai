import React, { useEffect, useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { useScroll } from '@react-three/drei';
import { gsap } from 'gsap';

const HeroScene = () => {
  const earthRef = useRef();
  const { scrollYProgress } = useScroll();

  useEffect(() => {
    const tl = gsap.timeline({
      scrollTrigger: {
        trigger: '.hero-section',
        start: 'top top',
        end: 'bottom top',
        scrub: true,
      },
    });

    tl.to(earthRef.current.rotation, { y: Math.PI * 2, duration: 1 })
      .to(earthRef.current.position, { z: -5, duration: 1 }, '<')
      .fromTo('.ui-panel', { opacity: 0, y: 50 }, { opacity: 1, y: 0, duration: 1 }, '<');

    return () => {
      tl.kill();
    };
  }, [scrollYProgress]);

  return (
    <Canvas>
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} />
      <mesh ref={earthRef} rotation={[0, 0, 0]}>
        <sphereGeometry args={[1, 32, 32]} />
        <meshStandardMaterial map={new THREE.TextureLoader().load('/assets/images/hero-globe.png')} />
      </mesh>
      <div className="ui-panel">
        {/* Floating UI Panels */}
      </div>
    </Canvas>
  );
};

export default HeroScene;