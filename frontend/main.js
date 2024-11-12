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
    
    // Load local models
    loadLocalModels();
}

function loadObject(folderName, position, rotation = { y: 0 }, objectType = '') {
    const loader = new THREE.GLTFLoader();
    const glbUrl = `./assets/${folderName}/scene.gltf`;
    
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
                case 'window':
                    desiredSize = 4;
                    break;
                case 'mirror':
                    desiredSize = .75;
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
                case 'gift':
                    desiredSize = 0.3;
                    break;
                case 'side table':
                    desiredSize = 1;
                    break;
                case 'lamp':
                    desiredSize = 0.8;
                    break;
                case 'radio':
                    desiredSize = 0.3;
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

function loadLocalModels() {
    // Specify each model's folder, position, rotation, and type
    const models = [
        { folder: 'bookshelf_cc0', position: { x: -10, y: 0, z: -1 }, rotation: { y: 0 }, type: 'bookshelf' },
        { folder: 'coffee_table', position: { x: -1, y: 0, z: -1 }, rotation: { y: 45 }, type: 'coffee table' },
        { folder: 'couch', position: { x: -2, y: 0, z: -1 }, rotation: { y: 90 }, type: 'couch' },
        { folder: 'gift_box_with_a_ribbons', position: { x: -1, y: .25, z: -.5 }, rotation: { y: 0 }, type: 'gift' },
        { folder: 'mirror', position: { x: -2.25, y: .75, z: -1 }, rotation: { y: 90 }, type: 'mirror' },
        { folder: 'modern_side_lamp_and_stand', position: { x: 1.75, y: 0, z: -2.5 }, rotation: { y: 0 }, type: 'lamp' },
        { folder: 'radio_broadcaster', position: { x: 0, y: 0, z: -2 }, rotation: { y: 0 }, type: 'radio' },
        { folder: 'telephone', position: { x: 1, y: 0, z: 1 }, rotation: { y: 0 }, type: 'telephone' },
        { folder: 'window_area', position: { x: 0, y: -.25, z: -3 }, rotation: { y: 0 }, type: 'window' },
    ];

    // Load each specified model
    models.forEach(model => {
        loadObject(model.folder, model.position, model.rotation, model.type);
    });
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
