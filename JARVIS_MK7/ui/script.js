/* ==========================================================
   J.A.R.V.I.S. MARK VII - TACTICAL IRON MAN HUD CORE SCRIPT
   3D Glowing Iron Man Helmet / Mask Wireframe Mesh (Three.js)
   Real-Time Speech Lip-Sync, Angled Slit Eyes & Multi-Modal File Hub
   Exclusively built for Administrator: Manuja (මනුජ)
   ========================================================== */

let scene, camera, renderer;
let headGroup, upperHelmetMesh, upperHelmetHull, jawGroup, jawMesh, jawHull;
let vocalCore, haloRing1, haloRing2, particlePoints;
let leftSlitEyeGroup, rightSlitEyeGroup, leftSlitCore, rightSlitCore;
let leftSlitBorder, rightSlitBorder;
let goldFaceplateContour, foreheadArcCore;
let leftTempleDisc, rightTempleDisc;

// State management
let currentEmotion = "SPEAK";
let faceState = "IDLE"; // IDLE, LISTENING, THINKING, SPEAKING, ALERT
let currentTheme = "cyan";

// Animation & Expression parameters
let currentMouthOpen = 0.0;
let targetLipSyncAmplitude = 0.0;
let smileAmount = 0.0;
let concernAmount = 0.0;
let alertAmount = 0.0;
let clock = 0;

// Theme color definitions matching specifications
const THEME_COLORS = {
  cyan: 0x00e5ff,   // Idle / Listening
  green: 0x00ffaa,  // Speaking
  gold: 0xffd700,   // [LAUGH] / Thinking / Gold Faceplate
  blue: 0x0055ff,   // [CRY] / Concern
  red: 0xff0033     // Unauthorized / Intruder Alert
};

// Shared dynamic materials
let wireframeMaterial, innerHullMaterial, goldEdgeMaterial;
let slitEyeCoreMaterial, slitEyeBorderMaterial;
let vocalCoreMaterial, haloMaterial, particleMaterial;

function initMaterials() {
  const initColor = THEME_COLORS.cyan;

  // 1. Neon Glowing Cyan Titanium Wireframe
  wireframeMaterial = new THREE.MeshBasicMaterial({
    color: initColor,
    wireframe: true,
    transparent: true,
    opacity: 0.88
  });

  // 2. Dark Titanium / Carbon-Fiber Base Hull (Opaque Depth)
  innerHullMaterial = new THREE.MeshBasicMaterial({
    color: 0x050c14,
    transparent: true,
    opacity: 0.72,
    side: THREE.DoubleSide
  });

  // 3. Iconic Gold Arc-Reactor Faceplate Edge Material
  goldEdgeMaterial = new THREE.LineBasicMaterial({
    color: THEME_COLORS.gold,
    linewidth: 3,
    transparent: true,
    opacity: 0.95
  });

  // 4. Glowing Angled Slit Eyes Core (Bright White-Cyan)
  slitEyeCoreMaterial = new THREE.MeshBasicMaterial({
    color: 0xffffff,
    transparent: true,
    opacity: 0.95,
    side: THREE.DoubleSide
  });

  // 5. Slit Eye Tech Border
  slitEyeBorderMaterial = new THREE.LineBasicMaterial({
    color: initColor,
    linewidth: 2,
    transparent: true,
    opacity: 0.95
  });

  // 6. Vocal Core inside mouth aperture
  vocalCoreMaterial = new THREE.MeshBasicMaterial({
    color: THEME_COLORS.green,
    wireframe: true,
    transparent: true,
    opacity: 0.45
  });

  // 7. Holographic Orbiting Tech Rings
  haloMaterial = new THREE.MeshBasicMaterial({
    color: initColor,
    wireframe: true,
    transparent: true,
    opacity: 0.28
  });

  // 8. Cybernetic Data Particles
  particleMaterial = new THREE.PointsMaterial({
    size: 0.28,
    color: initColor,
    transparent: true,
    opacity: 0.75
  });
}

// ---------------- 3D IRON MAN HELMET MESH GEOMETRY BUILDER ---------------- //

/**
 * Computes 3D coordinates for an iconic Iron Man MK-VII Helmet:
 * - Chiseled cranial dome with centerline crest ridge.
 * - Angular eyebrow overhang and deep recessed angled eye sockets.
 * - Sharp triangular nose/filter bridge.
 * - Angular cheek flares and mandibular bevels.
 * - Prominent chiseled chin guard.
 */
