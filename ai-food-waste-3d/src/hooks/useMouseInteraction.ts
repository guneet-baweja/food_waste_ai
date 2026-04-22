import { useEffect, useRef } from 'react';

const useMouseInteraction = () => {
  const mousePosition = useRef({ x: 0, y: 0 });
  const mouseDown = useRef(false);

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      mousePosition.current = { x: event.clientX, y: event.clientY };
      // Add logic for mouse movement interactions here
    };

    const handleMouseDown = () => {
      mouseDown.current = true;
      // Add logic for mouse down interactions here
    };

    const handleMouseUp = () => {
      mouseDown.current = false;
      // Add logic for mouse up interactions here
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  return { mousePosition: mousePosition.current, mouseDown: mouseDown.current };
};

export default useMouseInteraction;