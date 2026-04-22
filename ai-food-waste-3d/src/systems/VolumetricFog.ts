import * as THREE from 'three';

export class VolumetricFog {
    constructor(scene) {
        this.scene = scene;
        this.fogMaterial = this.createFogMaterial();
        this.fogMesh = this.createFogMesh();
        this.scene.add(this.fogMesh);
    }

    createFogMaterial() {
        const fogShader = `
            uniform float time;
            varying vec2 vUv;
            void main() {
                vec3 fogColor = vec3(0.0, 1.0, 0.0); // Green fog color
                float fogDensity = 0.1; // Adjust fog density
                float fogFactor = exp(-fogDensity * length(gl_FragCoord.xy));
                gl_FragColor = vec4(fogColor, fogFactor);
            }
        `;

        return new THREE.ShaderMaterial({
            uniforms: {
                time: { value: 0 }
            },
            vertexShader: `
                varying vec2 vUv;
                void main() {
                    vUv = uv;
                    vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
                    gl_Position = projectionMatrix * mvPosition;
                }
            `,
            fragmentShader: fogShader,
            transparent: true,
            depthWrite: false,
        });
    }

    createFogMesh() {
        const geometry = new THREE.PlaneGeometry(200, 200);
        const mesh = new THREE.Mesh(geometry, this.fogMaterial);
        mesh.rotation.x = -Math.PI / 2; // Rotate to horizontal
        return mesh;
    }

    update(time) {
        this.fogMaterial.uniforms.time.value = time;
    }
}