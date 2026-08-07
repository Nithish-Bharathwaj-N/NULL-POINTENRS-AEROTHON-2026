import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

interface UnityDigitalTwinViewportProps {
  viewMode: 'NORMAL' | 'EXPLODED' | 'THERMAL' | 'XRAY' | 'STRESS';
  onViewModeChange: (mode: string) => void;
  selectedSubsystem: string | null;
  onSelectSubsystem: (subsystem: string | null) => void;
  telemetry: {
    rpm: number;
    t2: number;
    t3: number;
    t4: number;
    p2: number;
    p3: number;
    p4: number;
    fuelFlow: number;
    altitude: number;
    mach: number;
    compressorHealth: number;
    combustorHealth: number;
    turbineHealth: number;
    overallHealth: number;
    thrust: number;
    tsfc: number;
    confidence: number;
  };
  activeScenario: string;
}

// Subsystem grouping definitions
const SUBSYSTEM_GROUPS = {
  FAN: ['Fan_Blade_Assembly', 'Fan_Hub'],
  LPC: Array.from({ length: 6 }, (_, i) => `LPC_Stage_0${i + 1}`),
  HPC: Array.from({ length: 8 }, (_, i) => `HPC_Stage_0${i + 1}`),
  COMBUSTOR: [
    'Combustor_Assembly', 
    'Streamline_Combustor',
    ...Array.from({ length: 16 }, (_, i) => `Fuel_Injector_Nozzle_Assembly_${i.toString().padStart(2, '0')}`)
  ],
  TURBINE: ['High_Pressure_Turbine', 'Low_Pressure_Turbine'],
  EXHAUST: ['Exhaust_Nozzle', 'Streamline_Exhaust'],
  STATIC: [
    ...Array.from({ length: 16 }, (_, i) => `Casing_Stiffener_Ring_${i.toString().padStart(2, '0')}`),
    'Intake_Cone', 'Intake_Mounting_Frame',
    'Streamline_Compressor', 'Streamline_Intake',
    'Central_Shaft', 'Bearing_Housing_00', 'Bearing_Housing_01', 'Bearing_Housing_02'
  ],
  SENSORS: [
    'Bearing_Temperature_Sensor', 'Oil_Pressure_Sensor', 'Pressure_Sensor', 
    'RPM_Sensor', 'Temperature_Sensor', 'Vibration_Sensor',
    'Bearing_Temperature_Sensor_LED', 'Oil_Pressure_Sensor_LED', 'Pressure_Sensor_LED', 
    'RPM_Sensor_LED', 'Temperature_Sensor_LED', 'Vibration_Sensor_LED'
  ],
  ACCESSORIES: [
    'FADEC_ECU_Module', 'Accessory_Gearbox',
    'Fuel_Manifold_Ring_00', 'Fuel_Manifold_Ring_01',
    ...Array.from({ length: 5 }, (_, i) => `Fuel_Line_0${i}`),
    ...Array.from({ length: 3 }, (_, i) => `Oil_Line_0${i}`),
    'Bleed_Air_Valve'
  ]
};

const ROTATING_PARTS = [
  'Fan_Blade_Assembly', 'Fan_Hub',
  ...SUBSYSTEM_GROUPS.LPC,
  ...SUBSYSTEM_GROUPS.HPC,
  'High_Pressure_Turbine', 'Low_Pressure_Turbine',
  'Central_Shaft'
];

const EXPLODED_OFFSETS = {
  FAN: -1.2,
  LPC: -0.6,
  HPC: -0.2,
  COMBUSTOR: 0.3,
  TURBINE: 0.8,
  EXHAUST: 1.4,
  STATIC: 0,
  SENSORS: 0,
  ACCESSORIES: 0
};

