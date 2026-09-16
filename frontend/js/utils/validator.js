/**
 * 前端数据校验工具
 * 受 GPL v3.0 保护
 */
const ValidatorUtils = {

    // ==================== 基础校验 ====================

    isEmail(str) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(str || '');
    },

    isPhone(str) {
        return /^1[3-9]\d{9}$/.test(str || '');
    },

    isNumber(val) {
        return typeof val === 'number' && !isNaN(val);
    },

    isPositiveNumber(val) {
        return this.isNumber(val) && val > 0;
    },

    isNonEmptyString(str) {
        return typeof str === 'string' && str.trim().length > 0;
    },

    isValidJSON(str) {
        if (typeof str !== 'string') return false;
        try {
            JSON.parse(str);
            return true;
        } catch (e) {
            return false;
        }
    },

    // ==================== 六层实体校验 ====================

    validateLayers(entity) {
        const errors = [];
        const layer = entity.layer || entity;
        if (!layer.r_layer) errors.push('缺少R层');
        if (!layer.l1_identity) errors.push('缺少L1层');
        if (!layer.l2_static_attributes) errors.push('缺少L2层');
        if (!layer.l3_dynamic_state) errors.push('缺少L3层');
        if (!layer.l4_event_chain) errors.push('缺少L4层');
        if (!layer.cbm_abilities) errors.push('缺少CBM层');
        return { valid: errors.length === 0, errors };
    },

    validateEntity(entity) {
        const layerResult = this.validateLayers(entity);
        const errors = [...layerResult.errors];
        const warnings = [];
        return { valid: errors.length === 0, errors, warnings };
    },

    validateForcePoints(entity) {
        const errors = [];
        const warnings = [];
        const type = entity.entity_type || '';
        const nonPhysical = ['任务', '报表', '模板', '项目', '合同', '图纸',
            '验收', '变更', '签证', '通知记录', '签字记录', '实测实量',
            '实测记录', '厂家', '产品', '组织', '人员'];
        if (nonPhysical.includes(type)) {
            return { valid: true, errors, warnings };
        }
        const l2 = entity.layer ? entity.layer.l2_static_attributes : {};
        const fps = (l2 && l2['受力点']) || [];
        if (fps.length === 0) {
            warnings.push(`物理实体 ${type} 缺少受力点`);
        }
        return { valid: errors.length === 0, errors, warnings };
    },

    validateContactFaces(entity) {
        const errors = [];
        const warnings = [];
        const type = entity.entity_type || '';
        const nonPhysical = ['任务', '报表', '模板', '项目', '合同', '图纸',
            '验收', '变更', '签证', '通知记录', '签字记录', '实测实量',
            '实测记录', '厂家', '产品', '组织', '人员'];
        if (nonPhysical.includes(type)) {
            return { valid: true, errors, warnings };
        }
        const l2 = entity.layer ? entity.layer.l2_static_attributes : {};
        const cfs = (l2 && l2['接触面']) || [];
        if (cfs.length === 0) {
            warnings.push(`物理实体 ${type} 缺少接触面`);
        }
        for (const cf of cfs) {
            if (cf['允许偏差'] && cf['允许偏差'] !== '0mm') {
                errors.push(`接触面 ${cf.id} 允许偏差必须为0mm`);
            }
        }
        return { valid: errors.length === 0, errors, warnings };
    },

    validateCBM(entity) {
        const errors = [];
        const warnings = [];
        const type = entity.entity_type || '';
        const nonPhysical = ['任务', '报表', '模板', '项目', '合同', '图纸',
            '验收', '变更', '签证', '通知记录', '签字记录', '实测实量',
            '实测记录', '厂家', '产品', '组织', '人员'];
        if (nonPhysical.includes(type)) {
            return { valid: true, errors, warnings };
        }
        const cbm = entity.layer ? entity.layer.cbm_abilities : {};
        const required = ['物理规则', '受力规则', '装配规则', '规范约束'];
        const missing = required.filter(r => !cbm || !cbm[r]);
        if (missing.length > 0) {
            errors.push(`缺少CBM规则：${missing.join(', ')}`);
        }
        return { valid: errors.length === 0, errors, warnings };
    },

    validatePipeSegments(pipe) {
        const errors = [];
        const l3 = pipe.layer ? pipe.layer.l3_dynamic_state : {};
        const length = (l3 && l3['长度']) || 0;
        if (length > 6000) {
            const l2 = pipe.layer ? pipe.layer.l2_static_attributes : {};
            const segments = l2 && l2['分段规则'];
            if (!segments) {
                errors.push('超过6米的管道必须分段（10米=6+4+卡箍）');
            } else if (length === 10000) {
                const segs = segments['分段'] || [];
                if (segs.length !== 2) {
                    errors.push('10米管道必须分为6+4');
                }
            }
        }
        return { valid: errors.length === 0, errors };
    },

    validateGasket(gasket) {
        const errors = [];
        const l2 = gasket.layer ? gasket.layer.l2_static_attributes : {};
        const constraints = (l2 && l2['约束']) || [];
        if (constraints.length < 5) {
            errors.push(`垫片必须有5个约束（位置/范围/孔径/方向/数量），当前${constraints.length}个`);
        }
        return { valid: errors.length === 0, errors };
    },

    validatePosition(pos) {
        const errors = [];
        if (!pos) {
            errors.push('位置为空');
        } else {
            const { x, y, z } = pos;
            if (x < -100000 || x > 100000) errors.push('X坐标越界');
            if (y < -100000 || y > 100000) errors.push('Y坐标越界');
            if (z < -1000 || z > 10000) errors.push('Z坐标越界');
        }
        return { valid: errors.length === 0, errors };
    },

    validateParams(params) {
        const errors = [];
        if (!params || typeof params !== 'object') {
            errors.push('参数必须为对象');
            return { valid: false, errors };
        }
        if (!params['产品名称'] && !params['产品型号']) {
            errors.push('缺少产品名称或产品型号');
        }
        return { valid: errors.length === 0, errors };
    },
};

window.ValidatorUtils = ValidatorUtils;