function computeIronManPoint(xNorm, yNorm) {
  let x0 = xNorm * 3.3;
  let y0 = yNorm * 4.3;

  // Base 3D aerodynamic helmet dome curvature
  let z0 = 3.65 * Math.cos(xNorm * Math.PI / 2.15) * Math.cos(yNorm * Math.PI / 2.45);

  // Cranium Centerline Crest Ridge (Iron Man helmet apex)
  const crest = Math.max(0, 1 - Math.abs(x0) / 0.55) * Math.max(0, (y0 - 0.2) / 3.0);
  z0 += crest * 0.65;

  // Forehead Brow Plate Overhang (Angled sharp brow)
  if (y0 >= 0.7 && y0 <= 1.6) {
    const browBevel = Math.max(0, 1 - Math.abs(y0 - 1.1) / 0.45) * Math.max(0, 1 - Math.abs(x0) / 2.4);
    z0 += browBevel * 0.95;
  }

  // Recessed Angled Eye Sockets (Iron Man eye indentation)
  if (y0 >= 0.1 && y0 <= 0.8) {
    const eyeDistL = Math.hypot(x0 - (-1.25), y0 - 0.45);
    const eyeDistR = Math.hypot(x0 - 1.25, y0 - 0.45);
    const socketL = Math.max(0, 1 - eyeDistL / 0.95);
    const socketR = Math.max(0, 1 - eyeDistR / 0.95);
    z0 -= (socketL + socketR) * 1.25;
  }

  // Sharp Triangular Nose / Center Filter Plate
  if (y0 >= -0.7 && y0 <= 0.5) {
    const noseWidth = 0.32 + 0.32 * (0.5 - y0) / 1.2;
    const nose = Math.max(0, 1 - Math.abs(x0) / noseWidth) * Math.max(0, 1 - Math.abs(y0 - (-0.1)) / 0.65);
    z0 += nose * 1.55;
  }

  // Chiseled Cheek Flares (Zygomatic armor plates)
  if (y0 >= -1.1 && y0 <= 0.3) {
    const cheekDist = Math.hypot(Math.abs(x0) - 2.15, y0 - (-0.3));
    const cheek = Math.max(0, 1 - cheekDist / 1.05);
    z0 += cheek * 0.75;
    x0 += Math.sign(x0) * cheek * 0.35;
  }

  // Upper Mouth Intake Plate
  if (y0 >= -1.35 && y0 < -0.7) {
    const mouthUpper = Math.max(0, 1 - Math.abs(x0) / 1.3) * Math.max(0, 1 - Math.abs(y0 - (-1.0)) / 0.3);
    z0 += mouthUpper * 0.55;
  }

  // Angular Mandible & Chiseled Chin Plate
  if (y0 <= -1.35) {
    const chinWidth = 1.25 + 0.25 * (y0 - (-1.35));
    const chin = Math.max(0, 1 - Math.abs(x0) / chinWidth) * Math.max(0, 1 - Math.abs(y0 - (-2.7)) / 1.2);
    z0 += chin * 1.45;
  }

  return { x: x0, y: y0, z: z0 };
}

function buildGridGeometry(xCount, startYRow, endYRow, totalYRows, pivotY = 0, pivotZ = 0) {
  const geometry = new THREE.BufferGeometry();
  const vertices = [];
  const indices = [];

  const xs = [];
  for (let i = 0; i < xCount; i++) {
    xs.push(-1 + (2 * i) / (xCount - 1));
  }

  const ys = [];
  for (let j = 0; j < totalYRows; j++) {
    ys.push(-1 + (2 * j) / (totalYRows - 1));
  }

  const rowCount = endYRow - startYRow + 1;

  for (let r = 0; r < rowCount; r++) {
    const j = startYRow + r;
    for (let i = 0; i < xCount; i++) {
      const pt = computeIronManPoint(xs[i], ys[j]);
      vertices.push(pt.x, pt.y - pivotY, pt.z - pivotZ);
    }
  }

  for (let r = 0; r < rowCount - 1; r++) {
    for (let i = 0; i < xCount - 1; i++) {
      const a = r * xCount + i;
      const b = r * xCount + (i + 1);
      const c = (r + 1) * xCount + i;
      const d = (r + 1) * xCount + (i + 1);

      indices.push(a, c, b);
      indices.push(b, c, d);
    }
  }

  geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  return geometry;
}

// ---------------- INITIALIZE THREE.JS 3D IRON MAN HUD SCENE ---------------- //

