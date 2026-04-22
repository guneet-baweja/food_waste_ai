import React, { useEffect, useRef } from 'react';

const Cursor: React.FC = () => {
    const cursorRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        const handleMouseMove = (event: MouseEvent) => {
            if (cursorRef.current) {
                cursorRef.current.style.transform = `translate3d(${event.clientX}px, ${event.clientY}px, 0)`;
            }
        };

        const handleMouseEnter = () => {
            if (cursorRef.current) {
                cursorRef.current.classList.add('hover');
            }
        };

        const handleMouseLeave = () => {
            if (cursorRef.current) {
                cursorRef.current.classList.remove('hover');
            }
        };

        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('mouseenter', handleMouseEnter);
        window.addEventListener('mouseleave', handleMouseLeave);

        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseenter', handleMouseEnter);
            window.removeEventListener('mouseleave', handleMouseLeave);
        };
    }, []);

    return (
        <div ref={cursorRef} className="custom-cursor"></div>
    );
};

export default Cursor;