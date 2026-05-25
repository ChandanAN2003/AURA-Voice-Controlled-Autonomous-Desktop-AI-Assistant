/**
 * AURA Orbital AI Visualization using Three.js
 */

const container = document.getElementById("three-container");

// Scene Setup
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
camera.position.z = 5;

const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
renderer.setSize(container.clientWidth, container.clientHeight);
container.appendChild(renderer.domElement);

// Create the Orb
const geometry = new THREE.IcosahedronGeometry(1.5, 3);

// Material
const uniforms = {
    uTime: { value: 0.0 },
    uColor: { value: new THREE.Color(0x0ea5e9) }, // Default Accent
    uSpeed: { value: 1.0 }
};

// Shader Material for animated displacement effect
const material = new THREE.ShaderMaterial({
    uniforms: uniforms,
    wireframe: true,
    transparent: true,
    vertexShader: `
        varying vec3 vNormal;
        uniform float uTime;
        uniform float uSpeed;
        
        // Simplex noise function placeholder (using simple sine wave for performance)
        void main() {
            vNormal = normal;
            vec3 newPosition = position;
            
            // Add distortion based on time
            float displacement = sin(position.x * 5.0 + uTime * uSpeed) * 
                                  cos(position.y * 5.0 + uTime * uSpeed) * 0.1;
            
            newPosition += normal * displacement;
            
            gl_Position = projectionMatrix * modelViewMatrix * vec4(newPosition, 1.0);
        }
    `,
    fragmentShader: `
        varying vec3 vNormal;
        uniform vec3 uColor;
        
        void main() {
            // Give glowing effect around edges
            float intensity = pow(0.7 - dot(vNormal, vec3(0, 0, 1.0)), 2.0);
            gl_FragColor = vec4(uColor, 0.5) + vec4(uColor * intensity, 1.0);
        }
    `
});

const sphere = new THREE.Mesh(geometry, material);
scene.add(sphere);

// Listen to State changes from main.js to change orb behavior
window.addEventListener('auraStateChange', (e) => {
    const state = e.detail.state;
    // target colors based on state
    if (state === 'idle') {
        uniforms.uColor.value.setHex(0x94a3b8);
        uniforms.uSpeed.value = 1.0;
    } else if (state === 'listening') {
        uniforms.uColor.value.setHex(0x0ea5e9);
        uniforms.uSpeed.value = 3.0;
    } else if (state === 'thinking') {
        uniforms.uColor.value.setHex(0xf59e0b);
        uniforms.uSpeed.value = 5.0;
    } else if (state === 'executing') {
        uniforms.uColor.value.setHex(0x10b981);
        uniforms.uSpeed.value = 2.0;
    } else if (state === 'error') {
        uniforms.uColor.value.setHex(0xef4444);
        uniforms.uSpeed.value = 0.5;
    }
});

// Animation Loop
const clock = new THREE.Clock();
function animate() {
    requestAnimationFrame(animate);

    const elapsedTime = clock.getElapsedTime();
    uniforms.uTime.value = elapsedTime;

    // Rotate orb
    sphere.rotation.y += 0.005;
    sphere.rotation.x += 0.002;

    renderer.render(scene, camera);
}
animate();

// Handle resizing
window.addEventListener('resize', () => {
    if (!container) return;
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
});
