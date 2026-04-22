// This file contains TypeScript type definitions used throughout the project.

declare module '*.png' {
  const content: string;
  export default content;
}

declare module '*.jpg' {
  const content: string;
  export default content;
}

declare module '*.jpeg' {
  const content: string;
  export default content;
}

declare module '*.gif' {
  const content: string;
  export default content;
}

declare module '*.glb' {
  const content: string;
  export default content;
}

declare module '*.gltf' {
  const content: string;
  export default content;
}

interface FoodItem {
  id: string;
  name: string;
  image: string;
  category: string;
}

interface Prediction {
  foodItem: FoodItem;
  label: string;
  confidence: number;
}

interface SceneProps {
  onScroll: (scrollY: number) => void;
}

interface DashboardData {
  totalFoodWaste: number;
  totalCO2Impact: number;
  predictions: Prediction[];
}