function initThreeCore() {
  const container = document.getElementById('three-canvas-container');
  if (!container) return;

  const width = container.clientWidth || 420;
  const height = container.clientHeight || 420;

  // Scene
  scene = new THREE.Scene();

  // Perspective Camera
  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
  camera.position.set(0, 0, 15.5);

  // WebGL Renderer with High-Performance Anti-Aliasing
  renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: "high-performance" });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  container.innerHTML = '';
  container.appendChild(renderer.domElement);

  initMaterials();

  // Master Head Group
  headGroup = new THREE.Group();
  scene.add(headGroup);

  const NX = 24;
  const NY = 30;
  const JAW_CUT_ROW = 9; // rows 0..9 = lower jaw, 10..29 = upper helmet

  // 1. Upper Helmet Mesh (Titanium Wireframe & Dark Carbon Hull)
  const upperGeo = buildGridGeometry(NX, JAW_CUT_ROW + 1, NY - 1, NY, 0, 0);
  upperHelmetMesh = new THREE.Mesh(upperGeo, wireframeMaterial);
  upperHelmetHull = new THREE.Mesh(upperGeo, innerHullMaterial);
  headGroup.add(upperHelmetMesh);
  headGroup.add(upperHelmetHull);

  // 2. Articulated Lower Jaw & Chin Plate Group
  // Pivot placed at mandibular hinge: (0, -1.15, 0.45)
  const JAW_PIVOT_Y = -1.15;
  const JAW_PIVOT_Z = 0.45;
  jawGroup = new THREE.Group();
  jawGroup.position.set(0, JAW_PIVOT_Y, JAW_PIVOT_Z);

  const jawGeo = buildGridGeometry(NX, 0, JAW_CUT_ROW, NY, JAW_PIVOT_Y, JAW_PIVOT_Z);
  jawMesh = new THREE.Mesh(jawGeo, wireframeMaterial);
  jawHull = new THREE.Mesh(jawGeo, innerHullMaterial);
  jawGroup.add(jawMesh);
  jawGroup.add(jawHull);
  headGroup.add(jawGroup);

  // 3. Iconic Iron Man Golden Faceplate Contour (Arc-Reactor Edge)
  const faceplatePoints = [
    new THREE.Vector3(0, 2.35, 3.45),      // Forehead Peak
    new THREE.Vector3(1.25, 1.85, 3.10),   // Right Brow Apex
    new THREE.Vector3(2.35, 1.45, 2.50),   // Right Temple Edge
    new THREE.Vector3(2.15, -0.05, 2.80),  // Right Cheek Flare
    new THREE.Vector3(1.50, -1.05, 2.55),  // Right Mandibular Cut
    new THREE.Vector3(0.95, -2.15, 2.65),  // Right Chin Corner
    new THREE.Vector3(0, -2.40, 2.75),     // Chin Bottom Apex
    new THREE.Vector3(-0.95, -2.15, 2.65), // Left Chin Corner
    new THREE.Vector3(-1.50, -1.05, 2.55), // Left Mandibular Cut
    new THREE.Vector3(-2.15, -0.05, 2.80), // Left Cheek Flare
    new THREE.Vector3(-2.35, 1.45, 2.50),  // Left Temple Edge
    new THREE.Vector3(-1.25, 1.85, 3.10),  // Left Brow Apex
    new THREE.Vector3(0, 2.35, 3.45)       // Close loop at peak
  ];
  const goldFaceplateGeo = new THREE.BufferGeometry().setFromPoints(faceplatePoints);
  goldFaceplateContour = new THREE.Line(goldFaceplateGeo, goldEdgeMaterial);
  headGroup.add(goldFaceplateContour);

  // 4. Iconic Angled Glowing Slit Eyes (Iron Man HUD Signature)
  function createSlitEye(isLeft) {
    const group = new THREE.Group();
    const sign = isLeft ? -1 : 1;

    // Angled trapezoidal slit corners
    // P0: outer-top, P1: inner-top, P2: inner-bottom, P3: outer-bottom
    const xOuterTop = sign * 1.82;
    const xInnerTop = sign * 0.62;
    const xInnerBot = sign * 0.72;
    const xOuterBot = sign * 1.72;

    const yOuterTop = 0.65;
    const yInnerTop = 0.40;
    const yInnerBot = 0.22;
    const yOuterBot = 0.42;

    const zOuter = 3.05;
    const zInner = 3.30;

    // Slit Core Surface (Planar Quad)
    const slitGeo = new THREE.BufferGeometry();
    const positions = new Float32Array([
      // Triangle 1
      xOuterTop, yOuterTop, zOuter,
      xInnerTop, yInnerTop, zInner,
      xInnerBot, yInnerBot, zInner,
      // Triangle 2
      xOuterTop, yOuterTop, zOuter,
      xInnerBot, yInnerBot, zInner,
      xOuterBot, yOuterBot, zOuter
    ]);
    slitGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    slitGeo.computeVertexNormals();

    const coreMesh = new THREE.Mesh(slitGeo, slitEyeCoreMaterial);
    group.add(coreMesh);

    // Sharp Angled Bezel Line
    const borderPoints = [
      new THREE.Vector3(xOuterTop, yOuterTop, zOuter + 0.02),
      new THREE.Vector3(xInnerTop, yInnerTop, zInner + 0.02),
      new THREE.Vector3(xInnerBot, yInnerBot, zInner + 0.02),
      new THREE.Vector3(xOuterBot, yOuterBot, zOuter + 0.02),
      new THREE.Vector3(xOuterTop, yOuterTop, zOuter + 0.02)
    ];
    const borderGeo = new THREE.BufferGeometry().setFromPoints(borderPoints);
    const borderLine = new THREE.Line(borderGeo, slitEyeBorderMaterial);
    group.add(borderLine);

    return { group: group, core: coreMesh, border: borderLine };
  }

  const leftEyeData = createSlitEye(true);
  const rightEyeData = createSlitEye(false);
  leftSlitEyeGroup = leftEyeData.group;
  rightSlitEyeGroup = rightEyeData.group;
  leftSlitCore = leftEyeData.core;
  rightSlitCore = rightEyeData.core;
  leftSlitBorder = leftEyeData.border;
  rightSlitBorder = rightEyeData.border;
  headGroup.add(leftSlitEyeGroup);
  headGroup.add(rightSlitEyeGroup);

  // 5. Forehead Arc Sensor Diamond
  const foreheadGeo = new THREE.OctahedronGeometry(0.32, 0);
  foreheadArcCore = new THREE.Mesh(foreheadGeo, slitEyeCoreMaterial);
  foreheadArcCore.position.set(0, 2.38, 3.48);
  headGroup.add(foreheadArcCore);

  // 6. Iconic Temple Arc Discs (Ear Pod Plates)
  leftTempleDisc = new THREE.Mesh(new THREE.TorusGeometry(0.55, 0.04, 8, 24), wireframeMaterial);
  leftTempleDisc.position.set(-3.45, 0.15, 0.65);
  leftTempleDisc.rotation.y = Math.PI / 2;
  headGroup.add(leftTempleDisc);

  rightTempleDisc = new THREE.Mesh(new THREE.TorusGeometry(0.55, 0.04, 8, 24), wireframeMaterial);
  rightTempleDisc.position.set(3.45, 0.15, 0.65);
  rightTempleDisc.rotation.y = Math.PI / 2;
  headGroup.add(rightTempleDisc);

  // 7. Vocal Waveform Core (Pulsing inside mouth opening)
  vocalCore = new THREE.Mesh(new THREE.IcosahedronGeometry(0.68, 1), vocalCoreMaterial);
  vocalCore.position.set(0, -1.35, 1.85);
  headGroup.add(vocalCore);

  // 8. Orbiting Holographic HUD Tech Halos (Iron Man Arc Aura)
  haloRing1 = new THREE.Mesh(new THREE.TorusGeometry(6.6, 0.03, 8, 80), haloMaterial);
  haloRing1.rotation.x = Math.PI / 2.3;
  scene.add(haloRing1);

  haloRing2 = new THREE.Mesh(new THREE.TorusGeometry(8.2, 0.02, 8, 80), haloMaterial);
  haloRing2.rotation.y = Math.PI / 3.0;
  scene.add(haloRing2);

  // 9. Floating Cybernetic Data Dust Particles
  const particleGeo = new THREE.BufferGeometry();
  const particleCount = 180;
  const posArray = new Float32Array(particleCount * 3);
  for (let i = 0; i < particleCount * 3; i++) {
    posArray[i] = (Math.random() - 0.5) * 34;
  }
  particleGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
  particlePoints = new THREE.Points(particleGeo, particleMaterial);
  scene.add(particlePoints);

  // Window Resize Listener
  window.addEventListener('resize', onWindowResize);

  // Kickoff 60 FPS Render Loop
  animateCyberFace();
}

