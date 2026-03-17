/**
 * FoodSave AI — Three.js 3D Scene
 * Features: Rotating globe, floating food items, particles,
 * mouse interaction, raycasting, orbit-style camera movement
 */

(function () {
  'use strict';

  // Only init on home page
  const canvas = document.getElementById('threeCanvas');
  if (!canvas) return;

  /* ═══════════════════════════════════════════
     SCENE SETUP
  ═══════════════════════════════════════════ */

  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x080c14, 0.018);

  // Camera
  const camera = new THREE.PerspectiveCamera(
    60, window.innerWidth / window.innerHeight, 0.1, 500
  );
  camera.position.set(0, 0, 18);

  // Renderer
  const renderer = new THREE.WebGLRenderer({
    canvas,
    alpha: true,
    antialias: true,
    powerPreference: 'high-performance'
  });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.2;

  /* ═══════════════════════════════════════════
     LIGHTS
  ═══════════════════════════════════════════ */

  const ambientLight = new THREE.AmbientLight(0x112233, 0.8);
  scene.add(ambientLight);

  const sunLight = new THREE.DirectionalLight(0x00ff88, 1.5);
  sunLight.position.set(10, 15, 10);
  scene.add(sunLight);

  const blueLight = new THREE.PointLight(0x00d4ff, 2.0, 30);
  blueLight.position.set(-10, 5, 8);
  scene.add(blueLight);

  const purpleLight = new THREE.PointLight(0xb48eff, 1.5, 25);
  purpleLight.position.set(8, -5, 5);
  scene.add(purpleLight);

  const rimLight = new THREE.DirectionalLight(0xffffff, 0.4);
  rimLight.position.set(-5, -10, -5);
  scene.add(rimLight);

  /* ═══════════════════════════════════════════
     EARTH GLOBE
  ═══════════════════════════════════════════ */

  function createGlobe() {
    const geometry = new THREE.SphereGeometry(4.5, 64, 64);

    // Custom shader material for the globe
    const material = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        glowColor: { value: new THREE.Color(0x00ff88) },
        deepColor: { value: new THREE.Color(0x001833) },
        landColor: { value: new THREE.Color(0x003322) },
        oceanColor: { value: new THREE.Color(0x001144) }
      },
      vertexShader: `
        varying vec3 vNormal;
        varying vec3 vPosition;
        varying vec2 vUv;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          vPosition = position;
          vUv = uv;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform float time;
        uniform vec3 glowColor;
        uniform vec3 deepColor;
        uniform vec3 landColor;
        uniform vec3 oceanColor;
        varying vec3 vNormal;
        varying vec3 vPosition;
        varying vec2 vUv;

        // Simple noise function
        float rand(vec2 c) {
          return fract(sin(dot(c, vec2(12.9898, 78.233))) * 43758.5453);
        }

        float noise(vec2 p) {
          vec2 i = floor(p);
          vec2 f = fract(p);
          f = f * f * (3.0 - 2.0 * f);
          float a = rand(i);
          float b = rand(i + vec2(1.0, 0.0));
          float c = rand(i + vec2(0.0, 1.0));
          float d = rand(i + vec2(1.0, 1.0));
          return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
        }

        void main() {
          // Continental map using noise
          float n = noise(vUv * 8.0);
          float continent = step(0.52, n);

          // Choose color based on land/ocean
          vec3 baseColor = mix(oceanColor, landColor, continent);

          // Fresnel rim glow
          float fresnel = 1.0 - max(dot(vNormal, vec3(0.0, 0.0, 1.0)), 0.0);
          fresnel = pow(fresnel, 3.0);

          // Animated grid lines
          float lat = abs(sin(vUv.y * 3.14159 * 8.0)) * 0.05;
          float lon = abs(sin(vUv.x * 3.14159 * 16.0)) * 0.05;
          float grid = max(lat, lon);
          grid *= continent > 0.5 ? 0.3 : 0.8;

          vec3 gridColor = glowColor * grid;

          // Pulsing glow on continents
          float pulse = 0.5 + 0.5 * sin(time * 1.2 + vUv.x * 20.0);
          vec3 pulseGlow = glowColor * pulse * continent * 0.08;

          // Final color
          vec3 finalColor = baseColor + gridColor + pulseGlow;
          finalColor += glowColor * fresnel * 0.6;

          gl_FragColor = vec4(finalColor, 0.9);
        }
      `,
      transparent: true,
      side: THREE.FrontSide
    });

    const globe = new THREE.Mesh(geometry, material);
    globe.name = 'globe';
    return globe;
  }

  const globe = createGlobe();
  globe.position.set(3, -1, 0);
  scene.add(globe);

  /* ═══════════════════════════════════════════
     GLOBE ATMOSPHERE GLOW
  ═══════════════════════════════════════════ */

  function createAtmosphere() {
    const geometry = new THREE.SphereGeometry(4.8, 32, 32);
    const material = new THREE.ShaderMaterial({
      uniforms: {
        glowColor: { value: new THREE.Color(0x00ff88) }
      },
      vertexShader: `
        varying vec3 vNormal;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform vec3 glowColor;
        varying vec3 vNormal;
        void main() {
          float intensity = pow(0.7 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 4.0);
          gl_FragColor = vec4(glowColor, 1.0) * intensity * 0.8;
        }
      `,
      side: THREE.BackSide,
      blending: THREE.AdditiveBlending,
      transparent: true,
      depthWrite: false
    });
    return new THREE.Mesh(geometry, material);
  }

  const atmosphere = createAtmosphere();
  atmosphere.position.copy(globe.position);
  scene.add(atmosphere);

  /* ═══════════════════════════════════════════
     ORBIT RINGS
  ═══════════════════════════════════════════ */

  function createOrbitRing(radius, color, opacity) {
    const geometry = new THREE.TorusGeometry(radius, 0.02, 8, 120);
    const material = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    });
    return new THREE.Mesh(geometry, material);
  }

  const ring1 = createOrbitRing(6.5, 0x00ff88, 0.15);
  ring1.rotation.x = Math.PI / 2.5;
  ring1.rotation.z = 0.3;
  ring1.position.copy(globe.position);
  scene.add(ring1);

  const ring2 = createOrbitRing(7.5, 0x00d4ff, 0.10);
  ring2.rotation.x = Math.PI / 1.8;
  ring2.rotation.y = 0.5;
  ring2.position.copy(globe.position);
  scene.add(ring2);

  /* ═══════════════════════════════════════════
     FLOATING FOOD ITEMS (emoji-based geometry)
  ═══════════════════════════════════════════ */

  const foodItems = [];

  function createFoodMesh(type) {
    let geometry, material, color;

    switch (type) {
      case 'apple':
        geometry = new THREE.SphereGeometry(0.45, 16, 16);
        color = 0xff4444;
        break;
      case 'bread':
        geometry = new THREE.BoxGeometry(0.8, 0.5, 0.5, 2, 2, 2);
        color = 0xd4a065;
        break;
      case 'carrot':
        geometry = new THREE.ConeGeometry(0.2, 0.9, 8);
        color = 0xff8800;
        break;
      case 'pea':
        geometry = new THREE.SphereGeometry(0.35, 12, 12);
        color = 0x44cc44;
        break;
      case 'grain':
        geometry = new THREE.SphereGeometry(0.25, 8, 8);
        color = 0xffdd88;
        break;
      default:
        geometry = new THREE.SphereGeometry(0.4, 16, 16);
        color = 0x00ff88;
    }

    material = new THREE.MeshPhongMaterial({
      color,
      emissive: new THREE.Color(color).multiplyScalar(0.15),
      shininess: 60,
      transparent: true,
      opacity: 0.85
    });

    const mesh = new THREE.Mesh(geometry, material);
    mesh.userData.foodType = type;
    mesh.userData.originalColor = new THREE.Color(color);
    mesh.userData.hovering = false;

    return mesh;
  }

  const foodTypes = ['apple', 'bread', 'carrot', 'pea', 'grain', 'apple', 'pea'];
  const foodCount = 14;

  for (let i = 0; i < foodCount; i++) {
    const type = foodTypes[i % foodTypes.length];
    const mesh = createFoodMesh(type);

    // Spread around globe with some randomness
    const angle = (i / foodCount) * Math.PI * 2;
    const radius = 6.5 + Math.random() * 3;
    const height = (Math.random() - 0.5) * 8;

    mesh.position.set(
      Math.cos(angle) * radius + globe.position.x,
      height,
      Math.sin(angle) * radius * 0.6 + globe.position.z
    );

    mesh.userData.orbitRadius = radius;
    mesh.userData.orbitAngle = angle;
    mesh.userData.orbitSpeed = 0.003 + Math.random() * 0.005;
    mesh.userData.orbitHeight = height;
    mesh.userData.bobSpeed = 0.5 + Math.random() * 1;
    mesh.userData.bobPhase = Math.random() * Math.PI * 2;
    mesh.userData.bobAmount = 0.2 + Math.random() * 0.4;

    scene.add(mesh);
    foodItems.push(mesh);
  }

  /* ═══════════════════════════════════════════
     PARTICLE SYSTEM
  ═══════════════════════════════════════════ */

  function createParticleSystem() {
    const count = 1800;
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    const sizes = new Float32Array(count);

    const colorPalette = [
      new THREE.Color(0x00ff88),
      new THREE.Color(0x00d4ff),
      new THREE.Color(0xb48eff),
      new THREE.Color(0xffd93d)
    ];

    for (let i = 0; i < count; i++) {
      // Distribute in a large sphere
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos((Math.random() * 2) - 1);
      const r = 12 + Math.random() * 20;

      positions[i * 3]     = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = r * Math.cos(phi);

      const c = colorPalette[Math.floor(Math.random() * colorPalette.length)];
      colors[i * 3]     = c.r;
      colors[i * 3 + 1] = c.g;
      colors[i * 3 + 2] = c.b;

      sizes[i] = Math.random() * 2.5 + 0.5;
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

    const material = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 }
      },
      vertexShader: `
        attribute float size;
        attribute vec3 color;
        varying vec3 vColor;
        uniform float time;
        void main() {
          vColor = color;
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          float sz = size * (1.0 + 0.3 * sin(time * 2.0 + position.x));
          gl_PointSize = sz * (300.0 / -mvPosition.z);
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        varying vec3 vColor;
        void main() {
          float d = distance(gl_PointCoord, vec2(0.5));
          if (d > 0.5) discard;
          float alpha = 1.0 - smoothstep(0.3, 0.5, d);
          gl_FragColor = vec4(vColor, alpha * 0.7);
        }
      `,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      vertexColors: true
    });

    return new THREE.Points(geometry, material);
  }

  const particles = createParticleSystem();
  scene.add(particles);

  /* ═══════════════════════════════════════════
     DATA STREAM LINES (orbiting globe)
  ═══════════════════════════════════════════ */

  const streamLines = [];

  function createStreamLine() {
    const points = [];
    const startAngle = Math.random() * Math.PI * 2;
    const endAngle   = startAngle + (Math.PI / 2 + Math.random() * Math.PI);

    for (let i = 0; i <= 32; i++) {
      const t = i / 32;
      const angle = startAngle + t * (endAngle - startAngle);
      const r = 5.2 + Math.sin(t * Math.PI) * 1.5;
      points.push(new THREE.Vector3(
        Math.cos(angle) * r + globe.position.x,
        (Math.random() - 0.5) * 3,
        Math.sin(angle) * r + globe.position.z
      ));
    }

    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    const material = new THREE.LineBasicMaterial({
      color: new THREE.Color(0x00ff88),
      transparent: true,
      opacity: 0.15,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    });

    return new THREE.Line(geometry, material);
  }

  for (let i = 0; i < 6; i++) {
    const line = createStreamLine();
    scene.add(line);
    streamLines.push(line);
  }

  /* ═══════════════════════════════════════════
     RAYCASTING & MOUSE INTERACTION
  ═══════════════════════════════════════════ */

  const raycaster = new THREE.Raycaster();
  const mouse = new THREE.Vector2();
  let hoveredObject = null;

  function onMouseMove(event) {
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

    // Update camera offset based on mouse
    cameraTargetX = mouse.x * 0.8;
    cameraTargetY = mouse.y * 0.4;
  }

  function onMouseClick() {
    if (!hoveredObject) return;
    triggerFoodClick(hoveredObject);
  }

  function triggerFoodClick(obj) {
    // Scale pop animation
    const originalScale = { x: obj.scale.x, y: obj.scale.y, z: obj.scale.z };

    let t = 0;
    const pop = () => {
      t += 0.12;
      if (t < 1) {
        const s = 1 + Math.sin(t * Math.PI) * 0.5;
        obj.scale.set(s, s, s);
        requestAnimationFrame(pop);
      } else {
        obj.scale.set(originalScale.x, originalScale.y, originalScale.z);
      }
    };
    pop();

    // Create floating +100 text effect (DOM based)
    const rect = canvas.getBoundingClientRect();
    const div = document.createElement('div');
    div.textContent = '+100 pts!';
    div.style.cssText = `
      position:fixed;
      font-family:'Syne',sans-serif;
      font-weight:800;
      font-size:1.1rem;
      color:#00ff88;
      pointer-events:none;
      z-index:9999;
      text-shadow: 0 0 20px rgba(0,255,136,0.8);
      left:${(mouse.x + 1) / 2 * window.innerWidth}px;
      top:${(-mouse.y + 1) / 2 * window.innerHeight}px;
      transform:translateX(-50%);
      animation:floatUp 1.5s ease forwards;
    `;

    if (!document.getElementById('floatUpStyle')) {
      const style = document.createElement('style');
      style.id = 'floatUpStyle';
      style.textContent = `@keyframes floatUp{0%{opacity:1;transform:translateX(-50%) translateY(0)}100%{opacity:0;transform:translateX(-50%) translateY(-80px)}}`;
      document.head.appendChild(style);
    }

    document.body.appendChild(div);
    setTimeout(() => div.remove(), 1500);
  }

  window.addEventListener('mousemove', onMouseMove);
  window.addEventListener('click', onMouseClick);

  /* ═══════════════════════════════════════════
     CAMERA ANIMATION VARS
  ═══════════════════════════════════════════ */

  let cameraTargetX = 0;
  let cameraTargetY = 0;
  let cameraX = 0;
  let cameraY = 0;
  let scrollProgress = 0;

  window.addEventListener('scroll', () => {
    scrollProgress = window.scrollY / (document.body.scrollHeight - window.innerHeight);
  });

  /* ═══════════════════════════════════════════
     ANIMATION LOOP
  ═══════════════════════════════════════════ */

  const clock = new THREE.Clock();
  let frameId;

  function animate() {
    frameId = requestAnimationFrame(animate);
    const elapsed = clock.getElapsedTime();
    const delta = clock.getDelta();

    // Update shader uniforms
    if (globe.material.uniforms) {
      globe.material.uniforms.time.value = elapsed;
    }
    if (particles.material.uniforms) {
      particles.material.uniforms.time.value = elapsed;
    }

    // Globe rotation
    globe.rotation.y = elapsed * 0.08;
    atmosphere.rotation.y = elapsed * 0.06;

    // Ring animations
    ring1.rotation.z = elapsed * 0.15;
    ring2.rotation.y = elapsed * 0.12;

    // Particle slow rotation
    particles.rotation.y = elapsed * 0.015;
    particles.rotation.x = elapsed * 0.008;

    // Food items orbital + bob animation
    foodItems.forEach((food, idx) => {
      food.userData.orbitAngle += food.userData.orbitSpeed;
      const angle = food.userData.orbitAngle;
      const r = food.userData.orbitRadius;

      food.position.x = Math.cos(angle) * r + globe.position.x;
      food.position.z = Math.sin(angle) * r * 0.6 + globe.position.z;
      food.position.y = food.userData.orbitHeight
        + Math.sin(elapsed * food.userData.bobSpeed + food.userData.bobPhase)
        * food.userData.bobAmount;

      // Gentle rotation
      food.rotation.x = elapsed * 0.5 + idx;
      food.rotation.y = elapsed * 0.7 + idx * 0.5;
    });

    // Stream lines opacity pulse
    streamLines.forEach((line, idx) => {
      line.material.opacity = 0.05 + 0.15 * Math.abs(Math.sin(elapsed * 0.8 + idx));
    });

    // Raycasting for hover
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(foodItems);

    if (intersects.length > 0) {
      const obj = intersects[0].object;
      if (hoveredObject !== obj) {
        if (hoveredObject) {
          hoveredObject.material.emissive.copy(
            hoveredObject.userData.originalColor
          ).multiplyScalar(0.15);
          hoveredObject.userData.hovering = false;
        }
        hoveredObject = obj;
        hoveredObject.material.emissive.copy(
          hoveredObject.userData.originalColor
        ).multiplyScalar(0.5);
        hoveredObject.userData.hovering = true;
        document.body.style.cursor = 'pointer';
      }
    } else {
      if (hoveredObject) {
        hoveredObject.material.emissive.copy(
          hoveredObject.userData.originalColor
        ).multiplyScalar(0.15);
        hoveredObject.userData.hovering = false;
        hoveredObject = null;
      }
      document.body.style.cursor = 'default';
    }

    // Smooth camera mouse follow
    cameraX += (cameraTargetX - cameraX) * 0.04;
    cameraY += (cameraTargetY - cameraY) * 0.04;
    camera.position.x = cameraX * 2;
    camera.position.y = cameraY * 1 + scrollProgress * -5;

    // Camera look at scene center
    camera.lookAt(globe.position.x, 0, 0);

    renderer.render(scene, camera);
  }

  animate();

  /* ═══════════════════════════════════════════
     RESPONSIVE RESIZE
  ═══════════════════════════════════════════ */

  function onResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  }

  window.addEventListener('resize', onResize);

  /* ═══════════════════════════════════════════
     CLEANUP
  ═══════════════════════════════════════════ */

  window.addEventListener('beforeunload', () => {
    cancelAnimationFrame(frameId);
    renderer.dispose();
    window.removeEventListener('mousemove', onMouseMove);
    window.removeEventListener('click', onMouseClick);
    window.removeEventListener('resize', onResize);
  });

  // Expose scene for debugging
  window.threeScene = { scene, camera, renderer, globe, foodItems };

})();