const THERMAL_COLORS = {
  FAN: 0x3B82F6,      // blue
  LPC: 0x60A5FA,      // light blue
  HPC: 0x14B8A6,      // cyan-green
  COMBUSTOR: 0xEF4444,// orange-red
  TURBINE: 0xDC2626,  // deep red (HPT) and 0xF97316 (LPT handled later)
  EXHAUST: 0xF59E0B,  // amber
  STATIC: 0x475569,
  SENSORS: 0x475569,
  ACCESSORIES: 0x475569
};

const getHealthColor = (health: number) => {
  if (health > 90) return 0x22C55E; // green
  if (health >= 70) return 0xEAB308; // yellow
  return 0xEF4444; // red
};

export default function UnityDigitalTwinViewport({
  viewMode,
  onViewModeChange,
  selectedSubsystem,
  onSelectSubsystem,
  telemetry,
  activeScenario
}: UnityDigitalTwinViewportProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  
  // ThreeJS core refs
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const requestRef = useRef<number>(0);
  const clockRef = useRef(new THREE.Clock());

  // Model refs
  const modelGroupRef = useRef<THREE.Group | null>(null);
  const meshesRef = useRef<Map<string, THREE.Mesh>>(new Map());
  const originalMaterialsRef = useRef<Map<string, THREE.Material | THREE.Material[]>>(new Map());
  const originalPositionsRef = useRef<Map<string, THREE.Vector3>>(new Map());
  const rotatingMeshesRef = useRef<THREE.Mesh[]>([]);
  
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [modelLoaded, setModelLoaded] = useState(false);

  // Use refs for reactive props to avoid resetting animation loop
  const telemetryRef = useRef(telemetry);
  const viewModeRef = useRef(viewMode);
  const activeScenarioRef = useRef(activeScenario);
  const selectedSubsystemRef = useRef(selectedSubsystem);

  useEffect(() => {
    telemetryRef.current = telemetry;
    viewModeRef.current = viewMode;
    activeScenarioRef.current = activeScenario;
    selectedSubsystemRef.current = selectedSubsystem;
  }, [telemetry, viewMode, activeScenario, selectedSubsystem]);

  // Initialization
  useEffect(() => {
    if (!mountRef.current) return;

    // 1. SceneManager
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#0B132B');
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(45, mountRef.current.clientWidth / mountRef.current.clientHeight, 0.1, 1000);
    camera.position.set(4, 2.5, 6);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    mountRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Realistic metallic reflections via RoomEnvironment
    const pmremGenerator = new THREE.PMREMGenerator(renderer);
    pmremGenerator.compileEquirectangularShader();
    const roomEnv = new RoomEnvironment();
    scene.environment = pmremGenerator.fromScene(roomEnv).texture;

    // Comprehensive Studio 360 Lighting
    const hemiLight = new THREE.HemisphereLight(0xffffff, 0x334155, 1.5);
    scene.add(hemiLight);

    const mainLight = new THREE.DirectionalLight(0xffffff, 2.5);
    mainLight.position.set(10, 12, 10);
    mainLight.castShadow = true;
    scene.add(mainLight);

    const backLight = new THREE.DirectionalLight(0x38bdf8, 1.8);
    backLight.position.set(-10, -5, -10);
    scene.add(backLight);

    const topLight = new THREE.DirectionalLight(0xffffff, 1.2);
    topLight.position.set(0, 15, 0);
    scene.add(topLight);

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 2;
    controls.maxDistance = 20;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.5;
    controlsRef.current = controls;

    // Model Group container to help with centering/scaling
    const modelGroup = new THREE.Group();
    scene.add(modelGroup);
    modelGroupRef.current = modelGroup;

    // 2. EngineModelController (Load Model)
    const loader = new GLTFLoader();
    loader.load(
      '/models/Turbojet.glb',
      (gltf) => {
        const root = gltf.scene;
        
        // Center and scale
        const box = new THREE.Box3().setFromObject(root);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        const scale = 5 / maxDim;
        root.scale.setScalar(scale);
        root.position.sub(center.multiplyScalar(scale));

        modelGroup.add(root);

        // Traverse and process meshes
        root.traverse((child) => {
          if (child instanceof THREE.Mesh) {
            child.castShadow = true;
            child.receiveShadow = true;
            
            meshesRef.current.set(child.name, child);
            originalPositionsRef.current.set(child.name, child.position.clone());
            
            // Clone materials for safe restoration
            if (Array.isArray(child.material)) {
              const clonedMats = child.material.map(m => m.clone());
              originalMaterialsRef.current.set(child.name, clonedMats);
              child.material = clonedMats;
            } else {
              const clonedMat = child.material.clone();
              originalMaterialsRef.current.set(child.name, clonedMat);
              child.material = clonedMat;
            }

            if (ROTATING_PARTS.includes(child.name)) {
              rotatingMeshesRef.current.push(child);
            }
          }
        });

        setModelLoaded(true);
      },
      (xhr) => {
        setLoadingProgress((xhr.loaded / xhr.total) * 100);
      },
      (error) => {
        console.error('Error loading Turbojet.glb', error);
      }
    );

    // Resize handler with ResizeObserver for flexbox/grid containers
    const handleResize = () => {
      if (!mountRef.current || !cameraRef.current || !rendererRef.current) return;
      const width = mountRef.current.clientWidth || mountRef.current.offsetWidth || 800;
      const height = mountRef.current.clientHeight || mountRef.current.offsetHeight || 600;
      cameraRef.current.aspect = width / height;
      cameraRef.current.updateProjectionMatrix();
      rendererRef.current.setSize(width, height);
    };

    const resizeObserver = new ResizeObserver(() => {
      handleResize();
    });
    resizeObserver.observe(mountRef.current);

    // Initial resize trigger after DOM layout settles
    setTimeout(handleResize, 50);
    setTimeout(handleResize, 200);
    
    // Interaction setup
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    
    const onClick = (event: MouseEvent) => {
      if (!mountRef.current || !cameraRef.current) return;
      const rect = mountRef.current.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, cameraRef.current);
      if (modelGroupRef.current) {
        const intersects = raycaster.intersectObject(modelGroupRef.current, true);
        if (intersects.length > 0) {
          controls.autoRotate = false; // Stop rotation on interaction
          const clickedMesh = intersects[0].object as THREE.Mesh;
          
          // Find subsystem
          let foundSubsystem: string | null = null;
          for (const [sys, names] of Object.entries(SUBSYSTEM_GROUPS)) {
            if (names.some(name => clickedMesh.name.match(name) || clickedMesh.name === name)) {
              foundSubsystem = sys;
              break;
            }
          }
          
          onSelectSubsystem(foundSubsystem);
        } else {
          onSelectSubsystem(null);
          controls.autoRotate = true;
        }
      }
    };
    mountRef.current.addEventListener('click', onClick);

    // Cleanup
    return () => {
      resizeObserver.disconnect();
      if (mountRef.current) {
        mountRef.current.removeEventListener('click', onClick);
        if (renderer.domElement.parentNode === mountRef.current) {
          mountRef.current.removeChild(renderer.domElement);
        }
      }
      cancelAnimationFrame(requestRef.current);
      
      scene.traverse((object) => {
        if (object instanceof THREE.Mesh) {
          object.geometry.dispose();
          if (Array.isArray(object.material)) {
            object.material.forEach(m => { m.dispose(); if (m.map) m.map.dispose(); });
          } else {
            object.material.dispose();
            if (object.material.map) object.material.map.dispose();
          }
        }
      });
      renderer.dispose();
      pmremGenerator.dispose();
    };
  }, []);

  // Animation Loop & Controllers
  useEffect(() => {
    if (!modelLoaded) return;

    // Helper to get subsystem for a mesh
    const getSubsystem = (meshName: string) => {
      for (const [sys, names] of Object.entries(SUBSYSTEM_GROUPS)) {
        if (names.some(name => meshName.match(name) || meshName === name)) return sys;
      }
      return 'STATIC';
    };

    const animate = () => {
      try {
        const delta = clockRef.current.getDelta();
        const time = clockRef.current.getElapsedTime();
        const t = telemetryRef.current;
        const mode = viewModeRef.current;
        const scenario = activeScenarioRef.current;
        const selected = selectedSubsystemRef.current;

        controlsRef.current?.update();

        // 3. TelemetryController (Rotation)
        let rotationSpeed = (t.rpm / 60) * Math.PI * 2 * delta;
        
        // Turbine Fouling failure effect
        if (scenario === 'TURBINE_FOULING') {
          rotationSpeed *= 0.7; // Reduce speed by 30%
        }

        // Single-spool rotation (Z-axis)
        rotatingMeshesRef.current.forEach(mesh => {
          if (!mesh) return;
          mesh.rotation.z += rotationSpeed;
          
          // Compressor Surge failure effect (flicker/vibration)
          const origPos = originalPositionsRef.current.get(mesh.name);
          if (origPos) {
            if (scenario === 'COMPRESSOR_SURGE' && (mesh.name.includes('LPC') || mesh.name.includes('HPC'))) {
              if (time % 2.0 < 0.1) {
                mesh.rotation.z -= rotationSpeed * 2; // reverse flicker
              }
              mesh.position.set(
                origPos.x + (Math.random() - 0.5) * 0.01,
                origPos.y + (Math.random() - 0.5) * 0.01,
                mesh.position.z
              );
            } else if (mesh.position.x !== origPos.x || mesh.position.y !== origPos.y) {
              mesh.position.x = origPos.x;
              mesh.position.y = origPos.y;
            }
          }
        });

        // 5. & 6. EffectsController (View Modes & Failure Visuals)
        meshesRef.current.forEach((mesh, name) => {
          if (!mesh || !mesh.material) return;

          const sys = getSubsystem(name);
          const origMatRaw = originalMaterialsRef.current.get(name);
          const origPos = originalPositionsRef.current.get(name);
          const isSelected = selected === sys;

          // Position Updates (Exploded vs Normal)
          if (origPos) {
            const targetZ = mode === 'EXPLODED' ? 
              (origPos.z + (EXPLODED_OFFSETS[sys as keyof typeof EXPLODED_OFFSETS] || 0)) 
              : origPos.z;
            mesh.position.z = THREE.MathUtils.lerp(mesh.position.z, targetZ, 5 * delta);
          }

          // Material Updates — safe in-place property mutations
          const mat = mesh.material as THREE.MeshStandardMaterial;
          const origMat = (Array.isArray(origMatRaw) ? origMatRaw[0] : origMatRaw) as THREE.MeshStandardMaterial;

          if (!mat || !mat.color) return;

          if (mode === 'NORMAL' || mode === 'EXPLODED') {
            if (origMat && origMat.color) {
              mat.color.copy(origMat.color);
              mat.metalness = origMat.metalness ?? 0.8;
              mat.roughness = origMat.roughness ?? 0.3;
              mat.transparent = origMat.transparent ?? false;
              mat.opacity = origMat.opacity ?? 1.0;
            }
            mat.depthWrite = true;

            if (scenario === 'TURBINE_FOULING' && sys === 'TURBINE') {
              mat.color.multiplyScalar(0.6).lerp(new THREE.Color(0x3e2723), 0.5);
            }
            if (isSelected) {
              mat.emissive.setHex(0x38bdf8);
              mat.emissiveIntensity = 0.5;
            } else {
              mat.emissive.setHex(0x000000);
              mat.emissiveIntensity = 0;
            }
          } else if (mode === 'THERMAL') {
            let baseHex = THERMAL_COLORS[sys as keyof typeof THERMAL_COLORS] || 0x888888;
            if (sys === 'TURBINE' && name.includes('Low')) baseHex = 0xF97316;

            mat.color.setHex(baseHex);
            mat.metalness = 0.2;
            mat.roughness = 0.8;
            mat.transparent = false;
            mat.opacity = 1.0;
            mat.depthWrite = true;

            mat.emissive.setHex(baseHex).multiplyScalar(0.3);
            mat.emissiveIntensity = 1.0;

            if (scenario === 'THERMAL_RUNAWAY' && (sys === 'COMBUSTOR' || name.includes('High_Pressure_Turbine'))) {
              const pulse = (Math.sin(time * 10) + 1) / 2;
              const hex = name.includes('Injector') ? 0xff5500 : 0xff0000;
              mat.emissive.setHex(hex).multiplyScalar((name.includes('Injector') ? 2.0 : 1.0) + pulse * 2.0);
            }

            if (isSelected) {
              mat.emissive.setHex(0x38bdf8);
              mat.emissiveIntensity = 0.8;
            }
          } else if (mode === 'STRESS') {
            let healthVal = t.overallHealth;
            if (sys === 'LPC' || sys === 'HPC') healthVal = t.compressorHealth;
            if (sys === 'COMBUSTOR') healthVal = t.combustorHealth;
            if (sys === 'TURBINE') healthVal = t.turbineHealth;

            mat.color.setHex(getHealthColor(healthVal));
            mat.metalness = 0.3;
            mat.roughness = 0.7;
            mat.transparent = false;
            mat.opacity = 1.0;
            mat.depthWrite = true;

            if (isSelected) {
              mat.emissive.setHex(0x38bdf8);
              mat.emissiveIntensity = 0.6;
            } else {
              mat.emissive.setHex(0x000000);
              mat.emissiveIntensity = 0;
            }
          } else if (mode === 'XRAY') {
            if (isSelected) {
              if (origMat && origMat.color) mat.color.copy(origMat.color);
              mat.metalness = 0.8;
              mat.roughness = 0.3;
              mat.transparent = false;
              mat.opacity = 1.0;
              mat.depthWrite = true;
              mat.emissive.setHex(0x38bdf8);
              mat.emissiveIntensity = 0.6;
            } else {
              mat.color.setHex(0x475569);
              mat.metalness = 0.1;
              mat.roughness = 0.9;
              mat.transparent = true;
              mat.opacity = 0.15;
              mat.depthWrite = false;
              mat.emissive.setHex(0x000000);
              mat.emissiveIntensity = 0;
            }
          }
        });

        // Camera Shake for Thermal Runaway
        if (scenario === 'THERMAL_RUNAWAY' && cameraRef.current) {
          cameraRef.current.position.x += (Math.random() - 0.5) * 0.05;
          cameraRef.current.position.y += (Math.random() - 0.5) * 0.05;
        }

        if (rendererRef.current && sceneRef.current && cameraRef.current) {
          rendererRef.current.render(sceneRef.current, cameraRef.current);
        }
      } catch (err) {
        console.error('[DigitalTwin] Error in animation loop:', err);
      }

      requestRef.current = requestAnimationFrame(animate);
    };

    requestRef.current = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(requestRef.current);
    };
  }, [modelLoaded]); // Dependency array ensures we only bind this once after model loads

  return (
    <div className="relative w-full h-full bg-[#0B132B] font-mono overflow-hidden flex flex-col">
      {/* 3D Canvas Container */}
      <div ref={mountRef} className="absolute inset-0 w-full h-full cursor-crosshair z-0" />

      {/* Loading Overlay */}
      {!modelLoaded && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-[#0B132B]/80 backdrop-blur-sm">
          <div className="flex flex-col items-center">
            <div className="w-48 h-2 bg-slate-800 rounded overflow-hidden">
              <div 
                className="h-full bg-cyan-500 transition-all duration-300"
                style={{ width: `${loadingProgress}%` }}
              />
            </div>
            <p className="mt-4 text-cyan-400 text-sm tracking-widest">
              INITIALIZING DIGITAL TWIN [{Math.round(loadingProgress)}%]
            </p>
          </div>
        </div>
      )}

      {/* HUD: Top Left Badge */}
      <div className="absolute top-4 left-4 z-10 flex flex-col gap-2 pointer-events-none">
        <div className="bg-slate-900/60 backdrop-blur border border-slate-700/50 px-4 py-2 rounded">
          <h2 className="text-slate-200 font-bold tracking-wider text-sm">LCA TEJAS MK1A • GE F404-IN20</h2>
          <p className="text-cyan-400 text-xs mt-1">VIEW: {viewMode}</p>
        </div>
        {activeScenario !== 'NORMAL' && (
          <div className="bg-red-900/40 backdrop-blur border border-red-500/50 px-4 py-2 rounded animate-pulse">
            <p className="text-red-400 text-xs font-bold">WARNING: {activeScenario.replace('_', ' ')}</p>
          </div>
        )}
      </div>

      {/* HUD: Top Right Telemetry */}
      <div className="absolute top-4 right-4 z-10 w-64 flex flex-col gap-2 pointer-events-none">
        <div className="bg-slate-900/60 backdrop-blur border border-slate-700/50 p-3 rounded">
          <div className="flex justify-between items-center mb-2">
            <span className="text-slate-400 text-xs">RPM (N2)</span>
            <span className="text-cyan-400 font-bold">{telemetry.rpm.toFixed(0)}</span>
          </div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-slate-400 text-xs">T4 TEMP</span>
            <span className="text-orange-400 font-bold">{telemetry.t4.toFixed(1)} °C</span>
          </div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-slate-400 text-xs">THRUST</span>
            <span className="text-slate-200 font-bold">{telemetry.thrust.toFixed(1)} kN</span>
          </div>
          <div className="flex justify-between items-center border-t border-slate-700/50 pt-2 mt-2">
            <span className="text-slate-400 text-xs">HEALTH</span>
            <span className={`font-bold ${telemetry.overallHealth > 80 ? 'text-green-400' : 'text-red-400'}`}>
              {telemetry.overallHealth.toFixed(1)}%
            </span>
          </div>
        </div>
        
        {/* Controls Hint */}
        <div className="bg-slate-900/40 backdrop-blur border border-slate-800 p-2 rounded text-center">
          <p className="text-slate-500 text-[10px]">Left Click: Rotate • Scroll: Zoom • Click Part: Inspect</p>
        </div>
      </div>

      {/* HUD: Bottom Controls & Ribbon */}
      <div className="absolute bottom-0 left-0 right-0 z-10 flex flex-col p-4 pointer-events-none">
        
        {/* View Mode Toggles */}
        <div className="flex justify-center gap-2 mb-4 pointer-events-auto">
          {['NORMAL', 'EXPLODED', 'THERMAL', 'XRAY', 'STRESS'].map(mode => (
            <button
              key={mode}
              onClick={() => onViewModeChange(mode)}
              className={`px-3 py-1.5 text-xs font-bold rounded border transition-colors ${
                viewMode === mode 
                  ? 'bg-cyan-900/60 border-cyan-500 text-cyan-200' 
                  : 'bg-slate-900/60 border-slate-700 text-slate-400 hover:border-slate-500 hover:text-slate-200'
              }`}
            >
              {mode}
            </button>
          ))}
        </div>

        {/* Subsystem Ribbon */}
        <div className="flex justify-center flex-wrap gap-1 pointer-events-auto max-w-4xl mx-auto bg-slate-900/60 backdrop-blur border border-slate-700/50 p-2 rounded-lg">
          {Object.keys(SUBSYSTEM_GROUPS).map(sys => (
            <button
              key={sys}
              onClick={() => onSelectSubsystem(sys === selectedSubsystem ? null : sys)}
              className={`px-3 py-1 text-[10px] sm:text-xs rounded transition-colors ${
                selectedSubsystem === sys
                  ? 'bg-cyan-600 text-white shadow-[0_0_10px_rgba(8,145,178,0.5)]'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {sys}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
