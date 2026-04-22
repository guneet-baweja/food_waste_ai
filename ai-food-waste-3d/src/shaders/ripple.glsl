void main() {
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    float time = iTime * 0.5;

    // Create ripple effect
    float dist = length(uv - 0.5);
    float ripple = sin(dist * 10.0 - time * 5.0) * 0.05;

    // Set color based on ripple
    vec3 color = vec3(0.0, 0.5 + ripple, 1.0 - ripple);

    gl_FragColor = vec4(color, 1.0);
}