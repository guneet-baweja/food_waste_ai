// GLSL shader code for distortion effects
uniform float time;
uniform vec2 resolution;

vec2 warp(vec2 uv) {
    float wave = sin(uv.y * 10.0 + time * 5.0) * 0.05;
    return vec2(uv.x + wave, uv.y);
}

void main() {
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    uv = warp(uv);
    
    // Sample the texture
    vec4 color = texture2D(u_texture, uv);
    
    gl_FragColor = color;
}