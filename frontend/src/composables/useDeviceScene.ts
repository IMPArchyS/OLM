import { Engine } from '@babylonjs/core/Engines/engine';
import { Scene } from '@babylonjs/core/scene';
import { ArcRotateCamera } from '@babylonjs/core/Cameras/arcRotateCamera';
import { HemisphericLight } from '@babylonjs/core/Lights/hemisphericLight';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import { Color3, Color4 } from '@babylonjs/core/Maths/math.color';
import { SceneLoader } from '@babylonjs/core/Loading/sceneLoader';
import type { DeviceVisualConfig } from '@/types/api';
import '@babylonjs/loaders/glTF';

const BLINK_DURATION_MS = 180;
const MIN_CAMERA_BETA = 0.2;
const MAX_CAMERA_BETA = Math.PI - 0.2;
const ZOOM_DELTA_PERCENTAGE = 0.004;

export function useDeviceScene(canvas: HTMLCanvasElement, visualConfig: DeviceVisualConfig) {
    let engine: Engine | null = null;
    let scene: Scene | null = null;
    let resizeObserver: ResizeObserver | null = null;
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

    const setMeshPosition = (meshName: string, axis: 'x' | 'y' | 'z', value: number) => {
        if (!scene) {
            return;
        }

        const mesh = scene.getMeshByName(meshName);
        if (!mesh) {
            return;
        }

        mesh.position[axis] = value;
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
        scene.clearColor = new Color4(0, 0, 0, 0);

        const camera = new ArcRotateCamera('cam', -Math.PI / 2, Math.PI / 3, 5, Vector3.Zero(), scene);
        camera.lowerBetaLimit = MIN_CAMERA_BETA;
        camera.upperBetaLimit = MAX_CAMERA_BETA;
        camera.wheelDeltaPercentage = ZOOM_DELTA_PERCENTAGE;
        camera.pinchDeltaPercentage = Math.abs(ZOOM_DELTA_PERCENTAGE);
        camera.attachControl(canvas, false);

        const light = new HemisphericLight('light', new Vector3(0, 1, 0), scene);
        light.intensity = 1.4;

        await SceneLoader.ImportMeshAsync('', '/models/', visualConfig.model_file, scene);

        const { min, max } = scene.getWorldExtends();
        const center = Vector3.Center(min, max);
        const diagonal = max.subtract(min).length();
        camera.setTarget(center);
        camera.radius = diagonal * 1.2;
        camera.lowerRadiusLimit = diagonal * 0.3;
        camera.upperRadiusLimit = diagonal * 5;

        engine.runRenderLoop(() => {
            scene?.render();
        });

        resizeObserver = new ResizeObserver(() => {
            engine?.resize();
        });
        resizeObserver.observe(canvas);
    }

    function triggerAnimation(signalKey: string, value: number) {
        const target = visualConfig.animations[signalKey];
        if (!target) {
            return;
        }

        if (target.type === 'position') {
            setMeshPosition(target.mesh, target.axis ?? 'y', value);
            return;
        }

        const offColor = Color3.Black();
        clearBlinkTimer(signalKey);

        if (value === 0) {
            setMeshEmissiveColor(target.mesh, offColor);
            return;
        }

        const baseColor = toColor3(target.color);

        if (target.type === 'blink') {
            setMeshEmissiveColor(target.mesh, baseColor);
            const timer = setTimeout(() => {
                setMeshEmissiveColor(target.mesh, offColor);
                blinkTimers.delete(signalKey);
            }, BLINK_DURATION_MS);
            blinkTimers.set(signalKey, timer);
        } else {
            const intensity = Math.min(Math.abs(value), 1);
            setMeshEmissiveColor(
                target.mesh,
                new Color3(baseColor.r * intensity, baseColor.g * intensity, baseColor.b * intensity),
            );
        }
    }

    function dispose() {
        blinkTimers.forEach((timer) => clearTimeout(timer));
        blinkTimers.clear();

        if (resizeObserver) {
            resizeObserver.disconnect();
            resizeObserver = null;
        }

        scene?.dispose();
        engine?.dispose();
        scene = null;
        engine = null;
    }

    return { init, triggerAnimation, dispose };
}