function onWindowResize() {
  const container = document.getElementById('three-canvas-container');
  if (!container || !renderer || !camera) return;
  const width = container.clientWidth || window.innerWidth;
  const height = container.clientHeight || window.innerHeight;
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);

  // Proportional mesh scaling to fill center viewport elegantly in fullscreen
  if (headGroup) {
    const isFullScreen = (window.innerWidth > 700 && window.innerHeight > 650);
    const targetScale = isFullScreen ? 1.35 : 1.0;
    headGroup.scale.set(targetScale, targetScale, targetScale);
  }
}

// ---------------- 60 FPS ANIMATION & REAL-TIME LIP-SYNC LOOP ---------------- //

function animateCyberFace() {
  requestAnimationFrame(animateCyberFace);
  clock += 0.022;

  // 1. Real-Time Lip-Sync & Lower Jaw Articulation
  if (faceState === "SPEAKING") {
    // If real-time audio amplitude ticks are streamed from Python, follow them closely
    if (targetLipSyncAmplitude > 0.01) {
      currentMouthOpen = THREE.MathUtils.lerp(currentMouthOpen, targetLipSyncAmplitude, 0.42);
    } else {
      // Natural procedural speech cadence simulating Sinhala vowel-consonant bursts
      const cadence = Math.max(0,
        Math.sin(clock * 16.0) * 0.48 +
        Math.sin(clock * 26.0) * 0.25 +
        Math.sin(clock * 8.5) * 0.20
      );
      currentMouthOpen = THREE.MathUtils.lerp(currentMouthOpen, cadence, 0.35);
    }

    // Lower Jaw Plate articulates down around mandibular hinge
    if (jawGroup) {
      jawGroup.rotation.x = currentMouthOpen * 0.32;
    }

    // Vocal core pulses in scale and luminescence
    if (vocalCore) {
      vocalCore.scale.setScalar(1.0 + currentMouthOpen * 2.2);
      vocalCore.rotation.x += 0.08;
      vocalCore.rotation.y += 0.12;
      vocalCore.material.opacity = 0.25 + currentMouthOpen * 0.75;
    }

    // Slit eyes maintain bright steady luminescence when speaking
    if (slitEyeCoreMaterial) {
      slitEyeCoreMaterial.opacity = 0.98;
    }
  } else {
    // Smooth return to closed resting position
    currentMouthOpen = THREE.MathUtils.lerp(currentMouthOpen, 0.0, 0.22);
    if (jawGroup) {
      jawGroup.rotation.x = currentMouthOpen * 0.32;
    }
    if (vocalCore) {
      vocalCore.scale.setScalar(1.0);
      vocalCore.material.opacity = 0.15;
    }

    // 2. Slit Eyes Breathing Pulse in LISTENING state
    if (faceState === "LISTENING") {
      const eyePulse = 0.82 + 0.18 * Math.sin(clock * 5.0);
      if (slitEyeCoreMaterial) {
        slitEyeCoreMaterial.opacity = eyePulse;
      }
      const scalePulse = 1.0 + 0.08 * Math.sin(clock * 5.0);
      if (leftSlitEyeGroup) leftSlitEyeGroup.scale.set(1.0, scalePulse, 1.0);
      if (rightSlitEyeGroup) rightSlitEyeGroup.scale.set(1.0, scalePulse, 1.0);
    } else {
      if (slitEyeCoreMaterial) slitEyeCoreMaterial.opacity = 0.85;
      if (leftSlitEyeGroup) leftSlitEyeGroup.scale.set(1.0, 1.0, 1.0);
      if (rightSlitEyeGroup) rightSlitEyeGroup.scale.set(1.0, 1.0, 1.0);
    }
  }

  // 3. Emotional State Morphing
  const targetSmile = (currentEmotion === "LAUGH") ? 1.0 : 0.0;
  smileAmount = THREE.MathUtils.lerp(smileAmount, targetSmile, 0.1);

  const targetConcern = (currentEmotion === "CRY") ? 1.0 : 0.0;
  concernAmount = THREE.MathUtils.lerp(concernAmount, targetConcern, 0.1);

  const targetAlert = (faceState === "ALERT" || currentEmotion === "ALERT") ? 1.0 : 0.0;
  alertAmount = THREE.MathUtils.lerp(alertAmount, targetAlert, 0.15);

  // 4. Autonomous Iron Man Helmet Floating & Physics
  const floatY = Math.sin(clock * 1.3) * 0.16;
  const floatYaw = Math.sin(clock * 0.75) * 0.045;
  const floatPitch = Math.cos(clock * 0.95) * 0.03;

  let targetRotX = floatPitch;
  let targetRotY = floatYaw;
  let targetRotZ = 0.0;
  let targetPosY = floatY;

  if (currentEmotion === "LAUGH") {
    // Cheerful rhythmic nod
    targetPosY += Math.abs(Math.sin(clock * 9.0)) * 0.22;
    targetRotX += Math.sin(clock * 9.0) * 0.05;
  } else if (currentEmotion === "CRY") {
    // Empathetic downward tilt
    targetRotX += 0.12;
    targetPosY += Math.sin(clock * 0.8) * 0.08;
  } else if (faceState === "ALERT" || currentEmotion === "ALERT") {
    // Vigorous lateral head shake
    targetRotY += Math.sin(clock * 22.0) * 0.35;
  } else if (faceState === "LISTENING") {
    // Attentive head tilt towards Sir
    targetRotZ += 0.05 * Math.sin(clock * 0.6) + 0.04;
    targetRotY += 0.05;
  } else if (faceState === "SPEAKING") {
    // Subtle nod with speech cadence
    targetRotX += Math.sin(clock * 7.5) * 0.035;
  }

  if (headGroup) {
    headGroup.rotation.x = THREE.MathUtils.lerp(headGroup.rotation.x, targetRotX, 0.08);
    headGroup.rotation.y = THREE.MathUtils.lerp(headGroup.rotation.y, targetRotY, 0.08);
    headGroup.rotation.z = THREE.MathUtils.lerp(headGroup.rotation.z, targetRotZ, 0.08);
    headGroup.position.y = THREE.MathUtils.lerp(headGroup.position.y, targetPosY, 0.08);
  }

  // 5. Halos & Tech Rings Rotation
  if (haloRing1) {
    haloRing1.rotation.z += 0.003;
  }
  if (haloRing2) {
    haloRing2.rotation.z -= 0.002;
  }
  if (particlePoints) {
    particlePoints.rotation.y += 0.0008;
  }

  // 6. Sync DOM Waveform Bars with speech
  const waveBars = document.querySelectorAll('#waveform .wave-bar');
  if (waveBars.length > 0) {
    waveBars.forEach((bar, idx) => {
      if (faceState === "SPEAKING" || currentMouthOpen > 0.05) {
        const h = 6 + Math.abs(Math.sin(clock * 14 + idx * 0.45)) * currentMouthOpen * 24;
        bar.style.height = `${h}px`;
      } else {
        bar.style.height = "6px";
      }
    });
  }

  // Render 3D Scene
  if (renderer && scene && camera) {
    renderer.render(scene, camera);
  }
}

