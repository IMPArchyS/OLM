import { Engine } from '@babylonjs/core/Engines/engine';
import { Scene } from '@babylonjs/core/scene';
import { ArcRotateCamera } from '@babylonjs/core/Cameras/arcRotateCamera';
import { HemisphericLight } from '@babylonjs/core/Lights/hemisphericLight';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import { Color3 } from '@babylonjs/core/Maths/math.color';
import { SceneLoader } from '@babylonjs/core/Loading/sceneLoader';
import type { DeviceVisualConfig } from '@/types/api';
import '@babylonjs/loaders/glTF';

const BLINK_DURATION_MS = 180;
const MIN_CAMERA_BETA = 0.2;
const MAX_CAMERA_BETA = Math.PI - 0.2;
const MIN_CAMERA_RADIUS = 1.6;
const MAX_CAMERA_RADIUS = 18;
const ZOOM_DELTA_PERCENTAGE = 0.004;

export function useDeviceScene(canvas: HTMLCanvasElement, visualConfig: DeviceVisualConfig) {
    let engine: Engine | null = null;
    let scene: Scene | null = null;
    let resizeHandler: (() => void) | null = null;
    const blinkTimers = new Map<string, ReturnType<typeof setTimeout>>();

    const toColor3 = (color: [number, number, number]): Color3 => {
        return new Color3(color[0], color[1], color[2]);
    };

    const setMeshEmissiveColor = (meshName: string, color: Color3) => {
        if (!scene) {
            return;
        }

        const mesh = scene.getMeshByName(meshName);
        if (!mesh?.material) {
            return;
        }

        const material = mesh.material as { emissiveColor?: Color3 };
        if (!('emissiveColor' in material)) {
            return;
        }

        material.emissiveColor = color;
    };

    const clearBlinkTimer = (signalKey: string) => {
        const timer = blinkTimers.get(signalKey);
        if (!timer) {
            return;
        }

        clearTimeout(timer);
        blinkTimers.delete(signalKey);
    };

    async function init() {
        if (engine || scene) {
            return;
        }

        engine = new Engine(canvas, true);
        scene = new Scene(engine);

        const camera = new ArcRotateCamera('cam', -Math.PI / 2, Math.PI / 3, 5, Vector3.Zero(), scene);
        camera.lowerBetaLimit = MIN_CAMERA_BETA;
        camera.upperBetaLimit = MAX_CAMERA_BETA;
        camera.lowerRadiusLimit = MIN_CAMERA_RADIUS;
        camera.upperRadiusLimit = MAX_CAMERA_RADIUS;
        camera.wheelDeltaPercentage = ZOOM_DELTA_PERCENTAGE;
        camera.pinchDeltaPercentage = Math.abs(ZOOM_DELTA_PERCENTAGE);
        camera.attachControl(canvas, false);

        new HemisphericLight('light', new Vector3(0, 1, 0), scene);

        await SceneLoader.ImportMeshAsync('', '/models/', visualConfig.model_file, scene);

        engine.runRenderLoop(() => {
            scene?.render();
        });

        resizeHandler = () => {
            engine?.resize();
        };
        window.addEventListener('resize', resizeHandler);
    }

    function triggerAnimation(signalKey: string, active: boolean) {
        const target = visualConfig.animations[signalKey];
        if (!target) {
            return;
        }

        const emissiveColor = toColor3(target.color);
        const offColor = Color3.Black();

        if (target.type === 'emissive' || target.type === 'blink') {
            clearBlinkTimer(signalKey);

            if (!active) {
                setMeshEmissiveColor(target.mesh, offColor);
                return;
            }

            setMeshEmissiveColor(target.mesh, emissiveColor);

            if (target.type === 'blink') {
                const timer = setTimeout(() => {
                    setMeshEmissiveColor(target.mesh, offColor);
                    blinkTimers.delete(signalKey);
                }, BLINK_DURATION_MS);
                blinkTimers.set(signalKey, timer);
            }
        }
    }

    function dispose() {
        blinkTimers.forEach((timer) => clearTimeout(timer));
        blinkTimers.clear();

        if (resizeHandler) {
            window.removeEventListener('resize', resizeHandler);
            resizeHandler = null;
        }

        scene?.dispose();
        engine?.dispose();
        scene = null;
        engine = null;
    }

    return { init, triggerAnimation, dispose };
}
