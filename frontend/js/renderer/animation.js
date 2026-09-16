/**
 * 动画引擎
 * 受 GPL v3.0 保护
 *
 * 提供所有动画效果的底层实现。
 * 含受力点动画 + CBM状态动画 + 装配动画。
 */
class AnimationEngine {
    constructor(scene) {
        this.scene = scene;
        this._activeAnimations = new Map();
    }

    // ==================== 基础插值 ====================

    lerp(a, b, t) {
        return a + (b - a) * t;
    }

    easeInOut(t) {
        return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
    }

    wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // ==================== 基础动画 ====================

    /**
     * 移动物体。
     * @param {THREE.Object3D} object
     * @param {THREE.Vector3} from
     * @param {THREE.Vector3} to
     * @param {number} duration 秒
     * @returns {Promise}
     */
    moveObject(object, from, to, duration = 1.0) {
        if (!object) return Promise.resolve();
        if (duration <= 0) {
            object.position.copy(to);
            return Promise.resolve();
        }

        const key = object.uuid;
        if (this._activeAnimations.has(key)) {
            cancelAnimationFrame(this._activeAnimations.get(key));
        }

        return new Promise(resolve => {
            const startTime = Date.now();
            const animate = () => {
                const t = Math.min(1, (Date.now() - startTime) / (duration * 1000));
                const eased = this.easeInOut(t);
                object.position.x = this.lerp(from.x, to.x, eased);
                object.position.y = this.lerp(from.y, to.y, eased);
                object.position.z = this.lerp(from.z, to.z, eased);
                if (t < 1) {
                    const raf = requestAnimationFrame(animate);
                    this._activeAnimations.set(key, raf);
                } else {
                    this._activeAnimations.delete(key);
                    resolve();
                }
            };
            animate();
        });
    }

    /**
     * 旋转物体。
     */
    rotateObject(object, angle, duration = 1.0) {
        if (!object) return Promise.resolve();
        const from = object.rotation.y;
        const to = from + angle;
        return new Promise(resolve => {
            const startTime = Date.now();
            const animate = () => {
                const t = Math.min(1, (Date.now() - startTime) / (duration * 1000));
                object.rotation.y = this.lerp(from, to, this.easeInOut(t));
                if (t < 1) requestAnimationFrame(animate);
                else resolve();
            };
            animate();
        });
    }

    /**
     * 闪烁物体。
     */
    async flashObject(object, color = 0xff4d4f, duration = 200, times = 3) {
        if (!object || !object.material) return;
        const original = object.material.color ? object.material.color.clone() : null;
        const flash = new THREE.Color(color);
        for (let i = 0; i < times; i++) {
            if (object.material.color) object.material.color.copy(flash);
            await this.wait(duration);
            if (object.material.color && original) object.material.color.copy(original);
            await this.wait(duration);
        }
    }

    // ==================== 挂载 / 卸载 ====================

    attachTo(payload, carrier) {
        if (!payload || !carrier) return;
        // 世界坐标转局部坐标
        const worldPos = new THREE.Vector3();
        payload.getWorldPosition(worldPos);
        carrier.attach(payload);
    }

    detachFrom(payload) {
        if (!payload) return;
        if (payload.parent) {
            payload.parent.remove(payload);
        }
        this.scene.add(payload);
    }

    // ==================== 受力点动画 ====================

    /**
     * 更新受力点动画。
     */
    async updateForcePoint(forcePointObj, newPos, newValue) {
        if (!forcePointObj) return;
        // 位置动画
        if (newPos) {
            await this.moveObject(forcePointObj, forcePointObj.position.clone(), newPos, 0.5);
        }
        // 数值动画
        if (newValue !== undefined) {
            const oldValue = forcePointObj.userData.value || 0;
            const startTime = Date.now();
            const duration = 500;
            await new Promise(resolve => {
                const animate = () => {
                    const t = Math.min(1, (Date.now() - startTime) / duration);
                    forcePointObj.userData.value = this.lerp(oldValue, newValue, t);
                    if (t < 1) requestAnimationFrame(animate);
                    else resolve();
                };
                animate();
            });
        }
    }

