/**
 * FoodSave AI — Background Particle System
 * Phase 1: Floating particles on Three.js canvas
 */
window.ParticleSystem = (function () {

  let scene, camera, renderer, particles, animId;

  function init() {
    const canvas = document.getElementById('mainCanvas');
    if (!canvas || typeof THREE === 'undefined') return;

    // Scene
    scene = new THREE.Scene();

    // Camera
    camera = new THREE.PerspectiveCamera(
      75, window.innerWidth / window.innerHeight, 0.1, 1000
    );
    camera.position.z = 30;

    // Renderer
    renderer = new THREE.WebGLRenderer({
      canvas, alpha: true, antialias: true
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);

    createParticles();
    createGridPlane();
    animate();

    window.addEventListener('resize', onResize);
  }

  function createParticles() {
    const count = 1500;
    const positions = new Float32Array(count * 3);
    const colors    = new Float32Array(count * 3);
    const sizes     = new Float32Array(count);

    const palette = [
      new THREE.Color(0x00ff88),
      new THREE.Color(0x00d4ff),
      new THREE.Color(0xb48eff),
      new THREE.Color(0xffd93d)
    ];

    for (let i = 0; i < count; i++) {
      positions[i * 3]     = (Math.random() - 0.5) * 120;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 80;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 60;

      const c = palette[Math.floor(Math.random() * palette.length)];
      colors[i * 3]     = c.r;
      colors[i * 3 + 1] = c.g;
      colors[i * 3 + 2] = c.b;

      sizes[i] = Math.random() * 2 + 0.5;
    }

    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geo.setAttribute('color',    new THREE.BufferAttribute(colors, 3));
    geo.setAttribute('size',     new THREE.BufferAttribute(sizes, 1));

    const mat = new THREE.ShaderMaterial({
      uniforms: { time: { value: 0 } },
      vertexShader: `
        attribute float size;
        attribute vec3 color;
        varying vec3 vColor;
        uniform float time;
        void main() {
          vColor = color;
          vec3 pos = position;
          pos.y += sin(time * 0.5 + position.x * 0.1) * 0.5;
          pos.x += cos(time * 0.3 + position.z * 0.1) * 0.3;
          vec4 mv = modelViewMatrix * vec4(pos, 1.0);
          gl_PointSize = size * (200.0 / -mv.z);
          gl_Position  = projectionMatrix * mv;
        }
      `,
      fragmentShader: `
        varying vec3 vColor;
        void main() {
          float d = distance(gl_PointCoord, vec2(0.5));
          if (d > 0.5) discard;
          float a = 1.0 - smoothstep(0.3, 0.5, d);
          gl_FragColor = vec4(vColor, a * 0.6);
        }
      `,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      vertexColors: true
    });

    particles = new THREE.Points(geo, mat);
    scene.add(particles);
  }

  function createGridPlane() {
    const geo = new THREE.PlaneGeometry(200, 200, 40, 40);
    const mat = new THREE.ShaderMaterial({
      uniforms: { time: { value: 0 } },
      vertexShader: `
        uniform float time;
        varying vec2 vUv;
        void main() {
          vUv = uv;
          vec3 pos = position;
          pos.z += sin(pos.x * 0.1 + time) * cos(pos.y * 0.1 + time) * 1.5;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        }
      `,
      fragmentShader: `
        varying vec2 vUv;
        void main() {
          float gx = abs(fract(vUv.x * 20.0) - 0.5);
          float gy = abs(fract(vUv.y * 20.0) - 0.5);
          float g  = min(gx, gy);
          float line = 1.0 - smoothstep(0.0, 0.05, g);
          float fade = 1.0 - length(vUv - 0.5) * 1.8;
          gl_FragColor = vec4(0.0, 1.0, 0.5, line * fade * 0.06);
        }
      `,
      transparent: true,
      side: THREE.DoubleSide,
      depthWrite: false
    });

    const grid = new THREE.Mesh(geo, mat);
    grid.rotation.x = -Math.PI / 2.5;
    grid.position.y = -15;
    scene.add(grid);

    window._gridMat = mat;
  }

  let mouseX = 0, mouseY = 0;
  document.addEventListener('mousemove', (e) => {
    mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
    mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
  });

  const clock = new THREE.Clock();

  function animate() {
    animId = requestAnimationFrame(animate);
    const t = clock.getElapsedTime();

    if (particles) {
      particles.material.uniforms.time.value = t;
      particles.rotation.y = t * 0.02;
      particles.rotation.x = mouseY * 0.05;
    }

    if (window._gridMat) {
      window._gridMat.uniforms.time.value = t;
    }

    // Smooth camera follow mouse
    camera.position.x += (mouseX * 3 - camera.position.x) * 0.03;
    camera.position.y += (-mouseY * 2 - camera.position.y) * 0.03;
    camera.lookAt(0, 0, 0);

    renderer.render(scene, camera);
  }

  function onResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }

  return { init };
})();