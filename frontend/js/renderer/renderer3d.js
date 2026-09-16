/**
 * 3D 渲染引擎
 * 受 GPL v3.0 保护
 *
 * 用 Three.js 渲染所有实体。
 * 含受力点可视化 + CBM 状态可视化 + 小零件点击代理球 + 图层开关。
 */
class Renderer3D {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            throw new Error(`画布不存在：${canvasId}`);
        }

        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x1a1a1a);

        this.camera = new THREE.PerspectiveCamera(
            60,
            this.canvas.clientWidth / this.canvas.clientHeight,
            0.1,
            1000
        );
        this.camera.position.set(8, 6, 12);

        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            antialias: true,
        });
        this.renderer.setSize(this.canvas.clientWidth, this.canvas.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);

        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.1;
        this.controls.target.set(5, 2.5, 0);
        this.controls.update();

        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();

        this.entityMeshes = [];  // [{id, mesh, entity}]
        this.forcePointMeshes = [];  // [{id, mesh, entityId}]
        this.cbmStatusMap = {};
        this.collisions = [];
        this.selectedId = null;
        this.hoveredId = null;
        this.showForcePoints = true;
        this.showCBMStatus = true;

        // 代理球配置
        this.proxyConfig = {
            maxDim: 0.3,
            radius: 0.1,
        };

        // 图层显隐状态 { 类别名: true/false }
        this.categoryVisibility = {};
        // 图例容器
        this.legendEl = null;

        this._setupLights();
        this._setupGround();
        this._setupResize();
        this._setupMouse();
        this._setupLegend();

        this._animate();
    }

    // ==================== 初始化 ====================

    _setupLights() {
        const ambient = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambient);

        const dir = new THREE.DirectionalLight(0xffffff, 0.8);
        dir.position.set(10, 20, 10);
        this.scene.add(dir);

        const dir2 = new THREE.DirectionalLight(0xffffff, 0.3);
        dir2.position.set(-10, -20, -10);
        this.scene.add(dir2);
    }

    _setupGround() {
        const grid = new THREE.GridHelper(20, 20, 0x444444, 0x333333);
        this.scene.add(grid);

        const planeGeo = new THREE.PlaneGeometry(20, 20);
        const planeMat = new THREE.MeshBasicMaterial({
            color: 0x222222,
            side: THREE.DoubleSide,
        });
        const plane = new THREE.Mesh(planeGeo, planeMat);
        plane.rotation.x = -Math.PI / 2;
        plane.position.y = -0.01;
        this.scene.add(plane);
    }

    _setupResize() {
        window.addEventListener('resize', () => {
            const w = this.canvas.clientWidth;
            const h = this.canvas.clientHeight;
            if (w === 0 || h === 0) return;
            this.camera.aspect = w / h;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(w, h);
        });
    }

    _setupMouse() {
        this.canvas.addEventListener('click', (e) => this._handleClick(e));
        this.canvas.addEventListener('mousemove', (e) => this._handleHover(e));
    }

    // ==================== 图层开关（图例） ====================

    _setupLegend() {
        // 动态插入样式
        this._injectLegendStyle();

        // 找到 canvas 的父元素（canvas-wrapper）
        const wrapper = this.canvas.parentElement;
        if (!wrapper) return;

        // 确保 wrapper 是相对定位
        if (getComputedStyle(wrapper).position === 'static') {
            wrapper.style.position = 'relative';
        }

        // 创建图例容器
        const legend = document.createElement('div');
        legend.className = 'scene-legend';
        wrapper.appendChild(legend);
        this.legendEl = legend;
    }

    _injectLegendStyle() {
        if (document.getElementById('scene-legend-style')) return;

        const style = document.createElement('style');
        style.id = 'scene-legend-style';
        style.textContent = `
            .scene-legend {
                position: absolute;
                left: 8px;
                right: 8px;
                bottom: 8px;
                padding: 6px 10px;
                background: rgba(0, 0, 0, 0.65);
                border-radius: 6px;
                color: #ddd;
                font-size: 12px;
                display: flex;
                align-items: center;
                flex-wrap: wrap;
                gap: 6px;
                z-index: 10;
                pointer-events: auto;
                backdrop-filter: blur(4px);
                user-select: none;
            }
            .scene-legend .legend-title {
                color: #999;
                margin-right: 4px;
                font-weight: 600;
            }
            .scene-legend .legend-items {
                display: flex;
                flex-wrap: wrap;
                gap: 4px;
                flex: 1;
            }
            .scene-legend .legend-item {
                padding: 2px 8px;
                border-radius: 3px;
                cursor: pointer;
                border: 1px solid transparent;
                transition: all 0.15s;
                font-size: 11px;
            }
            .scene-legend .legend-item.active {
                background: rgba(82, 196, 26, 0.2);
                border-color: #52c41a;
                color: #7bd662;
            }
            .scene-legend .legend-item.inactive {
                background: rgba(120, 120, 120, 0.15);
                border-color: #555;
                color: #777;
                text-decoration: line-through;
            }
            .scene-legend .legend-item:hover {
                border-color: #1677ff;
            }
            .scene-legend .legend-actions {
                display: flex;
                gap: 4px;
                margin-left: 8px;
            }
            .scene-legend .legend-btn {
                padding: 2px 8px;
                background: #1677ff;
                color: #fff;
                border: none;
                border-radius: 3px;
                cursor: pointer;
                font-size: 11px;
            }
            .scene-legend .legend-btn:hover {
                background: #4096ff;
            }
            .scene-legend .legend-btn.hide-all {
                background: #ff4d4f;
            }
            .scene-legend .legend-btn.hide-all:hover {
                background: #ff7875;
            }
        `;
        document.head.appendChild(style);
    }

    _updateLegend() {
        if (!this.legendEl) return;

        // 收集所有出现过的实体类别
        const categories = new Set();
        for (const em of this.entityMeshes) {
            const t = em.entity && em.entity.entity_type;
            if (t) categories.add(t);
        }

        // 定义显示顺序（重要的排前面）
        const order = [
            '管道', '给水管', '排水管', '消防管',
            '支架', '综合支架', '吊架',
            '阀门', '卡箍', '法兰', '垫片', '螺栓', '手轮', '阀杆', '套管',
            '风管', '桥架',
            '墙体', '楼板', '地面', '柱子', '吊顶',
            '人员', '车辆', '组织', '图纸', '合同',
        ];
        const sorted = [...categories].sort((a, b) => {
            const ia = order.indexOf(a);
            const ib = order.indexOf(b);
            return (ia === -1 ? 999 : ia) - (ib === -1 ? 999 : ib);
        });

        // 生成 HTML
        let html = '<div class="legend-title">图层：</div>';
        html += '<div class="legend-items">';
        for (const cat of sorted) {
            const visible = this.categoryVisibility[cat] !== false;
            html += `<span class="legend-item ${visible ? 'active' : 'inactive'}" data-category="${cat}">${cat}</span>`;
        }
        html += '</div>';
        html += '<div class="legend-actions">';
        html += '<button class="legend-btn" data-action="show-all">全部显示</button>';
        html += '<button class="legend-btn hide-all" data-action="hide-all">全部隐藏</button>';
        html += '</div>';

        this.legendEl.innerHTML = html;

        // 绑定类别点击
        this.legendEl.querySelectorAll('.legend-item').forEach(el => {
            el.onclick = (e) => {
                e.stopPropagation();
                const cat = el.dataset.category;
                const currentlyVisible = this.categoryVisibility[cat] !== false;
                this.setCategoryVisible(cat, !currentlyVisible);
            };
        });

        // 绑定全部显示
        const showAllBtn = this.legendEl.querySelector('[data-action="show-all"]');
        if (showAllBtn) showAllBtn.onclick = (e) => {
            e.stopPropagation();
            this.showAllCategories();
        };

        // 绑定全部隐藏
        const hideAllBtn = this.legendEl.querySelector('[data-action="hide-all"]');
        if (hideAllBtn) hideAllBtn.onclick = (e) => {
            e.stopPropagation();
            this.hideAllCategories();
        };
    }

    /**
     * 设置某类别的显隐
     */
    setCategoryVisible(category, visible) {
        this.categoryVisibility[category] = visible;

        for (const em of this.entityMeshes) {
            if (em.entity && em.entity.entity_type === category) {
                em.mesh.visible = visible;
            }
        }

        // 如果隐藏的是当前选中实体，取消选中高亮
        if (!visible && this.selectedId) {
            const sel = this.entityMeshes.find(em => em.id === this.selectedId);
            if (sel && sel.entity.entity_type === category) {
                // 保持选中状态，但视觉上隐藏了
            }
        }

        this._updateLegend();
    }

    /**
     * 显示所有类别
     */
    showAllCategories() {
        for (const em of this.entityMeshes) {
            if (em.entity && em.entity.entity_type) {
                this.categoryVisibility[em.entity.entity_type] = true;
                em.mesh.visible = true;
            }
        }
        this._updateLegend();
    }

    /**
     * 隐藏所有类别
     */
    hideAllCategories() {
        for (const em of this.entityMeshes) {
            if (em.entity && em.entity.entity_type) {
                this.categoryVisibility[em.entity.entity_type] = false;
                em.mesh.visible = false;
            }
        }
        this._updateLegend();
    }

    /**
     * 获取某类别是否可见
     */
    isCategoryVisible(category) {
        return this.categoryVisibility[category] !== false;
    }

    // ==================== 鼠标交互 ====================

    _handleClick(e) {
        const rect = this.canvas.getBoundingClientRect();
        this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
        this.raycaster.setFromCamera(this.mouse, this.camera);

        const meshes = this.entityMeshes.map(em => em.mesh);
        const hits = this.raycaster.intersectObjects(meshes, true);

        if (hits.length === 0) return;

        const hitIds = [];
        for (const hit of hits) {
            let obj = hit.object;
            while (obj && !obj.userData.entityId) obj = obj.parent;
            if (obj && obj.userData.entityId && !hitIds.includes(obj.userData.entityId)) {
                hitIds.push(obj.userData.entityId);
            }
        }

        if (hitIds.length === 0) return;

        let targetId = hitIds[0];
        if (this.selectedId && hitIds.includes(this.selectedId)) {
            const currentIdx = hitIds.indexOf(this.selectedId);
            const nextIdx = (currentIdx + 1) % hitIds.length;
            targetId = hitIds[nextIdx];
        }

        this.select(targetId);
        if (window.showEntity) window.showEntity(targetId);
    }

    _handleHover(e) {
        const rect = this.canvas.getBoundingClientRect();
        this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
        this.raycaster.setFromCamera(this.mouse, this.camera);

        const meshes = this.entityMeshes.map(em => em.mesh);
        const hits = this.raycaster.intersectObjects(meshes, true);

        let newHovered = null;
        if (hits.length > 0) {
            let obj = hits[0].object;
            while (obj && !obj.userData.entityId) obj = obj.parent;
            if (obj) newHovered = obj.userData.entityId;
        }

        if (newHovered !== this.hoveredId) {
            this.hoveredId = newHovered;
            this._updateHighlight();
            this.canvas.style.cursor = newHovered ? 'pointer' : 'default';
        }
    }

    _updateHighlight() {
        for (const em of this.entityMeshes) {
            const isSelected = em.id === this.selectedId;
            const isHovered = em.id === this.hoveredId;
            if (em.mesh.material) {
                if (isSelected) {
                    em.mesh.material.emissive = new THREE.Color(0x1677ff);
                    em.mesh.material.emissiveIntensity = 0.5;
                } else if (isHovered) {
                    em.mesh.material.emissive = new THREE.Color(0xffffff);
                    em.mesh.material.emissiveIntensity = 0.2;
                } else {
                    em.mesh.material.emissive = new THREE.Color(0x000000);
                    em.mesh.material.emissiveIntensity = 0;
                }
            }
        }
    }

    select(id) {
        this.selectedId = id;
        this._updateHighlight();
    }

    // ==================== 设置数据 ====================

    setEntities(entities) {
        this.entities = entities || [];
        this._rebuildScene();
    }

    setCollisions(collisions) {
        this.collisions = collisions || [];
    }

    setForcePoints(forcePoints) {
        this.forcePoints = forcePoints || [];
        this._rebuildForcePoints();
    }

    setCBMStatus(statusMap) {
        this.cbmStatusMap = statusMap || {};
        this._rebuildScene();
    }

    // ==================== 场景重建 ====================

    _rebuildScene() {
        for (const em of this.entityMeshes) {
            this.scene.remove(em.mesh);
        }
        this.entityMeshes = [];

        for (const e of this.entities) {
            const mesh = this._buildEntity(e);
            if (!mesh) continue;
            mesh.userData.entityId = e.id;
            this.scene.add(mesh);
            this.entityMeshes.push({ id: e.id, mesh, entity: e });
        }

        this._rebuildForcePoints();
        this._addPickProxies();
        this._applyCategoryVisibility();
        this._updateLegend();
    }

    _applyCategoryVisibility() {
        for (const em of this.entityMeshes) {
            const cat = em.entity && em.entity.entity_type;
            if (cat && this.categoryVisibility[cat] === false) {
                em.mesh.visible = false;
            }
        }
    }

    _addPickProxies() {
        const { maxDim, radius } = this.proxyConfig;

        for (const em of this.entityMeshes) {
            try {
                if (em.mesh.userData.__hasProxy) continue;

                const box = new THREE.Box3().setFromObject(em.mesh);
                const size = box.getSize(new THREE.Vector3());
                const curMaxDim = Math.max(size.x, size.y, size.z);

                if (curMaxDim > 0 && curMaxDim < maxDim) {
                    const proxy = new THREE.Mesh(
                        new THREE.SphereGeometry(radius, 8, 8),
                        new THREE.MeshBasicMaterial({
                            transparent: true,
                            opacity: 0,
                            depthWrite: false,
                        })
                    );
                    proxy.userData.entityId = em.id;
                    proxy.userData.isProxy = true;
                    em.mesh.add(proxy);
                    em.mesh.userData.__hasProxy = true;
                }
            } catch (err) {
                console.warn('代理球添加失败:', em.id, err);
            }
        }
    }

    _rebuildForcePoints() {
        for (const fp of this.forcePointMeshes) {
            this.scene.remove(fp.mesh);
        }
        this.forcePointMeshes = [];

        if (!this.showForcePoints) return;

        for (const em of this.entityMeshes) {
            const e = em.entity;
            const l2 = e.layer && e.layer.l2_static_attributes ? e.layer.l2_static_attributes : {};
            const fps = l2['受力点'] || [];
            const pos = this._getPosition(e);

            for (const fp of fps) {
                const fpMesh = this._buildForcePoint(fp, pos);
                if (fpMesh) {
                    this.scene.add(fpMesh);
                    this.forcePointMeshes.push({ id: fp.id, mesh: fpMesh, entityId: e.id });
                }
            }
        }
    }

    // ==================== 实体构建 ====================

    _buildEntity(e) {
        const type = e.entity_type || '';
        try {
            switch (type) {
                case '管道': return this._buildPipe(e);
                case '风管': return this._buildDuct(e);
                case '桥架': return this._buildTray(e);
                case '支架':
                case '综合支架': return this._buildSupport(e);
                case '阀门': return this._buildValve(e);
                case '卡箍': return this._buildClamp(e);
                case '套管': return this._buildSleeve(e);
                case '法兰': return this._buildFlange(e);
                case '螺栓': return this._buildBolt(e);
                case '垫片': return this._buildGasket(e);
                case '人员': return this._buildWorker(e);
                case '墙体': return this._buildWall(e);
                case '楼板': return this._buildSlab(e);
                case '吊顶': return this._buildCeiling(e);
                default: return this._buildDefault(e);
            }
        } catch (err) {
            console.warn(`构建实体失败：${type}`, err);
            return this._buildDefault(e);
        }
    }

    _buildPipe(e) {
        const l2 = e.layer.l2_static_attributes || {};
        const l3 = e.layer.l3_dynamic_state || {};
        const outer = this._parseMM(l2['外径'] || 114.3) / 1000;
        const length = this._parseMM(l3['长度'] || 10000) / 1000;
        const pos = this._getPosition(e);

        const geo = new THREE.CylinderGeometry(outer / 2, outer / 2, length, 16);
        const mat = new THREE.MeshPhongMaterial({ color: this._getColor(e) });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.rotation.z = Math.PI / 2;
        mesh.position.copy(this._toThree(pos.x, pos.y, pos.z));
        return mesh;
    }

    _buildDuct(e) {
        const l2 = e.layer.l2_static_attributes || {};
        const w = this._parseMM(l2['宽度'] || 400) / 1000;
        const h = this._parseMM(l2['高度'] || 200) / 1000;
        const length = 10;
        const pos = this._getPosition(e);

        const geo = new THREE.BoxGeometry(length, h, w);
        const mat = new THREE.MeshPhongMaterial({
            color: this._getColor(e),
            transparent: true,
            opacity: 0.7,
        });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.copy(this._toThree(pos.x, pos.y, pos.z));

        const edges = new THREE.EdgesGeometry(geo);
        const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x666666 }));
        mesh.add(line);
        return mesh;
    }

    _buildTray(e) {
        const l2 = e.layer.l2_static_attributes || {};
        const w = this._parseMM(l2['宽度'] || 300) / 1000;
        const h = this._parseMM(l2['高度'] || 100) / 1000;
        const length = 10;
        const pos = this._getPosition(e);

        const geo = new THREE.BoxGeometry(length, h, w);
        const mat = new THREE.MeshPhongMaterial({
            color: this._getColor(e),
            transparent: true,
            opacity: 0.5,
        });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.copy(this._toThree(pos.x, pos.y, pos.z));

        const edges = new THREE.EdgesGeometry(geo);
        const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x666666 }));
        mesh.add(line);
        return mesh;
    }

    _buildSupport(e) {
        const pos = this._getPosition(e);
        const group = new THREE.Group();

        const poleGeo = new THREE.BoxGeometry(0.05, 0.3, 0.05);
        const poleMat = new THREE.MeshPhongMaterial({ color: this._getColor(e) });
        const pole = new THREE.Mesh(poleGeo, poleMat);
        pole.position.y = -0.15;
        group.add(pole);

        const armGeo = new THREE.BoxGeometry(0.05, 0.05, 0.4);
        const arm = new THREE.Mesh(armGeo, poleMat);
        arm.position.y = 0.15;
        group.add(arm);

        const baseGeo = new THREE.BoxGeometry(0.1, 0.01, 0.1);
        const base = new THREE.Mesh(baseGeo, poleMat);
        base.position.y = -0.3;
        group.add(base);

        group.position.copy(this._toThree(pos.x, pos.y, pos.z));
        return group;
    }

    _buildValve(e) {
        const l2 = e.layer.l2_static_attributes || {};
        const outer = this._parseMM(l2['外径'] || 220) / 1000;
        const length = this._parseMM(l2['长度'] || 280) / 1000;
        const pos = this._getPosition(e);
        const group = new THREE.Group();

        const bodyGeo = new THREE.CylinderGeometry(outer / 2, outer / 2, length, 16);
        const mat = new THREE.MeshPhongMaterial({ color: this._getColor(e) });
        const body = new THREE.Mesh(bodyGeo, mat);
        body.rotation.z = Math.PI / 2;
        group.add(body);

        const cavityGeo = new THREE.CylinderGeometry(outer / 2 * 1.1, outer / 2 * 1.1, length * 0.3, 16);
        const cavity = new THREE.Mesh(cavityGeo, mat);
        cavity.rotation.z = Math.PI / 2;
        group.add(cavity);

        const neckGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.15, 8);
        const neck = new THREE.Mesh(neckGeo, mat);
        neck.position.y = 0.1;
        group.add(neck);

        group.position.copy(this._toThree(pos.x, pos.y, pos.z));
        return group;
    }

    _buildClamp(e) {
        const l2 = e.layer.l2_static_attributes || {};
        const outer = this._parseMM(l2['外径'] || 140) / 1000;
        const width = this._parseMM(l2['宽度'] || 60) / 1000;
        const pos = this._getPosition(e);
        const group = new THREE.Group();
        const mat = new THREE.MeshPhongMaterial({ color: this._getColor(e) });

        const geo = new THREE.CylinderGeometry(outer / 2, outer / 2, width, 16);
        const mesh = new THREE.Mesh(geo, mat);
        mesh.rotation.z = Math.PI / 2;
        group.add(mesh);

        group.position.copy(this._toThree(pos.x, pos.y, pos.z));
        return group;
    }

    _buildSleeve(e) {
        const l2 = e.layer.l2_static_attributes || {};
        const outer = this._parseMM(l2['外径'] || 168.3) / 1000;
        const length = this._parseMM(l2['长度'] || 340) / 1000;
        const pos = this._getPosition(e);

        const geo = new THREE.CylinderGeometry(outer / 2, outer / 2, length, 16, 1, true);
        const mat = new THREE.MeshPhongMaterial({
            color: this._getColor(e),
            side: THREE.DoubleSide,
        });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.rotation.z = Math.PI / 2;
        mesh.position.copy(this._toThree(pos.x, pos.y, pos.z));
        return mesh;
    }

    _buildFlange(e) {
        const l2 = e.layer.l2_static_attributes || {};
        const outer = this._parseMM(l2['外径'] || 220) / 1000;
        const thickness = this._parseMM(l2['厚度'] || 24) / 1000;
        const pos = this._getPosition(e);

        const geo = new THREE.CylinderGeometry(outer / 2, outer / 2, thickness, 24);
        const mat = new THREE.MeshPhongMaterial({ color: this._getColor(e) });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.rotation.z = Math.PI / 2;
        mesh.position.copy(this._toThree(pos.x, pos.y, pos.z));
        return mesh;
    }

    _buildBolt(e) {
        const l2 = e.layer.l2_static_attributes || {};
        const d = this._parseMM(l2['直径'] || 16) / 1000;
        const l = this._parseMM(l2['长度'] || 80) / 1000;
        const pos = this._getPosition(e);

        const geo = new THREE.CylinderGeometry(d / 2, d / 2, l, 8);
        const mat = new THREE.MeshPhongMaterial({ color: this._getColor(e) });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.rotation.z = Math.PI / 2;
        mesh.position.copy(this._toThree(pos.x, pos.y, pos.z));
        return mesh;
    }

    _buildGasket(e) {
        const l2 = e.layer.l2_static_attributes || {};
        const outer = this._parseMM(l2['外径'] || 220) / 1000;
        const inner = this._parseMM(l2['内径'] || 114.3) / 1000;
        const thickness = this._parseMM(l2['厚度'] || 3) / 1000;
        const pos = this._getPosition(e);

        const geo = new THREE.TorusGeometry((outer + inner) / 4, thickness / 2, 8, 24);
        const mat = new THREE.MeshPhongMaterial({ color: this._getColor(e) });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.rotation.y = Math.PI / 2;
        mesh.position.copy(this._toThree(pos.x, pos.y, pos.z));
        return mesh;
    }

    _buildWorker(e) {
        const pos = this._getPosition(e);
        const group = new THREE.Group();
        const mat = new THREE.MeshPhongMaterial({ color: this._getColor(e) });

        const headGeo = new THREE.SphereGeometry(0.12, 12, 12);
        const head = new THREE.Mesh(headGeo, mat);
        head.position.y = 0.6;
        group.add(head);

        const bodyGeo = new THREE.CylinderGeometry(0.1, 0.1, 0.5, 8);
        const body = new THREE.Mesh(bodyGeo, mat);
        body.position.y = 0.25;
        group.add(body);

        const armGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.4, 6);
        const armL = new THREE.Mesh(armGeo, mat);
        armL.position.set(-0.15, 0.35, 0);
        group.add(armL);
        const armR = new THREE.Mesh(armGeo, mat);
        armR.position.set(0.15, 0.35, 0);
        group.add(armR);

        group.position.copy(this._toThree(pos.x, pos.y, pos.z));
        return group;
    }

    _buildWall(e) {
        const l2 = e.layer.l2_static_attributes || {};
        const len = this._parseMM(l2['长度'] || 10000) / 1000;
        const h = this._parseMM(l2['高度'] || 3000) / 1000;
        const t = this._parseMM(l2['厚度'] || 240) / 1000;
        const pos = this._getPosition(e);

        const geo = new THREE.BoxGeometry(len, h, t);
        const mat = new THREE.MeshPhongMaterial({
            color: this._getColor(e),
            transparent: true,
            opacity: 0.3,
        });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.copy(this._toThree(pos.x, pos.y, pos.z));
        return mesh;
    }

    _buildSlab(e) {
        const l2 = e.layer.l2_static_attributes || {};
        const len = this._parseMM(l2['长度'] || 10000) / 1000;
        const w = this._parseMM(l2['宽度'] || 3000) / 1000;
        const t = this._parseMM(l2['厚度'] || 120) / 1000;
        const pos = this._getPosition(e);

        const geo = new THREE.BoxGeometry(len, t, w);
        const mat = new THREE.MeshPhongMaterial({
            color: 0xfaad14,
            transparent: true,
            opacity: 0.2,
        });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.copy(this._toThree(pos.x, pos.y, pos.z));
        return mesh;
    }

    _buildCeiling(e) {
        const l2 = e.layer.l2_static_attributes || {};
        const len = this._parseMM(l2['长度'] || 10000) / 1000;   // 10m
        const w = this._parseMM(l2['宽度'] || 3000) / 1000;     // 3m
        const pos = this._getPosition(e);

        const group = new THREE.Group();

        // ==================== 材质定义 ====================
        // 主龙骨：浅银灰
        const mainKeelMat = new THREE.MeshPhongMaterial({ color: 0xc8c8c8 });
        // 副龙骨：稍深灰
        const subKeelMat = new THREE.MeshPhongMaterial({ color: 0xb0b0b0 });
        // 吊杆：深灰
        const hangerMat = new THREE.MeshPhongMaterial({ color: 0x8c8c8c });
        // 石膏板：米白半透明
        const boardMat = new THREE.MeshPhongMaterial({
            color: 0xf0ead6,
            transparent: true,
            opacity: 0.4,
            side: THREE.DoubleSide,
        });

        // ==================== 1. 主龙骨（C38，3 根，沿 X 方向） ====================
        const mainKeelSpacing = 1.2;      // 主龙骨间距 1.2m
        const mainKeelCount = 3;          // 3 根
        const mainKeelGeo = new THREE.BoxGeometry(len, 0.012, 0.038);

        for (let i = 0; i < mainKeelCount; i++) {
            const z = (i - (mainKeelCount - 1) / 2) * mainKeelSpacing;
            const mainKeel = new THREE.Mesh(mainKeelGeo, mainKeelMat);
            mainKeel.position.set(0, 0, z);
            group.add(mainKeel);
        }

        // ==================== 2. 副龙骨（C50，间距 0.4m，沿 Z 方向） ====================
        const subKeelSpacing = 0.4;       // 副龙骨间距 0.4m
        const subKeelCount = Math.floor(len / subKeelSpacing) + 1;
        const subKeelGeo = new THREE.BoxGeometry(0.05, 0.012, w);

        for (let i = 0; i < subKeelCount; i++) {
            const x = -len / 2 + i * subKeelSpacing;
            const subKeel = new THREE.Mesh(subKeelGeo, subKeelMat);
            subKeel.position.set(x, -0.012, 0);   // 主龙骨下方
            group.add(subKeel);
        }

        // ==================== 3. 吊杆（Φ8，9 根） ====================
        const hangerGeo = new THREE.CylinderGeometry(0.004, 0.004, 0.3, 6);
        const hangerXPositions = [-4, 0, 4];      // 沿主龙骨每根 3 个吊点
        const hangerZPositions = [-1.2, 0, 1.2];  // 主龙骨位置

        for (const x of hangerXPositions) {
            for (const z of hangerZPositions) {
                // 吊杆本体
                const hanger = new THREE.Mesh(hangerGeo, hangerMat);
                hanger.position.set(x, 0.15, z);
                group.add(hanger);

                // 吊杆顶部挂件（在楼板底）
                const hookGeo = new THREE.SphereGeometry(0.015, 8, 8);
                const hook = new THREE.Mesh(hookGeo, hangerMat);
                hook.position.set(x, 0.3, z);
                group.add(hook);

                // 主龙骨吊件（吊杆与主龙骨连接处）
                const clipGeo = new THREE.BoxGeometry(0.05, 0.03, 0.05);
                const clip = new THREE.Mesh(clipGeo, hangerMat);
                clip.position.set(x, 0.015, z);
                group.add(clip);
            }
        }

        // ==================== 4. 石膏板 ====================
        const boardGeo = new THREE.PlaneGeometry(len, w);
        const board = new THREE.Mesh(boardGeo, boardMat);
        board.rotation.x = Math.PI / 2;
        board.position.set(0, -0.024, 0);   // 副龙骨下方
        group.add(board);

        // ==================== 5. 边龙骨（四周） ====================
        const edgeKeelHeight = 0.025;
        const edgeKeelThickness = 0.02;

        // 前后两条（沿 X 方向）
        const edgeFrontBackGeo = new THREE.BoxGeometry(len, edgeKeelHeight, edgeKeelThickness);
        for (const z of [-w / 2, w / 2]) {
            const edge = new THREE.Mesh(edgeFrontBackGeo, mainKeelMat);
            edge.position.set(0, 0, z);
            group.add(edge);
        }

        // 左右两条（沿 Z 方向）
        const edgeLeftRightGeo = new THREE.BoxGeometry(edgeKeelThickness, edgeKeelHeight, w);
        for (const x of [-len / 2, len / 2]) {
            const edge = new THREE.Mesh(edgeLeftRightGeo, mainKeelMat);
            edge.position.set(x, 0, 0);
            group.add(edge);
        }

        group.position.copy(this._toThree(pos.x, pos.y, pos.z));
        return group;
    }

    _buildDefault(e) {
        const pos = this._getPosition(e);
        const geo = new THREE.BoxGeometry(0.2, 0.2, 0.2);
        const mat = new THREE.MeshPhongMaterial({ color: this._getColor(e) });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.copy(this._toThree(pos.x, pos.y, pos.z));
        return mesh;
    }

    // ==================== 受力点可视化 ====================

    _buildForcePoint(fp, parentPos) {
        const group = new THREE.Group();
        const rel = fp['位置'] || { x: 0, y: 0, z: 0 };
        const abs = {
            x: parentPos.x + (rel.x || 0),
            y: parentPos.y + (rel.y || 0),
            z: parentPos.z + (rel.z || 0),
        };

        const pos = this._toThree(abs.x, abs.y, abs.z);

        const sphereGeo = new THREE.SphereGeometry(0.05, 12, 12);
        const color = this._getForceColor(fp['受力状态'] || '稳定');
        const sphereMat = new THREE.MeshBasicMaterial({ color });
        const sphere = new THREE.Mesh(sphereGeo, sphereMat);
        sphere.position.copy(pos);
        group.add(sphere);

        const dir = fp['方向'] || 'Z-';
        const arrow = this._buildForceArrow(pos, dir, color);
        group.add(arrow);

        const label = this._buildForceLabel(pos, fp);
        group.add(label);

        return group;
    }

    _buildForceArrow(pos, direction, color) {
        const dirMap = {
            'Z-': new THREE.Vector3(0, -1, 0),
            'Z+': new THREE.Vector3(0, 1, 0),
            'X+': new THREE.Vector3(1, 0, 0),
            'X-': new THREE.Vector3(-1, 0, 0),
            'Y+': new THREE.Vector3(0, 0, 1),
            'Y-': new THREE.Vector3(0, 0, -1),
        };
        const dir = dirMap[direction] || dirMap['Z-'];
        const arrow = new THREE.ArrowHelper(dir, pos, 0.15, color, 0.08, 0.04);
        return arrow;
    }

    _buildForceLabel(pos, fp) {
        const canvas = document.createElement('canvas');
        canvas.width = 128;
        canvas.height = 32;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = 'rgba(0,0,0,0.6)';
        ctx.fillRect(0, 0, 128, 32);
        ctx.fillStyle = '#fff';
        ctx.font = '12px sans-serif';
        ctx.fillText(fp['承重上限'] || '500kg', 8, 20);

        const texture = new THREE.CanvasTexture(canvas);
        const mat = new THREE.SpriteMaterial({ map: texture });
        const sprite = new THREE.Sprite(mat);
        sprite.position.copy(pos);
        sprite.position.y += 0.15;
        sprite.scale.set(0.3, 0.08, 1);
        return sprite;
    }

    _getForceColor(status) {
        switch (status) {
            case '稳定': return 0x52c41a;
            case '预警': return 0xfaad14;
            case '超载': return 0xff4d4f;
            default: return 0x52c41a;
        }
    }

    // ==================== CBM 状态颜色 ====================

    _getCBMColor(entity) {
        const status = this.cbmStatusMap[entity.id] || 'stable';
        switch (status) {
            case 'stable': return 0x52c41a;
            case 'warning': return 0xfaad14;
            case 'overload': return 0xff4d4f;
            case 'collision': return 0xff7a45;
            case 'unbuilt': return 0xd9d9d9;
            default: return 0x1677ff;
        }
    }

    _getColor(e) {
        if (!this.showCBMStatus) {
            return this._isInstalled(e) ? 0x52c41a : 0xd9d9d9;
        }
        return this._getCBMColor(e);
    }

    _isInstalled(e) {
        const l3 = e.layer && e.layer.l3_dynamic_state ? e.layer.l3_dynamic_state : {};
        return l3['状态'] === '已安装' || l3['状态'] === '已验收';
    }

    // ==================== 坐标映射 ====================

    _toThree(x, y, z) {
        return new THREE.Vector3(x / 1000, z / 1000, y / 1000);
    }

    _parseMM(val) {
        if (typeof val === 'number') return val;
        if (typeof val === 'string') {
            const n = parseFloat(val.replace('mm', '').replace('kg', '').trim());
            return isNaN(n) ? 0 : n;
        }
        return 0;
    }

    _getPosition(e) {
        const l3 = e.layer && e.layer.l3_dynamic_state ? e.layer.l3_dynamic_state : {};
        return l3['绝对坐标'] || { x: 0, y: 0, z: 0 };
    }

    // ==================== 视图控制 ====================

    zoomIn() {
        this.camera.position.multiplyScalar(0.9);
    }
    zoomOut() {
        this.camera.position.multiplyScalar(1.1);
    }
    resetView() {
        this.camera.position.set(8, 6, 12);
        this.controls.target.set(5, 2.5, 0);
        this.controls.update();
    }
    fitView() {
        this.resetView();
    }
    sideView() {
        this.camera.position.set(0, 5, 20);
        this.controls.target.set(5, 2.5, 0);
        this.controls.update();
    }
    topView() {
        this.camera.position.set(5, 20, 0.1);
        this.controls.target.set(5, 0, 0);
        this.controls.update();
    }
    frontView() {
        this.camera.position.set(5, 5, 20);
        this.controls.target.set(5, 2.5, 0);
        this.controls.update();
    }

    toggleForcePoints() {
        this.showForcePoints = !this.showForcePoints;
        this._rebuildForcePoints();
    }

    toggleCBMStatus() {
        this.showCBMStatus = !this.showCBMStatus;
        this._rebuildScene();
    }

    // ==================== 渲染循环 ====================

    _animate() {
        requestAnimationFrame(() => this._animate());
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }
}

window.Renderer3D = Renderer3D;