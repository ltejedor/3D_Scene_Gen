let camera, scene, renderer, controls;
let moveForward = false;
let moveBackward = false;
let moveLeft = false;
let moveRight = false;
let canJump = false;
let prevTime = performance.now();
let velocity = new THREE.Vector3();
let direction = new THREE.Vector3();
let stories = [];
let spheres = [];

async function init() {
    // Load stories data
    const response = await fetch('stories.json');
    stories = await response.json();

    // Scene setup
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x88ccff); // Light blue sky
    scene.fog = new THREE.Fog(0x88ccff, 0, 100);

    // Camera setup
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.y = 2; // Eye level

    // Renderer setup
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.shadowMap.enabled = true;
    document.body.appendChild(renderer.domElement);

    // Controls setup
    controls = new THREE.PointerLockControls(camera, document.body);

    // Click to start
    document.addEventListener('click', function() {
        if (!controls.isLocked) {
            controls.lock();
        }
    });

    // Movement
    document.addEventListener('keydown', onKeyDown);
    document.addEventListener('keyup', onKeyUp);

    // Ground
    const groundGeometry = new THREE.PlaneGeometry(200, 200);
    const groundMaterial = new THREE.MeshLambertMaterial({ color: 0x567d46 }); // Garden green
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

    // Create story spheres
    createSpheres();

    // Start animation loop
    animate();
}

function createSpheres() {
    const sphereGeometry = new THREE.SphereGeometry(0.5, 32, 32);
    const sphereMaterial = new THREE.MeshPhongMaterial({
        color: 0x3498db,
        emissive: 0x2980b9,
        emissiveIntensity: 0.2,
        shininess: 100
    });

    stories.forEach((story, index) => {
        const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial.clone());
        
        // Use TSNE1 and TSNE2 for x and z coordinates
        sphere.position.x = story.TSNE1 * 2; // Scale the positions as needed
        sphere.position.z = story.TSNE2 * 2;
        sphere.position.y = 1; // Consistent height

        sphere.castShadow = true;
        sphere.receiveShadow = true;
        
        // Store the story content with the sphere
        sphere.userData.content = story.content;
        sphere.userData.index = index;

        spheres.push(sphere);
        scene.add(sphere);
    });

    // Add click interaction
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    window.addEventListener('click', (event) => {
        if (!controls.isLocked) return;

        raycaster.setFromCamera({ x: 0, y: 0 }, camera);
        const intersects = raycaster.intersectObjects(spheres);

        if (intersects.length > 0) {
            const sphere = intersects[0].object;
            const tooltip = document.getElementById('tooltip');
            tooltip.style.display = 'block';
            tooltip.style.left = '50%';
            tooltip.style.top = '50%';
            tooltip.style.transform = 'translate(-50%, -50%)';
            tooltip.textContent = sphere.userData.content;

            // Highlight the selected sphere
            sphere.material.emissiveIntensity = 0.8;
            setTimeout(() => {
                sphere.material.emissiveIntensity = 0.2;
            }, 1000);
        } else {
            document.getElementById('tooltip').style.display = 'none';
        }
    });
}

function onKeyDown(event) {
    switch (event.code) {
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
            moveLeft = true;
            break;
        case 'ArrowRight':
        case 'KeyD':
            moveRight = true;
            break;
    }
}

function onKeyUp(event) {
    switch (event.code) {
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
            moveLeft = false;
            break;
        case 'ArrowRight':
        case 'KeyD':
            moveRight = false;
            break;
    }
}

function animate() {
    requestAnimationFrame(animate);

    if (controls.isLocked) {
        const time = performance.now();
        const delta = (time - prevTime) / 1000;

        velocity.x -= velocity.x * 10.0 * delta;
        velocity.z -= velocity.z * 10.0 * delta;

        direction.z = Number(moveForward) - Number(moveBackward);
        direction.x = Number(moveRight) - Number(moveLeft);
        direction.normalize();

        if (moveForward || moveBackward) velocity.z -= direction.z * 400.0 * delta;
        if (moveLeft || moveRight) velocity.x -= direction.x * 400.0 * delta;

        controls.moveRight(-velocity.x * delta);
        controls.moveForward(-velocity.z * delta);

        prevTime = time;
    }

    renderer.render(scene, camera);
}

// Handle window resizing
function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

window.addEventListener('resize', onWindowResize, false);

init();