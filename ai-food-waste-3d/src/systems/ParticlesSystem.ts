import * as THREE from 'three';

export class ParticlesSystem {
    constructor(scene) {
        this.scene = scene;
        this.particleCount = 1000;
        this.particles = new THREE.BufferGeometry();
        this.positions = new Float32Array(this.particleCount * 3);
        this.colors = new Float32Array(this.particleCount * 3);
        this.initParticles();
        this.createParticleMaterial();
        this.createParticleMesh();
    }

    initParticles() {
        for (let i = 0; i < this.particleCount; i++) {
            this.positions.set([
                (Math.random() - 0.5) * 100,
                (Math.random() - 0.5) * 100,
                (Math.random() - 0.5) * 100
            ], i * 3);

            this.colors.set([
                Math.random(),
                Math.random(),
                Math.random()
            ], i * 3);
        }

        this.particles.setAttribute('position', new THREE.BufferAttribute(this.positions, 3));
        this.particles.setAttribute('color', new THREE.BufferAttribute(this.colors, 3));
    }

    createParticleMaterial() {
        this.material = new THREE.PointsMaterial({
            size: 0.5,
            vertexColors: true,
            transparent: true,
            opacity: 0.7
        });
    }

    createParticleMesh() {
        this.particleMesh = new THREE.Points(this.particles, this.material);
        this.scene.add(this.particleMesh);
    }

    update() {
        const positions = this.particles.attributes.position.array;

        for (let i = 0; i < this.particleCount; i++) {
            positions[i * 3 + 1] -= 0.1; // Move particles down
            if (positions[i * 3 + 1] < -50) {
                positions[i * 3 + 1] = 50; // Reset position
            }
        }

        this.particles.attributes.position.needsUpdate = true; // Notify Three.js to update the positions
    }
}