/**
 * 数学计算工具
 * 受 GPL v3.0 保护
 */
const MathUtils = {

    distance(p1, p2) {
        if (!p1 || !p2) return 0;
        const dx = (p2.x || 0) - (p1.x || 0);
        const dy = (p2.y || 0) - (p1.y || 0);
        return Math.sqrt(dx * dx + dy * dy);
    },

    distance3D(p1, p2) {
        if (!p1 || !p2) return 0;
        const dx = (p2.x || 0) - (p1.x || 0);
        const dy = (p2.y || 0) - (p1.y || 0);
        const dz = (p2.z || 0) - (p1.z || 0);
        return Math.sqrt(dx * dx + dy * dy + dz * dz);
    },

    angleBetween(v1, v2) {
        if (!v1 || !v2) return 0;
        const d = this.dot(v1, v2);
        const l1 = this.vectorLength(v1);
        const l2 = this.vectorLength(v2);
        if (l1 === 0 || l2 === 0) return 0;
        return Math.acos(Math.min(1, Math.max(-1, d / (l1 * l2))));
    },

    vectorLength(v) {
        if (!v) return 0;
        return Math.sqrt((v.x || 0) ** 2 + (v.y || 0) ** 2 + (v.z || 0) ** 2);
    },

    normalize(v) {
        const len = this.vectorLength(v);
        if (len === 0) return { x: 0, y: 0, z: 0 };
        return { x: v.x / len, y: v.y / len, z: v.z / len };
    },

    dot(v1, v2) {
        if (!v1 || !v2) return 0;
        return (v1.x || 0) * (v2.x || 0)
            + (v1.y || 0) * (v2.y || 0)
            + (v1.z || 0) * (v2.z || 0);
    },

    cross(v1, v2) {
        if (!v1 || !v2) return { x: 0, y: 0, z: 0 };
        return {
            x: (v1.y || 0) * (v2.z || 0) - (v1.z || 0) * (v2.y || 0),
            y: (v1.z || 0) * (v2.x || 0) - (v1.x || 0) * (v2.z || 0),
            z: (v1.x || 0) * (v2.y || 0) - (v1.y || 0) * (v2.x || 0),
        };
    },

    lerp(a, b, t) {
        return a + (b - a) * t;
    },

    clamp(value, min, max) {
        return Math.max(min, Math.min(max, value));
    },

    degToRad(deg) {
        return deg * Math.PI / 180;
    },

    radToDeg(rad) {
        return rad * 180 / Math.PI;
    },

    roundTo(value, decimals = 2) {
        const f = Math.pow(10, decimals);
        return Math.round(value * f) / f;
    },

    /**
     * AABB 包围盒重叠判断
     * @param {Object} box1 {x, y, z}
     * @param {Object} box2 {x, y, z}
     * @param {Object} pos1 {x, y, z}
     * @param {Object} pos2 {x, y, z}
     */
    aabbOverlap(box1, box2, pos1, pos2) {
        if (!box1 || !box2 || !pos1 || !pos2) return false;
        const dx = Math.abs((pos1.x || 0) - (pos2.x || 0));
        const dy = Math.abs((pos1.y || 0) - (pos2.y || 0));
        const dz = Math.abs((pos1.z || 0) - (pos2.z || 0));
        return dx < ((box1.x || 0) + (box2.x || 0)) / 2
            && dy < ((box1.y || 0) + (box2.y || 0)) / 2
            && dz < ((box1.z || 0) + (box2.z || 0)) / 2;
    },

    /**
     * 解析 "220mm" → 220
     */
    parseMM(str) {
        if (typeof str === 'number') return str;
        if (typeof str === 'string') {
            const n = parseFloat(str.replace('mm', '').replace('kg', '').trim());
            return isNaN(n) ? 0 : n;
        }
        return 0;
    },
};

window.MathUtils = MathUtils;