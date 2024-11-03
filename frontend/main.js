// frontend/main.js

// Initialize Three.js Scene
let scene, camera, renderer, controls;
let objects = [];

function initScene() {
    const container = document.getElementById('scene-container');

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xeeeeee);

    camera = new THREE.PerspectiveCamera(
        75,
        window.innerWidth / window.innerHeight,
        0.1,
        1000
    );
    camera.position.set(0, 5, 10);

    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    container.appendChild(renderer.domElement);

    // Add ambient light
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);

    // Add directional light
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
    directionalLight.position.set(10, 10, 10);
    scene.add(directionalLight);

    // Add grid helper
    const gridHelper = new THREE.GridHelper(20, 20);
    scene.add(gridHelper);

    // Handle window resize
    window.addEventListener('resize', onWindowResize, false);

    // Orbit controls
    controls = new THREE.OrbitControls(camera, renderer.domElement);
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}

function clearScene() {
    // Remove existing objects
    objects.forEach(obj => {
        scene.remove(obj);
    });
    objects = [];
}

function loadObject(glbUrl, position) {
    const loader = new THREE.GLTFLoader();
    
    loader.load(
        glbUrl,
        function(gltf) {
            const model = gltf.scene;

            // Compute the bounding box of the model
            const box = new THREE.Box3().setFromObject(model);
            const size = box.getSize(new THREE.Vector3());
            const center = box.getCenter(new THREE.Vector3());

            // Define the desired size (e.g., max dimension = 1 unit)
            const desiredSize = 1; // Adjust as needed

            // Calculate the scaling factor
            const maxDim = Math.max(size.x, size.y, size.z);
            const scaleFactor = desiredSize / maxDim;

            // Apply the scaling factor to the model
            model.scale.multiplyScalar(scaleFactor);

            // Recompute bounding box after scaling
            box.setFromObject(model);
            const sizeAfterScale = box.getSize(new THREE.Vector3());
            const centerAfterScale = box.getCenter(new THREE.Vector3());
            const minY = box.min.y;

            // Adjust model position
            model.position.x = position.x - centerAfterScale.x;
            model.position.z = position.z - centerAfterScale.z;

            // For y-axis, align the base of the model with the ground (y = position.y)
            model.position.y = position.y - minY;

            scene.add(model);
            objects.push(model);

            // Center the camera on the loaded object
            adjustCamera(model);
        },
        undefined,
        function(error) {
            console.error(`Error loading model from ${glbUrl}:`, error);
            alert(`Failed to load model from ${glbUrl}. Check console for details.`);
        }
    );
}

function adjustCamera(model) {
    const box = new THREE.Box3().setFromObject(model);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());

    const maxDim = Math.max(size.x, size.y, size.z);
    const fov = camera.fov * (Math.PI / 180);
    let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));

    camera.position.set(center.x, center.y + cameraZ / 3, center.z + cameraZ * 1.5);
    camera.lookAt(center);

    const minZ = box.min.z;
    const cameraToFarEdge = (minZ < 0) ? -minZ + cameraZ : cameraZ - minZ;

    camera.far = cameraToFarEdge * 3;
    camera.updateProjectionMatrix();

    controls.target.set(center.x, center.y, center.z);
    controls.update();
}

document.getElementById('generateBtn').addEventListener('click', async () => {
    const prompt = document.getElementById('promptInput').value.trim();
    if (!prompt) {
        alert("Please enter a scene description.");
        return;
    }

    // Show loading indicator
    document.getElementById('loading').style.display = 'block';

    try {
        const response = await fetch('http://localhost:8000/generate_scene', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error generating scene.');
        }

        const data = await response.json();
        console.log('Response:', data);

        // Clear existing scene
        clearScene();

        // Load the new object
        const objectURL = data.fileURL;
        const absoluteURL = `http://localhost:8000${objectURL}`; // Adjust if backend is hosted elsewhere

        // For positioning, you can set default values or include in the backend response
        loadObject(absoluteURL, { x: 0, y: 0, z: 0 });

    } catch (error) {
        console.error("Failed to generate scene:", error);
        alert(`Failed to generate scene: ${error.message}`);
    } finally {
        // Hide loading indicator
        document.getElementById('loading').style.display = 'none';
    }
});

// Initialize and start animation
initScene();
animate();
