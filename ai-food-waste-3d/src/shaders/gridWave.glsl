uniform float u_time;
uniform vec2 u_resolution;

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution.xy;
    uv = uv * 2.0 - 1.0; // Normalize to [-1, 1]
    uv.x *= u_resolution.x / u_resolution.y; // Correct aspect ratio

    float wave = sin(uv.y * 10.0 + u_time * 5.0) * 0.1; // Wave effect
    uv.y += wave;

    // Create a grid pattern
    float grid = step(0.05, abs(sin(uv.x * 10.0))) * step(0.05, abs(sin(uv.y * 10.0)));

    // Set the color based on the grid
    vec3 color = mix(vec3(0.0, 0.0, 0.0), vec3(0.0, 1.0, 0.0), grid);

    gl_FragColor = vec4(color, 1.0);
}