void main() {
    // Define the fog color and density
    vec3 fogColor = vec3(0.1, 0.1, 0.1); // Dark fog color
    float fogDensity = 0.05; // Density of the fog

    // Calculate the distance from the camera to the fragment
    float distance = length(gl_FragCoord.xyz);

    // Calculate fog factor based on distance
    float fogFactor = exp(-fogDensity * distance);
    fogFactor = clamp(fogFactor, 0.0, 1.0);

    // Mix the fragment color with the fog color based on the fog factor
    vec4 color = texture2D(u_texture, v_texCoord);
    color.rgb = mix(color.rgb, fogColor, 1.0 - fogFactor);

    gl_FragColor = color;
}