// ---------------- THEME & COLOR UPDATER ---------------- //

function applyThemeColor(colorKey) {
  currentTheme = colorKey;
  const hex = THEME_COLORS[colorKey] || THEME_COLORS.cyan;

  // Update Three.js materials
  if (wireframeMaterial) wireframeMaterial.color.setHex(hex);
  if (slitEyeBorderMaterial) slitEyeBorderMaterial.color.setHex(hex);
  if (haloMaterial) haloMaterial.color.setHex(hex);
  if (particleMaterial) particleMaterial.color.setHex(hex);

  // Update Body Theme Class
  document.body.className = `theme-${colorKey}`;
}

// ---------------- PUBLIC PYTHON-TO-JAVASCRIPT IPC API ---------------- //

/**
 * Updates 3D Iron Man Helmet State and Facial Emotion.
 * Invoked directly from Python backend (app.py & voice_engine.py).
 * @param {string} state "SPEAKING", "LISTENING", "THINKING", "ALERT", or "IDLE"
 * @param {string} emotion "SPEAK", "LAUGH", "CRY", "ALERT", or "NORMAL"
 */
window.setFaceState = function(state, emotion) {
  if (state) {
    faceState = state.toUpperCase();
  }

  const badgeText = document.getElementById('state-text');
  const badgeIcon = document.getElementById('state-icon');

  if (faceState === "SPEAKING") {
    const emo = (emotion || currentEmotion || "SPEAK").toUpperCase();
    currentEmotion = emo;
    document.body.classList.add("speaking");

    if (emo === "LAUGH") {
      applyThemeColor("gold");
      if (badgeText) badgeText.innerText = "● J.A.R.V.I.S. [LAUGH]...";
      if (badgeIcon) badgeIcon.innerText = "😄";
    } else if (emo === "CRY") {
      applyThemeColor("blue");
      if (badgeText) badgeText.innerText = "● J.A.R.V.I.S. [CONCERN]...";
      if (badgeIcon) badgeIcon.innerText = "💧";
    } else {
      applyThemeColor("green");
      if (badgeText) badgeText.innerText = "● J.A.R.V.I.S. SPEAKING...";
      if (badgeIcon) badgeIcon.innerText = "🔊";
    }
  } else if (faceState === "THINKING") {
    currentEmotion = "SPEAK";
    document.body.classList.remove("speaking");
    applyThemeColor("gold");
    if (badgeText) badgeText.innerText = "● PROCESSING...";
    if (badgeIcon) badgeIcon.innerText = "🧠";
  } else if (faceState === "ALERT") {
    currentEmotion = "ALERT";
    document.body.classList.remove("speaking");
    applyThemeColor("red");
    if (badgeText) badgeText.innerText = "● INTRUDER DETECTED // LOCKDOWN";
    if (badgeIcon) badgeIcon.innerText = "🚨";
  } else {
    // LISTENING / IDLE
    currentEmotion = "SPEAK";
    document.body.classList.remove("speaking");
    applyThemeColor("cyan");
    if (badgeText) badgeText.innerText = "● LISTENING TO SIR (MANUJA)...";
    if (badgeIcon) badgeIcon.innerText = "🎙️";
  }
};

