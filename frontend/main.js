// Initialize Three.js Scene
let scene, camera, renderer;
let objects = [];
let moveForward = false;
let moveBackward = false;
let rotateLeft = false;
let rotateRight = false;
const moveSpeed = 0.1;
const rotateSpeed = 0.03;
const cameraHeight = 0.8; // Lowered camera height
let highlightedObject = null;
const INTERACTION_DISTANCE = 2; // Distance threshold for interaction in units
const objectDescriptions = {
    'gift_box_with_a_ribbons': "he was very friendly at first and he seemed very low-key and non-threatening so we met at the gym we started hanging out um a little bit but he just would not give up so he was texting me all the time pursuing me all the time always asking me to hang out he he very quickly jumped right into the i love you the i want to be with you forever you're you're perfect for me true love bombing straight from the beginning and he encouraged um you know moving in together and made these really grand promises",
    'mirror': "I mean, there would have been no way for me to get out if I would have said I'm leaving. Not too long before this had happened, we were in a car accident. And I was like, we were away for a weekend. And he said to me, you know, if you ever leave me, they're going to find you at the bottom of a lake somewhere. And he just said it really subtly, like casually in a conversation",
    'modern_side_lamp_and_stand': "Shaun started making remarks about my little sister who was twelve at the time. We'd been out for my sister's birthday and I posted a photo of us online; minutes later Shaun was tweeting about how shocking it was one sister could look much more sexy than another, how surprising it was that one person could go from pretty to hideous whilst their younger sister remained gorgeou",
    'radio_broadcaster': "I said once I wanted to go to university in the future, he suddenly went really off and wouldn\u2019t talk to me for days. Then he said he was furious I\u2019d want to waste my time at university instead of spending it with him! Try and take a step back and think about what you'd think if someone else was in your relationship would you be worried for them?",
    'telephone':"He triangulated us a lot. So he would say, oh, mom's stupid or oh, mom is this or oh, mom's that. And then I remember one time with our, so my daughter's older and I remember one time my daughter was maybe two and they were sitting playing a game on the floor and I walked into the room and he said, tell mommy to go away. And she's like, mommy, go away",
};

function initScene() {
    const container = document.getElementById('scene-container');

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xeeeeee);

    // Set up first-person camera
    camera = new THREE.PerspectiveCamera(
        75,  // FOV
        window.innerWidth / window.innerHeight,
        0.1,
        1000
    );
    
    // Set initial camera position and height
    camera.position.set(0, cameraHeight, 5);
    camera.lookAt(0, cameraHeight, 0);

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

    // Add keyboard controls
    document.addEventListener('keydown', onKeyDown);
    document.addEventListener('keyup', onKeyUp);

    // Handle window resize
    window.addEventListener('resize', onWindowResize, false);
    
    // Load local models
    loadLocalModels();
}

function createHighlightMaterial(originalMaterial) {
    if (Array.isArray(originalMaterial)) {
        return originalMaterial.map(mat => {
            const highlightMat = mat.clone();
            highlightMat.emissive = new THREE.Color(0x666666);
            highlightMat.emissiveIntensity = 0.5;
            return highlightMat;
        });
    } else {
        const highlightMat = originalMaterial.clone();
        highlightMat.emissive = new THREE.Color(0x666666);
        highlightMat.emissiveIntensity = 0.5;
        return highlightMat;
    }
}

function onKeyDown(event) {
    switch(event.code) {
        case 'ArrowUp':
        case 'KeyW':
            moveForward = true;
            break;
        case 'ArrowDown':
        case 'KeyS':
            moveBackward = true;
            break;
        case 'ArrowLeft':
        case 'KeyA':
            rotateLeft = true;
            break;
        case 'ArrowRight':
        case 'KeyD':
            rotateRight = true;
            break;
    }
}

function onKeyUp(event) {
    switch(event.code) {
        case 'ArrowUp':
        case 'KeyW':
            moveForward = false;
            break;
        case 'ArrowDown':
        case 'KeyS':
            moveBackward = false;
            break;
        case 'ArrowLeft':
        case 'KeyA':
            rotateLeft = false;
            break;
        case 'ArrowRight':
        case 'KeyD':
            rotateRight = false;
            break;
    }
}

// Mouse look controls
let rotationSpeed = 0.002;
function onMouseMove(event) {
    if (document.pointerLockElement === container) {
        camera.rotation.y -= event.movementX * rotationSpeed;
    }
}

function updateCamera() {
    // Handle rotation
    if (rotateLeft) {
        camera.rotation.y += rotateSpeed;
    }
    if (rotateRight) {
        camera.rotation.y -= rotateSpeed;
    }
    
    // Get forward direction
    const direction = new THREE.Vector3();
    camera.getWorldDirection(direction);
    
    // Handle movement
    if (moveForward) {
        camera.position.add(direction.multiplyScalar(moveSpeed));
    }
    if (moveBackward) {
        camera.position.add(direction.multiplyScalar(-moveSpeed));
    }
    
    // Maintain fixed height
    camera.position.y = cameraHeight;
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

            // Store the object type and original materials
            model.userData = {
                type: folderName,
                originalMaterials: []
            };

            // Store original materials for each mesh
            model.traverse((child) => {
                if (child.isMesh) {
                    child.userData.originalMaterial = child.material;
                    model.userData.originalMaterials.push({
                        mesh: child,
                        material: child.material
                    });
                }
            });


            scene.add(model);
            objects.push(model);
        },
        undefined,
        function(error) {
            console.error(`Error loading model:`, error);
        }
    );
}

function checkObjectProximity() {
    const interactiveObjects = objects.filter(obj => 
        ['gift_box_with_a_ribbons', 'mirror', 'modern_side_lamp_and_stand', 
         'radio_broadcaster', 'telephone', 'coffee_table'].includes(obj.userData.type)
    );

    let closestObject = null;
    let closestDistance = Infinity;

    interactiveObjects.forEach(obj => {
        const distance = camera.position.distanceTo(obj.position);
        
        if (distance < INTERACTION_DISTANCE && distance < closestDistance) {
            closestDistance = distance;
            closestObject = obj;
        }
    });

    // Handle highlighting and overlay
    if (closestObject !== highlightedObject) {
        // Remove highlight from previous object
        if (highlightedObject) {
            highlightedObject.userData.originalMaterials.forEach(({ mesh, material }) => {
                mesh.material = material;
            });
            document.getElementById('object-overlay').classList.add('hidden');
        }

        // Add highlight to new object
        if (closestObject) {
            closestObject.traverse((child) => {
                if (child.isMesh) {
                    child.material = createHighlightMaterial(child.userData.originalMaterial);
                }
            });
            
            // Show text overlay
            const overlay = document.getElementById('object-overlay');
            const description = document.getElementById('object-description');
            description.textContent = objectDescriptions[closestObject.userData.type];
            overlay.classList.remove('hidden');
        }

        highlightedObject = closestObject;
    }
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
    updateCamera();
    checkObjectProximity();
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
