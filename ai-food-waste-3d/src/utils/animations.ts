import { gsap } from 'gsap';

// Function to create a fade-in animation
export const fadeIn = (element: HTMLElement, duration: number = 1) => {
  gsap.fromTo(element, { opacity: 0 }, { opacity: 1, duration });
};

// Function to create a slide-in animation
export const slideIn = (element: HTMLElement, direction: 'left' | 'right' | 'top' | 'bottom', duration: number = 1) => {
  const distance = direction === 'left' ? '-100%' : direction === 'right' ? '100%' : direction === 'top' ? '-100%' : '100%';
  gsap.fromTo(element, { x: direction === 'left' || direction === 'right' ? distance : 0, y: direction === 'top' || direction === 'bottom' ? distance : 0, opacity: 0 }, { x: 0, y: 0, opacity: 1, duration });
};

// Function to create a scale animation
export const scaleUp = (element: HTMLElement, duration: number = 1) => {
  gsap.fromTo(element, { scale: 0 }, { scale: 1, duration });
};

// Function to create a rotation animation
export const rotate = (element: HTMLElement, duration: number = 1, angle: number = 360) => {
  gsap.to(element, { rotation: angle, duration });
};

// Function to create a bounce effect
export const bounce = (element: HTMLElement, duration: number = 1) => {
  gsap.fromTo(element, { scale: 0.5 }, { scale: 1, duration, ease: 'bounce.out' });
};