/**
 * Pushes real-time audio amplitude for lip-sync jaw articulation.
 * Invoked directly from Python during TTS playback ticks.
 * @param {number} amplitude 0.0 (closed) to 1.0 (fully articulated open)
 */
window.setFaceLipSync = function(amplitude) {
  targetLipSyncAmplitude = Math.max(0, Math.min(1.0, parseFloat(amplitude) || 0));
};

/**
 * Backwards-compatible emotion setter.
 */
window.setEmotionState = function(state) {
  const upper = (state || "").toUpperCase();
  if (upper === "SPEAK" || upper === "SPEAKING") {
    window.setFaceState("SPEAKING", "SPEAK");
  } else if (upper === "LAUGH") {
    window.setFaceState("SPEAKING", "LAUGH");
  } else if (upper === "CRY") {
    window.setFaceState("SPEAKING", "CRY");
  } else if (upper === "THINKING" || upper === "PROCESSING") {
    window.setFaceState("THINKING");
  } else if (upper === "ALERT" || upper === "UNAUTHORIZED") {
    window.setFaceState("ALERT", "ALERT");
  } else {
    window.setFaceState("LISTENING");
  }
};

/**
 * Updates telemetry metrics from psutil.
 */
window.updateStats = function(data) {
  if (!data) return;

  // CPU
  const cpuPct = Math.round(data.cpu_percent || 0);
  const cpuVal = document.getElementById('cpu-val');
  const cpuBar = document.getElementById('cpu-bar');
  if (cpuVal) cpuVal.innerText = `${cpuPct}%`;
  if (cpuBar) cpuBar.style.width = `${cpuPct}%`;

  // RAM
  const ramPct = Math.round(data.ram_percent || 0);
  const ramVal = document.getElementById('ram-val');
  const ramBar = document.getElementById('ram-bar');
  const ramSub = document.getElementById('ram-sub');
  if (ramVal) ramVal.innerText = `${ramPct}%`;
  if (ramBar) ramBar.style.width = `${ramPct}%`;
  if (ramSub) ramSub.innerText = `${data.ram_used_gb || 0} GB / ${data.ram_total_gb || 0} GB Used`;

  // Battery
  const batPct = Math.round(data.battery_percent || 100);
  const batVal = document.getElementById('battery-val');
  const batBar = document.getElementById('battery-bar');
  const batSub = document.getElementById('battery-sub');
  if (batVal) batVal.innerText = `${batPct}%`;
  if (batBar) batBar.style.width = `${batPct}%`;
  if (batSub) {
    batSub.innerText = data.power_plugged ? "A/C Connected (Charging)" : "On Battery Power";
  }

  // Disk & Net
  const diskVal = document.getElementById('disk-val');
  const netVal = document.getElementById('net-val');
  if (diskVal) diskVal.innerText = `${Math.round(data.disk_percent || 0)}%`;
  if (netVal) netVal.innerText = `${data.net_sent_mb || 0} / ${data.net_recv_mb || 0} MB`;
};

