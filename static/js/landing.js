/**
 * FoodSave AI — Cinematic Landing Page (Three.js + GLSL)
 * Features: Interactive Globe, Particle System, AI Brain, Loader
 */

let scene, camera, renderer;
let globe, particles, brainMesh;
let mouseX = 0, mouseY = 0;
let targetX = 0, targetY = 0;

// Loader Function (as you provided)
function initLoader() {
  const screen = document.getElementById('loadingScreen');
  const bar = document.getElementById('loaderBarFill');
  const text = document.getElementById('loaderText');
  
  if (!screen) {
    console.warn("Loading screen not found");
    initThreeScene();
    return;
  }

  const steps = [
    { pct: 15, msg: 'Loading AI Engine...' },
    { pct: 35, msg: 'Mapping Food Networks...' },
    { pct: 55, msg: 'Connecting NGO Database...' },
    { pct: 75, msg: 'Initializing 3D Scene...' },
    { pct: 90, msg: 'Almost ready...' },
    { pct: 100, msg: 'Welcome to FoodSave AI 🌱' }
  ];

  let i = 0;

  function nextStep() {
    if (i >= steps.length) {
      hideLoader();
      return;
    }
    if (bar) bar.style.width = steps[i].pct + '%';
    if (text) text.textContent = steps[i].msg;
    i++;
    setTimeout(nextStep, 380);
  }

  function hideLoader() {
    screen.style.opacity = '0';
    screen.style.transition = 'opacity 0.8s ease-out';
    setTimeout(() => {
      screen.style.display = 'none';
      initThreeScene();   // Start 3D scene after loader
    }, 800);
  }

  // Hard timeout safety
  const hardTimeout = setTimeout(() => {
    console.log('⏱️ Hard timeout — forcing loader hide');
    hideLoader();
  }, 4200);

  nextStep();
}

// ====================== THREE.JS SCENE ======================
function initThreeScene() {
  const container = document.getElementById('threeContainer');
  if (!container) return;

  // Scene Setup
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(renderer.domElement);

  camera.position.z = 4.5;

  // Ambient Light
  const ambient = new THREE.AmbientLight(0xaaaaaa, 0.6);
  scene.add(ambient);

  // Directional Light
  const dirLight = new THREE.DirectionalLight(0x00ff88, 1.2);
  dirLight.position.set(5, 10, 7);
  scene.add(dirLight);

  createGlobe();
  createParticles();
  createBrainEffect();

  // Mouse Interaction
  window.addEventListener('mousemove', (e) => {
    mouseX = (e.clientX / window.innerWidth) * 2 - 1;
    mouseY = -(e.clientY / window.innerHeight) * 2 + 1;
  });

  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  animate();
}

// Globe
function createGlobe() {
  const geometry = new THREE.SphereGeometry(1.8, 64, 64);
  const material = new THREE.MeshPhongMaterial({
    color: 0x00cc88,
    emissive: 0x003322,
    shininess: 5,
    transparent: true,
    opacity: 0.95
  });
  globe = new THREE.Mesh(geometry, material);
  scene.add(globe);

  // Glow Ring
  const ringGeo = new THREE.RingGeometry(2.1, 2.3, 64);
  const ringMat = new THREE.MeshBasicMaterial({
    color: 0x00ffaa,
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 0.15
  });
  const ring = new THREE.Mesh(ringGeo, ringMat);
  ring.rotation.x = Math.PI / 2;
  scene.add(ring);
}

// Particle System
function createParticles() {
  const count = 1200;
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);

  for (let i = 0; i < count * 3; i += 3) {
    const radius = 3.2 + Math.random() * 1.8;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);

    positions[i]     = radius * Math.sin(phi) * Math.cos(theta);
    positions[i + 1] = radius * Math.sin(phi) * Math.sin(theta);
    positions[i + 2] = radius * Math.cos(phi);

    colors[i]     = 0.2 + Math.random() * 0.6;
    colors[i + 1] = 0.9;
    colors[i + 2] = 0.6;
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

  const material = new THREE.PointsMaterial({
    size: 0.018,
    vertexColors: true,
    transparent: true,
    opacity: 0.85,
    blending: THREE.AdditiveBlending
  });

  particles = new THREE.Points(geometry, material);
  scene.add(particles);
}

// AI Brain Effect
function createBrainEffect() {
  const geometry = new THREE.IcosahedronGeometry(0.9, 2);
  const material = new THREE.MeshPhongMaterial({
    color: 0x00ffff,
    emissive: 0x0088ff,
    shininess: 10,
    wireframe: true,
    transparent: true,
    opacity: 0.6
  });
  brainMesh = new THREE.Mesh(geometry, material);
  brainMesh.position.set(2.8, 1.2, -1.5);
  scene.add(brainMesh);
}

// Animation Loop
function animate() {
  requestAnimationFrame(animate);

  // Gentle rotation
  if (globe) globe.rotation.y += 0.0012;
  if (brainMesh) brainMesh.rotation.y += 0.003;

  // Particle movement
  if (particles) {
    particles.rotation.y += 0.0003;
  }

  // Mouse follow
  targetX = mouseX * 0.15;
  targetY = mouseY * 0.12;
  if (globe) {
    globe.rotation.x = THREE.MathUtils.lerp(globe.rotation.x, targetY, 0.05);
    globe.rotation.y = THREE.MathUtils.lerp(globe.rotation.y, targetX * 1.2, 0.05);
  }

  renderer.render(scene, camera);
}

// Initialize everything
document.addEventListener('DOMContentLoaded', () => {
  initLoader();
});

// Expose for external use
window.foodsaveLanding = { initLoader, initThreeScene };