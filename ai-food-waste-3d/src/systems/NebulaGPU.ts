import * as THREE from 'three';

export class NebulaGPU {
    constructor(scene) {
        this.scene = scene;
        this.particleCount = 10000;
        this.particles = null;
        this.geometry = null;
        this.material = null;
        this.init();
    }

    init() {
        this.geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(this.particleCount * 3);
        const colors = new Float32Array(this.particleCount * 3);
        const sizes = new Float32Array(this.particleCount);

        for (let i = 0; i < this.particleCount; i++) {
            positions.set([Math.random() * 200 - 100, Math.random() * 200 - 100, Math.random() * 200 - 100], i * 3);
            colors.set([Math.random(), Math.random(), Math.random()], i * 3);
            sizes[i] = Math.random() * 5;
        }

        this.geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        this.geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        this.geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

        this.material = new THREE.ShaderMaterial({
            vertexShader: this.getVertexShader(),
            fragmentShader: this.getFragmentShader(),
            depthWrite: false,
            transparent: true,
            blending: THREE.AdditiveBlending,
        });

        this.particles = new THREE.Points(this.geometry, this.material);
        this.scene.add(this.particles);
    }

    getVertexShader() {
        return `
            attribute float size;
            varying vec3 vColor;

            void main() {
                vColor = color;
                vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
                gl_PointSize = size * (300.0 / -mvPosition.z);
                gl_Position = projectionMatrix * mvPosition;
            }
        `;
    }

    getFragmentShader() {
        return `
            varying vec3 vColor;

            void main() {
                gl_FragColor = vec4(vColor, 1.0);
            }
        `;
    }

    update() {
        // Update logic for nebula particles can be added here
    }
}