/**
 * Appends message to Sinhala terminal activity stream.
 * @param {string} sender "SYSTEM", "J.A.R.V.I.S.", "MANUJA", or "ALERT"
 * @param {string} message Sinhala text content
 * @param {string} type "system", "ai", "user", or "alert"
 */
window.appendLog = function(sender, message, type = "ai") {
  const terminal = document.getElementById('terminal-body');
  if (!terminal) return;

  const now = new Date();
  const timeStr = `[${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}]`;

  const msgDiv = document.createElement('div');
  msgDiv.className = `term-msg msg-${type}`;

  msgDiv.innerHTML = `
    <span class="msg-time">${timeStr}</span>
    <span class="msg-sender">${sender}:</span>
    <span class="msg-content">${escapeHtml(message)}</span>
  `;

  terminal.appendChild(msgDiv);
  terminal.scrollTop = terminal.scrollHeight;
};

/**
 * Updates Biometric Gate status.
 */
window.setBiometricStatus = function(isVerified, username = "MANUJA", detail = "") {
  const card = document.getElementById('security-badge-card');
  const title = document.getElementById('sec-user-title');
  const status = document.getElementById('sec-user-status');
  const icon = document.getElementById('sec-icon-status');
  const sysStatus = document.getElementById('system-status-text');

  if (isVerified) {
    if (card) card.classList.remove('intruder-alert');
    if (title) title.innerText = `ADMINISTRATOR: ${username}`;
    if (status) status.innerText = detail || "BIOMETRIC MATCH CONFIRMED";
    if (icon) icon.innerText = "🛡️";
    if (sysStatus) sysStatus.innerText = "SYSTEM SECURE // BIOMETRICS ACTIVE";
  } else {
    if (card) card.classList.add('intruder-alert');
    if (title) title.innerText = "SECURITY BREACH: UNKNOWN USER";
    if (status) status.innerText = detail || "INTRUDER DETECTED // LOCKDOWN";
    if (icon) icon.innerText = "🚨";
    if (sysStatus) sysStatus.innerText = "LOCKDOWN ACTIVE // ACCESS DENIED";
    window.setFaceState("ALERT", "ALERT");
  }
};

// ---------------- MULTI-MODAL DRAG & DROP FILE HUB ---------------- //

function triggerFileInput() {
  const input = document.getElementById('hud-file-input');
  if (input) input.click();
}

function handleFileSelected(event) {
  const files = event.target.files;
  if (files && files.length > 0) {
    processUploadedFile(files[0]);
  }
}

