import React, { useState, useEffect } from 'react';
import HeroScene from './HeroScene';
import BrainScene from './BrainScene';
import CityScene from './CityScene';
import ProductScene from './ProductScene';
import BackgroundSystem from './BackgroundSystem';

const SceneManager = () => {
    const [currentScene, setCurrentScene] = useState('hero');

    const handleScroll = () => {
        const scrollPosition = window.scrollY;
        if (scrollPosition < window.innerHeight) {
            setCurrentScene('hero');
        } else if (scrollPosition < window.innerHeight * 2) {
            setCurrentScene('brain');
        } else if (scrollPosition < window.innerHeight * 3) {
            setCurrentScene('city');
        } else {
            setCurrentScene('product');
        }
    };

    useEffect(() => {
        window.addEventListener('scroll', handleScroll);
        return () => {
            window.removeEventListener('scroll', handleScroll);
        };
    }, []);

    return (
        <>
            <BackgroundSystem />
            {currentScene === 'hero' && <HeroScene />}
            {currentScene === 'brain' && <BrainScene />}
            {currentScene === 'city' && <CityScene />}
            {currentScene === 'product' && <ProductScene />}
        </>
    );
};

export default SceneManager;