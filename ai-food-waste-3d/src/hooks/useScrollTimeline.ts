import { useEffect, useRef } from 'react';

const useScrollTimeline = (callback: (progress: number) => void) => {
    const scrollRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        const handleScroll = () => {
            if (scrollRef.current) {
                const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
                const progress = scrollTop / (scrollHeight - clientHeight);
                callback(progress);
            }
        };

        const currentRef = scrollRef.current;
        if (currentRef) {
            currentRef.addEventListener('scroll', handleScroll);
        }

        return () => {
            if (currentRef) {
                currentRef.removeEventListener('scroll', handleScroll);
            }
        };
    }, [callback]);

    return scrollRef;
};

export default useScrollTimeline;