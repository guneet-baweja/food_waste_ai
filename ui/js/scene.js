/**
 * FoodSave AI — Cinematic 3D WebGL Scene
 * Three.js + GSAP for immersive visualization
 */

// ━━━ THREE.JS SETUP ━━━
const canvas = document.querySelector('canvas') || createCanvas();
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x000000);
scene.fog = new THREE.Fog(0x000000, 500, 2000);

const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 10000);
camera.position.set(0, 50, 150);

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowShadowMap;

// Insert canvas if it doesn't exist
function createCanvas() {
    const canvas = document.createElement('canvas');
    document.body.insertBefore(canvas, document.querySelector('.ui-overlay'));
    return canvas;
}

document.body.insertBefore(renderer.domElement, document.querySelector('.ui-overlay'));

// ━━━ LIGHTING ━━━
const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
scene.add(ambientLight);

const directionalLight = new THREE.DirectionalLight(0x00ff88, 0.8);
directionalLight.position.set(100, 100, 100);
directionalLight.castShadow = true;
directionalLight.shadow.mapSize.width = 2048;
directionalLight.shadow.mapSize.height = 2048;
scene.add(directionalLight);

// Point lights for atmosphere
const pointLight1 = new THREE.PointLight(0x00ff88, 0.5, 300);
pointLight1.position.set(100, 100, 0);
scene.add(pointLight1);

const pointLight2 = new THREE.PointLight(0x00d4ff, 0.5, 300);
pointLight2.position.set(-100, 100, 100);
scene.add(pointLight2);

// ━━━ PARTICLE SYSTEM (AI Brain) ━━━
class ParticleSystem {
    constructor(count = 1000) {
        const geometry = new THREE.BufferGeometry();
        const positions = [];
        const velocities = [];
        
        for (let i = 0; i < count; i++) {
            positions.push(
                (Math.random() - 0.5) * 300,
                (Math.random() - 0.5) * 300,
                (Math.random() - 0.5) * 300
            );
            velocities.push(
                (Math.random() - 0.5) * 2,
                (Math.random() - 0.5) * 2,
                (Math.random() - 0.5) * 2
            );
        }
        
        geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(positions), 3));
        
        const material = new THREE.PointsMaterial({
            size: 1,
            color: 0x00ff88,
            transparent: true,
            opacity: 0.6,
            sizeAttenuation: true
        });
        
        this.particles = new THREE.Points(geometry, material);
        this.velocities = velocities;
        scene.add(this.particles);
    }
    
    update() {
        const positions = this.particles.geometry.attributes.position.array;
        
        for (let i = 0; i < positions.length; i += 3) {
            positions[i] += this.velocities[i / 3 * 3] * 0.1;
            positions[i + 1] += this.velocities[i / 3 * 3 + 1] * 0.1;
            positions[i + 2] += this.velocities[i / 3 * 3 + 2] * 0.1;
            
            // Wrap around
            if (Math.abs(positions[i]) > 150) this.velocities[i / 3 * 3] *= -1;
            if (Math.abs(positions[i + 1]) > 150) this.velocities[i / 3 * 3 + 1] *= -1;
            if (Math.abs(positions[i + 2]) > 150) this.velocities[i / 3 * 3 + 2] *= -1;
        }
        
        this.particles.geometry.attributes.position.needsUpdate = true;
    }
}

// ━━━ EARTH SCENE ━━━
function createEarth() {
    const geometry = new THREE.SphereGeometry(50, 64, 64);
    
    // Create canvas texture for Earth
    const canvas = document.createElement('canvas');
    canvas.width = 2048;
    canvas.height = 1024;
    const ctx = canvas.getContext('2d');
    
    // Blue ocean
    ctx.fillStyle = '#001a4d';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Green continents
    ctx.fillStyle = '#00a834';
    
    // Simple continents pattern
    for (let i = 0; i < 5; i++) {
        for (let j = 0; j < 3; j++) {
            ctx.fillRect(
                i * 400 + Math.random() * 100,
                j * 300 + Math.random() * 100,
                Math.random() * 150 + 100,
                Math.random() * 150 + 100
            );
        }
    }
    
    const texture = new THREE.CanvasTexture(canvas);
    const material = new THREE.MeshPhongMaterial({ map: texture });
    
    const earth = new THREE.Mesh(geometry, material);
    earth.castShadow = true;
    earth.receiveShadow = true;
    
    // Rotate Earth
    gsap.to(earth.rotation, { z: Math.PI * 2, duration: 60, repeat: -1, ease: 'none' });
    
    scene.add(earth);
    return earth;
}

