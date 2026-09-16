/**
 * 游戏式手动安装模拟器
 * 受 GPL v3.0 保护
 *
 * 第2批：点地板 → 选支架 → 安装
 */

(function () {
    'use strict';

    // ==================== 全局状态 ====================
    var state = {
        mode: 'idle',         // idle / pick_floor / pick_entity / confirm
        pickedPosition: null, // {x, y, z}
        pickedEntityId: null,
        entitiesCache: [],
    };

    // ==================== UI ====================

    function createButton() {
        var btn = document.createElement('button');
        btn.id = 'game-installer-btn';
        btn.innerHTML = '🔨 安装模式';
        btn.style.cssText = [
            'position: fixed', 'top: 60px', 'right: 20px', 'z-index: 9999',
            'padding: 8px 16px', 'background: #ff7a45', 'color: #fff',
            'border: none', 'border-radius: 6px', 'font-size: 14px',
            'font-weight: 600', 'cursor: pointer',
            'box-shadow: 0 2px 8px rgba(0,0,0,0.3)',
        ].join(';');
        btn.onclick = togglePanel;
        document.body.appendChild(btn);
    }

    function createPanel() {
        var panel = document.createElement('div');
        panel.id = 'game-installer-panel';
        panel.style.cssText = [
            'position: fixed', 'top: 100px', 'right: 20px', 'width: 300px',
            'z-index: 9998', 'background: #001529', 'color: #fff',
            'border-radius: 8px', 'padding: 16px',
            'box-shadow: 0 4px 16px rgba(0,0,0,0.5)', 'display: none',
            'font-size: 13px',
        ].join(';');
        document.body.appendChild(panel);
        renderPanel();
    }

    function renderPanel() {
        var panel = document.getElementById('game-installer-panel');
        if (!panel) return;
        var html = '';

        html += '<div style="font-weight:600;margin-bottom:12px;color:#ff7a45;">🔨 安装模式</div>';

        if (state.mode === 'idle') {
            html += '<div style="color:#aaa;font-size:12px;line-height:1.8;">';
            html += '  <div>👆 点击【开始安装】</div>';
            html += '  <div style="color:#666;font-size:11px;margin-top:8px;">';
            html += '    流程：点地板 → 选支架 → 点安装';
            html += '  </div>';
            html += '</div>';
            html += '<div style="margin-top:12px;text-align:right;">';
            html += '  <button id="gi-start" style="padding:6px 16px;background:#52c41a;color:#fff;border:none;border-radius:4px;cursor:pointer;font-weight:600;">开始安装</button>';
            html += '  <button id="gi-close" style="padding:6px 12px;background:#444;color:#fff;border:none;border-radius:4px;cursor:pointer;margin-left:6px;">关闭</button>';
            html += '</div>';
        } else if (state.mode === 'pick_floor') {
            html += '<div style="color:#faad14;font-size:13px;line-height:1.8;">';
            html += '  <div>📍 步骤 1/3：请点击 3D 场景里的地板</div>';
            html += '  <div style="color:#666;font-size:11px;margin-top:8px;">';
            html += '    （在 3D 画布上直接点击你要安装的位置）';
            html += '  </div>';
            html += '</div>';
            html += '<div style="margin-top:12px;text-align:right;">';
            html += '  <button id="gi-cancel" style="padding:4px 12px;background:#444;color:#fff;border:none;border-radius:4px;cursor:pointer;">取消</button>';
            html += '</div>';
        } else if (state.mode === 'pick_entity') {
            html += '<div style="color:#52c41a;font-size:13px;">';
            html += '  <div>✅ 位置已设定：' + formatPos(state.pickedPosition) + '</div>';
            html += '</div>';
            html += '<div style="color:#faad14;font-size:13px;margin-top:12px;">';
            html += '  <div>📦 步骤 2/3：选择要安装的支架</div>';
            html += '</div>';
            html += '<select id="gi-entity" style="width:100%;margin-top:8px;padding:6px;background:#1a1a1a;color:#fff;border:1px solid #444;border-radius:4px;">';
            html += '<option value="">-- 请选择 --</option>';
            for (var i = 0; i < state.entitiesCache.length; i++) {
                var e = state.entitiesCache[i];
                html += '<option value="' + e.id + '">' + e.id + ' (' + e.entity_type + ')</option>';
            }
            html += '</select>';
            html += '<div style="margin-top:12px;text-align:right;">';
            html += '  <button id="gi-next" style="padding:4px 12px;background:#52c41a;color:#fff;border:none;border-radius:4px;cursor:pointer;">下一步</button>';
            html += '  <button id="gi-cancel" style="padding:4px 12px;background:#444;color:#fff;border:none;border-radius:4px;cursor:pointer;margin-left:6px;">取消</button>';
            html += '</div>';
        } else if (state.mode === 'confirm') {
            html += '<div style="color:#52c41a;font-size:13px;">';
            html += '  <div>✅ 位置：' + formatPos(state.pickedPosition) + '</div>';
            html += '  <div>✅ 支架：' + state.pickedEntityId + '</div>';
            html += '</div>';
            html += '<div style="color:#faad14;font-size:13px;margin-top:12px;">';
            html += '  <div>🔨 步骤 3/3：点击【安装】执行</div>';
            html += '</div>';
            html += '<div style="margin-top:12px;text-align:right;">';
            html += '  <button id="gi-install" style="padding:6px 16px;background:#ff7a45;color:#fff;border:none;border-radius:4px;cursor:pointer;font-weight:600;">安装</button>';
            html += '  <button id="gi-cancel" style="padding:4px 12px;background:#444;color:#fff;border:none;border-radius:4px;cursor:pointer;margin-left:6px;">取消</button>';
            html += '</div>';
        }

        panel.innerHTML = html;
        bindEvents();
    }

    function formatPos(p) {
        if (!p) return '';
        return '(' + Math.round(p.x) + ', ' + Math.round(p.y) + ', ' + Math.round(p.z) + ')';
    }

    function bindEvents() {
        var el;

        el = document.getElementById('gi-start');
        if (el) el.onclick = startInstall;

        el = document.getElementById('gi-close');
        if (el) el.onclick = function () {
            document.getElementById('game-installer-panel').style.display = 'none';
        };

        el = document.getElementById('gi-cancel');
        if (el) el.onclick = resetInstall;

        el = document.getElementById('gi-next');
        if (el) el.onclick = function () {
            var sel = document.getElementById('gi-entity');
            if (!sel || !sel.value) {
                alert('请先选择一个支架');
                return;
            }
            state.pickedEntityId = sel.value;
            state.mode = 'confirm';
            renderPanel();
        };

        el = document.getElementById('gi-install');
        if (el) el.onclick = doInstall;
    }

    // ==================== 核心流程 ====================

    function startInstall() {
        state.mode = 'pick_floor';
        state.pickedPosition = null;
        state.pickedEntityId = null;
        loadEntities();
        renderPanel();
    }

    function resetInstall() {
        state.mode = 'idle';
        state.pickedPosition = null;
        state.pickedEntityId = null;
        removeMarker();
        renderPanel();
    }

    function loadEntities() {
        fetch('/api/entities/')
            .then(function (r) { return r.json(); })
            .then(function (d) {
                var list = d.data || d.entities || d;
                // 只保留"支架"和"综合支架"
                state.entitiesCache = list.filter(function (e) {
                    return e.entity_type === '支架' || e.entity_type === '综合支架';
                });
            })
            .catch(function (err) {
                console.warn('加载实体失败', err);
            });
    }

    // ==================== 3D 交互 ====================

    var _marker = null;

    function removeMarker() {
        if (_marker && _marker.parent) {
            _marker.parent.remove(_marker);
            _marker = null;
        }
    }

    function placeMarker(pos) {
        removeMarker();
        var renderer = window.__renderer;
        if (!renderer) return;

        // 在世界坐标处放一个绿色标记
        var geo = new THREE.SphereGeometry(0.15, 16, 16);
        var mat = new THREE.MeshBasicMaterial({
            color: 0x52c41a,
            transparent: true,
            opacity: 0.7,
        });
        var sphere = new THREE.Mesh(geo, mat);
        sphere.position.set(pos.x / 1000, pos.z / 1000, pos.y / 1000);
        renderer.scene.add(sphere);
        _marker = sphere;
    }

    // 监听 canvas 点击
    function attachCanvasListener() {
        var canvas = document.querySelector('canvas');
        if (!canvas || canvas.dataset.giBound) return;
        canvas.dataset.giBound = '1';

        canvas.addEventListener('click', function (e) {
            if (state.mode !== 'pick_floor') return;
            e.stopPropagation();

            var renderer = window.__renderer;
            if (!renderer) return;

            var rect = canvas.getBoundingClientRect();
            var mouse = new THREE.Vector2();
            mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
            mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

            var raycaster = new THREE.Raycaster();
            raycaster.setFromCamera(mouse, renderer.camera);

            // 检测跟地面网格的交点
            var plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
            var point = new THREE.Vector3();
            var hit = raycaster.ray.intersectPlane(plane, point);

            if (hit) {
                // three → world：反转坐标映射
                var worldX = point.x * 1000;
                var worldY = point.z * 1000;
                var worldZ = point.y * 1000;
                state.pickedPosition = { x: worldX, y: worldY, z: worldZ };
                placeMarker(state.pickedPosition);
                state.mode = 'pick_entity';
                renderPanel();
            }
        }, true); // 用捕获阶段，抢在 renderer3d 的 _handleClick 之前
    }

    // ==================== 执行安装 ====================

    function doInstall() {
        if (!state.pickedEntityId || !state.pickedPosition) return;

        fetch('/api/game/install', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                entity_id: state.pickedEntityId,
                position: state.pickedPosition,
            }),
        })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (d.success) {
                    alert('✅ 安装成功：' + state.pickedEntityId);
                    resetInstall();
                    // 刷新 3D 场景
                    if (window.refreshAll) window.refreshAll();
                } else {
                    alert('❌ 安装失败：' + (d.message || '未知错误'));
                }
            })
            .catch(function (err) {
                alert('❌ 请求失败：' + err);
            });
    }

    // ==================== 启动 ====================

    function togglePanel() {
        var panel = document.getElementById('game-installer-panel');
        if (!panel) return;
        if (panel.style.display === 'none' || !panel.style.display) {
            panel.style.display = 'block';
            attachCanvasListener();
        } else {
            panel.style.display = 'none';
            removeMarker();
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            createButton();
            createPanel();
        });
    } else {
        createButton();
        createPanel();
    }
})();