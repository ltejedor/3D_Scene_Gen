let scene, camera, renderer;
let spheres = [];
let moveForward = false;
let moveBackward = false;
let rotateLeft = false;
let rotateRight = false;
const moveSpeed = 0.1;
const rotateSpeed = 0.03;
const cameraHeight = 0.8;
let highlightedSphere = null;
const INTERACTION_DISTANCE = 2;

async function init() {
    const container = document.getElementById('scene-container');
    
    // Load stories data
    const response = await fetch('stories.json');
    const stories = await response.json();

    // Scene setup
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x88ccff);
    scene.fog = new THREE.Fog(0x88ccff, 0, 100);

    // Camera setup
    camera = new THREE.PerspectiveCamera(
        75,
        window.innerWidth / window.innerHeight,
        0.1,
        1000
    );
    camera.position.set(0, cameraHeight, 5);
    camera.lookAt(0, cameraHeight, 0);

    // Renderer setup
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // Ground with repeating texture
    const textureLoader = new THREE.TextureLoader();
    const grassTexture = textureLoader.load('../assets/grass.png');
    grassTexture.wrapS = THREE.RepeatWrapping;
    grassTexture.wrapT = THREE.RepeatWrapping;
    grassTexture.repeat.set(50, 50); // Adjust these numbers to control how many times the texture repeats
    
    const groundGeometry = new THREE.PlaneGeometry(200, 200);
    const groundMaterial = new THREE.MeshLambertMaterial({ 
        map: grassTexture
    });
    const ground = new THREE.Mesh(groundGeometry, groundMaterial);
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    scene.add(ground);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0x666666);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(5, 10, 5);
    directionalLight.castShadow = true;
    scene.add(directionalLight);

    // Add grid helper
    const gridHelper = new THREE.GridHelper(20, 20);
    scene.add(gridHelper);

    // Controls
    document.addEventListener('keydown', onKeyDown);
    document.addEventListener('keyup', onKeyUp);
    window.addEventListener('resize', onWindowResize, false);

    // Load flower texture before creating spheres
    const flowerTexture = await new Promise((resolve) => {
        textureLoader.load('../assets/flowers.png', resolve);
    });
    flowerTexture.wrapS = THREE.RepeatWrapping;
    flowerTexture.wrapT = THREE.RepeatWrapping;
    flowerTexture.repeat.set(1.5, 1.5); // Adjust repeat value as needed

    createSpheres(stories, flowerTexture);
    animate();
}


function createSpheres(stories, flowerTexture) {
    const sphereGeometry = new THREE.SphereGeometry(0.3, 10, 10);
    const sphereMaterial = new THREE.MeshPhongMaterial({
        map: flowerTexture,
        shininess: 5,
        emissiveMap: flowerTexture,
        emissiveIntensity: 0
    });

    stories.forEach((story, index) => {
        const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial.clone());
        
        // Use TSNE1 for X and TSNE2 for Z coordinates
        sphere.position.x = story.TSNE1 * 2;
        sphere.position.z = story.TSNE2 * 2;
        sphere.position.y = .2;

        sphere.castShadow = true;
        sphere.receiveShadow = true;
        
        sphere.userData = {
            content: story.content,
            index: index,
            originalMaterial: sphere.material.clone(),
            type: 'story_sphere'
        };

        spheres.push(sphere);
        scene.add(sphere);
    });
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

function checkProximity() {
    let closestSphere = null;
    let closestDistance = Infinity;

    spheres.forEach(sphere => {
        const distance = camera.position.distanceTo(sphere.position);
        
        if (distance < INTERACTION_DISTANCE && distance < closestDistance) {
            closestDistance = distance;
            closestSphere = sphere;
        }
    });

    // Handle highlighting and overlay
    if (closestSphere !== highlightedSphere) {
        // Remove highlight from previous sphere
        if (highlightedSphere) {
            highlightedSphere.material = highlightedSphere.userData.originalMaterial.clone();
            document.getElementById('object-overlay').classList.add('hidden');
        }

        // Add highlight to new sphere
        if (closestSphere) {
            const highlightMaterial = closestSphere.userData.originalMaterial.clone();
            highlightMaterial.emissive = new THREE.Color(0x666666);
            highlightMaterial.emissiveIntensity = 0.5;
            closestSphere.material = highlightMaterial;
            
            // Show text overlay
            const overlay = document.getElementById('object-overlay');
            const description = document.getElementById('object-description');
            description.textContent = closestSphere.userData.content;
            overlay.classList.remove('hidden');
        }

        highlightedSphere = closestSphere;
    }
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
    requestAnimationFrame(animate);
    updateCamera();
    checkProximity();
    renderer.render(scene, camera);
}

init();