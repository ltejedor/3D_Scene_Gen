// Initialize Three.js Scene
let scene, camera, renderer, controls;
let objects = [];

function initScene() {
    const container = document.getElementById('scene-container');

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xeeeeee);

    // Set up camera with fixed position
    camera = new THREE.PerspectiveCamera(
        65,  // Slightly wider FOV to see more of the room
        window.innerWidth / window.innerHeight,
        0.1,
        1000
    );
    
    // Position camera to view the entire scene
    camera.position.set(0, 3, 5);  // Centered, slightly elevated, pulled back
    camera.lookAt(0, 1, -2);  // Look towards the window

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

    // Set up orbit controls with constraints
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 1, -2);  // Set orbit target to center of room
    controls.minDistance = 3;        // Don't allow camera too close
    controls.maxDistance = 10;       // Don't allow camera too far
    controls.maxPolarAngle = Math.PI / 2;  // Don't allow camera below ground
    controls.update();

    // Handle window resize
    window.addEventListener('resize', onWindowResize, false);
    
    // Load scene objects
    loadSceneObjects();
}

function loadObject(glbUrl, position, rotation = { y: 0 }, objectType = '') {
    const loader = new THREE.GLTFLoader();
    
    loader.load(
        glbUrl,
        function(gltf) {
            const model = gltf.scene;

            // Compute the bounding box of the model
            const box = new THREE.Box3().setFromObject(model);
            const size = box.getSize(new THREE.Vector3());
            const center = box.getCenter(new THREE.Vector3());

            // Adjust desired size based on object type
            let desiredSize = 1;
            switch(objectType) {
                // Original furniture
                case 'window':
                    desiredSize = 2;
                    break;
                case 'mirror':
                    desiredSize = 1.5;
                    break;
                case 'couch':
                    desiredSize = 1.8;
                    break;
                case 'coffee table':
                    desiredSize = 1;
                    break;
                case 'bookshelf':
                    desiredSize = 1.5;
                    break;
                // New objects
                case 'gift':
                    desiredSize = 0.3;
                    break;
                case 'side table':
                    desiredSize = 1;
                    break;
                case 'lamp':
                    desiredSize = 0.8;
                    break;
                case 'cards':
                    desiredSize = 0.15;
                    break;
                case 'radio':
                    desiredSize = 0.3;
                    break;
                case 'journal notebook':
                    desiredSize = 0.2;
                    break;
                case 'telephone':
                    desiredSize = 0.15;
                    break;
                default:
                    desiredSize = 1;
            }

            // Calculate and apply scaling
            const maxDim = Math.max(size.x, size.y, size.z);
            const scaleFactor = desiredSize / maxDim;
            model.scale.multiplyScalar(scaleFactor);

            // Recompute bounding box after scaling
            box.setFromObject(model);
            const minY = box.min.y;

            // Set position and rotation
            model.position.x = position.x;
            model.position.z = position.z;
            model.position.y = position.y - minY;
            model.rotation.y = THREE.MathUtils.degToRad(rotation.y);

            scene.add(model);
            objects.push(model);
        },
        undefined,
        function(error) {
            console.error(`Error loading model:`, error);
        }
    );
}

async function loadSceneObjects() {
    try {
        const response = await fetch('http://localhost:8000/initialize_scene');
        if (!response.ok) {
            throw new Error('Failed to initialize scene');
        }

        const data = await response.json();
        
        // Clear existing scene
        clearScene();

        // Load each object
        data.objects.forEach(obj => {
            const absoluteURL = `http://localhost:8000${obj.fileURL}`;
            loadObject(absoluteURL, obj.position, obj.rotation, obj.type);
        });

    } catch (error) {
        console.error('Error loading scene objects:', error);
    }
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
    objects.forEach(obj => {
        scene.remove(obj);
    });
    objects = [];
}

// Initialize and start animation
initScene();
animate();