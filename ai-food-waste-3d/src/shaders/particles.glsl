void main() {
    // Particle shader code
    // Define the varying variables for position and color
    varying vec3 vPosition;
    varying vec3 vColor;

    void main() {
        // Set the position of the particle
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        
        // Set the size of the particle based on its distance from the camera
        gl_PointSize = 100.0 / -gl_Position.z;

        // Set the color of the particle
        vColor = color;
    }

    void fragmentShader() {
        // Set the output color of the particle
        gl_FragColor = vec4(vColor, 1.0);
    }
}