// ━━━ ROTATING CUBE (Data Processing) ━━━
function createDataCube() {
    const geometry = new THREE.BoxGeometry(30, 30, 30);
    const material = new THREE.MeshPhongMaterial({ 
        color: 0x00d4ff,
        emissive: 0x00a8cc,
        wireframe: false
    });
    
    const cube = new THREE.Mesh(geometry, material);
    cube.position.set(0, 0, 0);
    cube.castShadow = true;
    cube.receiveShadow = true;
    
    // Add edges
    const edges = new THREE.EdgesGeometry(geometry);
    const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x00ff88 }));
    cube.add(line);
    
    // Rotate continuously
    gsap.to(cube.rotation, { 
        x: Math.PI * 2, 
        y: Math.PI * 2, 
        duration: 8, 
        repeat: -1, 
        ease: 'none' 
    });
    
    scene.add(cube);
    return cube;
}

// ━━━ CLASSIFICATION VISUALIZATION ━━━
function createClassificationSpheres() {
    const spheres = [];
    const classes = ['Fresh', 'Semi-Fresh', 'Rotten', 'Cooked', 'Packaged'];
    const colors = [0x00ff88, 0xffa500, 0xff6b6b, 0xff8c42, 0xcccccc];
    
    for (let i = 0; i < classes.length; i++) {
        const angle = (i / classes.length) * Math.PI * 2;
        const x = Math.cos(angle) * 120;
        const z = Math.sin(angle) * 120;
        
        const geometry = new THREE.SphereGeometry(15, 32, 32);
        const material = new THREE.MeshPhongMaterial({ 
            color: colors[i],
            emissive: colors[i],
            emissiveIntensity: 0.3
        });
        
        const sphere = new THREE.Mesh(geometry, material);
        sphere.position.set(x, 0, z);
        sphere.castShadow = true;
        sphere.receiveShadow = true;
        
        // Pulsing animation
        gsap.to(sphere.scale, { 
            x: 1.2, 
            y: 1.2, 
            z: 1.2, 
            duration: 2,
            repeat: -1,
            yoyo: true,
            delay: i * 0.3
        });
        
        scene.add(sphere);
        spheres.push({ sphere, class: classes[i], index: i });
    }
    
    return spheres;
}

// ━━━ ROUTE VISUALIZATION (Lines between destinations) ━━━
function createRoutes() {
    const points = [
        new THREE.Vector3(100, 50, 0),      // NGO
        new THREE.Vector3(-100, 50, 0),     // Poultry Farm
        new THREE.Vector3(0, 50, 100),      // Biogas Plant
        new THREE.Vector3(0, 50, -100),     // Compost
    ];
    
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    const material = new THREE.LineBasicMaterial({ 
        color: 0xffa500,
        linewidth: 2,
        transparent: true,
        opacity: 0.3
    });
    
    const routes = new THREE.Line(geometry, material);
    scene.add(routes);
    
    return { routes, points };
}

// ━━━ INITIALIZE SCENE ━━━
const earth = createEarth();
const dataCube = createDataCube();
const classificationSpheres = createClassificationSpheres();
const { routes } = createRoutes();
const particleSystem = new ParticleSystem(800);

// Camera control
let cameraTarget = new THREE.Vector3(0, 0, 0);
gsap.to(camera.position, {
    x: 0,
    y: 80,
    z: 200,
    duration: 10,
    repeat: -1,
    yoyo: true,
    ease: 'sine.inOut'
});