function processUploadedFile(file) {
  if (!file) return;

  const validExts = ['.jpg', '.jpeg', '.png', '.pdf', '.py', '.txt', '.json'];
  const nameLower = file.name.toLowerCase();
  const isValid = validExts.some(ext => nameLower.endsWith(ext));

  if (!isValid) {
    window.appendLog("SYSTEM", `ගොනු ආකෘතිය වලංගු නොවේ: ${file.name}. කරුණාකර .jpg, .png, .pdf, .py, .txt, .json ගොනුවක් ලබා දෙන්න.`, "alert");
    return;
  }

  window.appendLog("MANUJA", `ගොනුව විශ්ලේෂණය සඳහා යොමු කරන ලදී: ${file.name}`, "user");
  window.setFaceState("THINKING");

  const reader = new FileReader();
  reader.onload = function(e) {
    const base64Data = e.target.result;
    if (window.pywebview && window.pywebview.api && window.pywebview.api.on_file_upload) {
      window.pywebview.api.on_file_upload(file.name, base64Data);
    } else {
      console.log("[FILE HUB] pywebview API not mounted yet for file upload.");
    }
  };
  reader.readAsDataURL(file);
}

function setupDropzone() {
  const dropzone = document.getElementById('hud-file-dropzone');
  if (!dropzone) return;

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('drag-active');
    }, false);
  });

  ['dragleave', 'dragend'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('drag-active');
    }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove('drag-active');
    const dt = e.dataTransfer;
    if (dt && dt.files && dt.files.length > 0) {
      processUploadedFile(dt.files[0]);
    }
  }, false);
}

// ---------------- UI ACTION HANDLERS (Invoking Python pywebview API) ---------------- //

function triggerVoiceInput() {
  window.setFaceState("LISTENING");
  window.appendLog("SYSTEM", "හඬ හඳුනාගැනීම ආරම්භ විය. සර්, කරුණාකර කතා කරන්න...", "system");
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.on_user_voice_request();
  }
}

function triggerScreenshot() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.on_screenshot_request();
  }
}

function triggerScreenAnalysis() {
  window.setFaceState("THINKING");
  window.appendLog("MANUJA", "පරිගණක තිරය විශ්ලේෂණය කරන්න (Screen Vision)", "user");
  if (window.pywebview && window.pywebview.api && window.pywebview.api.on_screen_analysis_request) {
    window.pywebview.api.on_screen_analysis_request();
  }
}

function triggerLockPc() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.on_lock_pc_request();
  }
}

function triggerLaunchApp(appName) {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.on_launch_app_request(appName);
  }
}

function submitTextInput() {
  const input = document.getElementById('manu-text-input');
  if (!input) return;
  const text = input.value.trim();
  if (!text) return;

  window.appendLog("MANUJA", text, "user");
  input.value = "";

  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.on_user_text_command(text);
  }
}

function handleInputKey(event) {
  if (event.key === 'Enter') {
    submitTextInput();
  }
}

function escapeHtml(string) {
  return String(string).replace(/[&<>"'`=\/]/g, function (s) {
    return {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
      '/': '&#x2F;',
      '`': '&#x60;',
      '=': '&#x3D;'
    }[s];
  });
}

// Floating Desktop Corner Widget Controls
function toggleWidgetMode() {
  document.body.classList.toggle('widget-collapsed');
  const btn = document.getElementById('btn-toggle-compact');
  if (btn) {
    btn.innerText = document.body.classList.contains('widget-collapsed') ? '+' : '−';
  }
  // Recompute Three.js canvas size
  setTimeout(onWindowResize, 50);
}

function closeWidget() {
  if (window.pywebview && window.pywebview.api) {
    if (window.pywebview.api.on_close_widget) {
      window.pywebview.api.on_close_widget();
    }
  }
}

// ---------------- FULLSCREEN HUD CONTROLS ---------------- //

function toggleFullScreen() {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.toggle_fullscreen) {
    window.pywebview.api.toggle_fullscreen();
  } else if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(err => {
      console.warn("Fullscreen request error:", err);
    });
  } else {
    document.exitFullscreen().catch(err => {
      console.warn("Exit fullscreen error:", err);
    });
  }
}

// Global F11 Key Listener
window.addEventListener('keydown', function(e) {
  if (e.key === 'F11') {
    e.preventDefault();
    toggleFullScreen();
  }
});

document.addEventListener('fullscreenchange', () => {
  setTimeout(onWindowResize, 80);
});

// Clock & Date Tick
function updateClock() {
  const now = new Date();
  const timeEl = document.getElementById('hud-clock');
  const dateEl = document.getElementById('hud-date');

  if (timeEl) {
    timeEl.innerText = now.toTimeString().split(' ')[0];
  }
  if (dateEl) {
    const days = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
    const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
    dateEl.innerText = `${days[now.getDay()]} // ${now.getDate()} ${months[now.getMonth()]} ${now.getFullYear()}`;
  }
}

// Auto-init on load
window.addEventListener('DOMContentLoaded', () => {
  initThreeCore();
  setupDropzone();
  setInterval(updateClock, 1000);
  updateClock();
});
