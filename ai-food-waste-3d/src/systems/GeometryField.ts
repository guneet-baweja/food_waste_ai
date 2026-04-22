import * as THREE from 'three';

export class GeometryField {
    constructor(scene) {
        this.scene = scene;
        this.geometry = new THREE.BoxGeometry(1, 1, 1);
        this.material = new THREE.MeshStandardMaterial({ color: 0x00ff00, wireframe: true });
        this.mesh = new THREE.Mesh(this.geometry, this.material);
        this.scene.add(this.mesh);
        this.rotationSpeed = 0.01;
    }

    update() {
        this.mesh.rotation.x += this.rotationSpeed;
        this.mesh.rotation.y += this.rotationSpeed;
    }

    setRotationSpeed(speed) {
        this.rotationSpeed = speed;
    }

    dispose() {
        this.scene.remove(this.mesh);
        this.geometry.dispose();
        this.material.dispose();
    }
}