// ━━━ ANIMATION LOOP ━━━
function animate() {
    requestAnimationFrame(animate);
    
    particleSystem.update();
    
    // Gentle camera look
    camera.lookAt(cameraTarget);
    
    renderer.render(scene, camera);
}

animate();

// ━━━ RESPONSIVE ━━━
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// ━━━ UI INTERACTIONS ━━━
const predictionPanel = document.getElementById('predictionPanel');
const routingPanel = document.getElementById('routingPanel');
const uploadArea = document.getElementById('uploadArea');

function openUploadArea() {
    uploadArea.classList.add('active');
}

function closeUploadArea() {
    uploadArea.classList.remove('active');
}

async function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    const spinner = document.getElementById('spinner');
    const status = document.getElementById('uploadStatus');
    
    spinner.style.display = 'block';
    status.textContent = 'Analyzing image...';
    
    try {
        const response = await fetch('http://localhost:5000/predict', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showPredictionResult(result.data);
            closeUploadArea();
            updateStats();
        } else {
            status.textContent = '❌ Error: ' + result.error;
        }
    } catch (error) {
        status.textContent = '❌ Connection error. Is Flask server running?';
        console.error('Error:', error);
    } finally {
        spinner.style.display = 'none';
    }
}

function showPredictionResult(data) {
    const panel = predictionPanel;
    const freshness = data.freshness_class;
    const confidence = data.confidence;
    const action = data.action;
    
    // Update prediction panel
    const badgeEl = document.getElementById('freshnessBadge');
    badgeEl.textContent = freshness.toUpperCase();
    badgeEl.className = `freshness-badge freshness-${freshness}`;
    
    const confidenceFill = document.getElementById('confidenceFill');
    confidenceFill.style.width = (confidence * 100) + '%';
    
    const actionEl = document.getElementById('actionText');
    actionEl.textContent = action;
    
    panel.classList.add('active');
    
    // Show routing panel
    const routingPanelEl = document.getElementById('routingPanel');
    const routeDetails = document.getElementById('routeDetails');
    const destination = data.decision.destination;
    const distance = data.decision.distance_km;
    
    routeDetails.innerHTML = `
        <div class="route-item">
            📍 <strong>${destination}</strong><br>
            Distance: <span class="route-distance">${distance} km</span>
        </div>
    `;
    
    routingPanelEl.classList.add('active');
    
    // Animate sphere based on prediction
    const sphereIndex = ['fresh', 'semi_fresh', 'rotten', 'cooked', 'packaged'].indexOf(freshness);
    if (sphereIndex >= 0) {
        const sphere = classificationSpheres[sphereIndex].sphere;
        gsap.to(sphere.scale, { x: 1.5, y: 1.5, z: 1.5, duration: 0.8, yoyo: true });
        
        // Camera zoom towards sphere
        const pos = sphere.position;
        gsap.to(camera.position, { 
            x: pos.x * 1.5, 
            y: 100, 
            z: pos.z * 1.5, 
            duration: 1.5
        });
    }
}

function updateStats() {
    const count = parseInt(document.getElementById('stat-predictions').textContent) + 1;
    document.getElementById('stat-predictions').textContent = count;
    document.getElementById('stat-processing').textContent = 'Complete ✓';
}

// Check API status
setInterval(async () => {
    try {
        const response = await fetch('http://localhost:5000/health');
        if (response.ok) {
            document.getElementById('api-status').textContent = '● Online';
            document.getElementById('api-status').style.color = '#00ff88';
        }
    } catch (e) {
        document.getElementById('api-status').textContent = '● Offline';
        document.getElementById('api-status').style.color = '#ff6b6b';
    }
}, 5000);

// Drag and drop
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = '#00d4ff';
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.style.borderColor = 'rgba(0, 255, 136, 0.5)';
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        document.getElementById('fileInput').files = files;
        handleFileSelect({ target: { files } });
    }
});

console.log('✅ FoodSave AI — 3D Scene initialized');