    // ==================== CBM 状态动画 ====================

    /**
     * 更新 CBM 状态颜色动画。
     */
    updateCBMStatus(entityObj, newStatus) {
        if (!entityObj || !entityObj.material || !entityObj.material.color) {
            return Promise.resolve();
        }

        const colorMap = {
            'stable': 0x52c41a,
            'warning': 0xfaad14,
            'overload': 0xff4d4f,
            'collision': 0xff7a45,
            'unbuilt': 0xd9d9d9,
        };
        const targetColor = new THREE.Color(colorMap[newStatus] || 0x1677ff);
        const startColor = entityObj.material.color.clone();
        const startTime = Date.now();
        const duration = 500;

        return new Promise(resolve => {
            const animate = () => {
                const t = Math.min(1, (Date.now() - startTime) / duration);
                entityObj.material.color.copy(startColor).lerp(targetColor, t);
                if (t < 1) requestAnimationFrame(animate);
                else resolve();
            };
            animate();
        });
    }

    // ==================== 装配流程动画 ====================

    /**
     * 装配流程动画（5阶段）。
     */
    async animateAssemblyFlow(part, target, forcePoints) {
        if (!part || !target) return;

        // 1. 小人走到零件处
        // 2. 小人拿起零件
        // 3. 小人走到目标位置
        // 4. 小人安装
        // 5. 受力点更新

        // 简化：直接把零件移动到目标
        const from = part.position.clone();
        const to = target.position.clone();
        await this.moveObject(part, from, to, 1.0);

        // 受力点更新
        if (forcePoints && forcePoints.length > 0) {
            for (const fp of forcePoints) {
                await this.updateForcePoint(fp, null, fp.userData.value);
            }
        }
    }

    // ==================== 装配失败动画 ====================

    /**
     * 装配失败动画（红色闪烁3次 + 回到原位）。
     */
    async animateAssemblyFailure(part) {
        if (!part) return;
        const original = part.position.clone();
        await this.flashObject(part, 0xff4d4f, 200, 3);
        // 回到原位（简化：不动）
    }

    // ==================== 人物动画 ====================

    async animateWorkerMove(worker, startPos, endPos) {
        return this.moveObject(worker, startPos, endPos, 2.0);
    }

    async animateWorkerStatus(worker, newStatus) {
        if (!worker || !worker.material) return;
        const statusColors = {
            'idle': 0x52c41a,
            'busy': 0xfaad14,
            'resting': 0x1677ff,
        };
        const targetColor = new THREE.Color(statusColors[newStatus] || 0x52c41a);
        await this._transitionColor(worker, targetColor, 0.5);
    }

    async animateStamina(worker, oldStamina, newStamina) {
        if (!worker || !worker.userData.staminaBar) return;
        const bar = worker.userData.staminaBar;
        const startWidth = bar.geometry.parameters.width * (oldStamina / 100);
        const endWidth = bar.geometry.parameters.width * (newStamina / 100);
        // 简化：直接设置
        bar.scale.x = newStamina / 100;
    }

    async animateMentality(worker, oldMentality, newMentality) {
        // 简化：只打印
        console.log(`心态变化：${oldMentality} → ${newMentality}`);
    }

    _transitionColor(object, targetColor, duration) {
        if (!object.material || !object.material.color) return Promise.resolve();
        const startColor = object.material.color.clone();
        const startTime = Date.now();
        return new Promise(resolve => {
            const animate = () => {
                const t = Math.min(1, (Date.now() - startTime) / (duration * 1000));
                object.material.color.copy(startColor).lerp(targetColor, t);
                if (t < 1) requestAnimationFrame(animate);
                else resolve();
            };
            animate();
        });
    }
}

window.AnimationEngine = AnimationEngine;