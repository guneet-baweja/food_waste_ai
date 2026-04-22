import * as THREE from 'three';

export const loadTexture = (url: string): Promise<THREE.Texture> => {
    return new Promise((resolve, reject) => {
        const loader = new THREE.TextureLoader();
        loader.load(
            url,
            (texture) => {
                resolve(texture);
            },
            undefined,
            (error) => {
                reject(error);
            }
        );
    });
};

export const loadGLTFModel = (url: string): Promise<THREE.Group> => {
    return new Promise((resolve, reject) => {
        const loader = new THREE.GLTFLoader();
        loader.load(
            url,
            (gltf) => {
                resolve(gltf.scene);
            },
            undefined,
            (error) => {
                reject(error);
            }
        );
    });
};

export const loadFont = (url: string): Promise<THREE.Font> => {
    return new Promise((resolve, reject) => {
        const loader = new THREE.FontLoader();
        loader.load(
            url,
            (font) => {
                resolve(font);
            },
            undefined,
            (error) => {
                reject(error);
            }
        );
    });
};