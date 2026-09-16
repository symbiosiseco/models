/**
 * L4 套娃履历查看器
 * 受 GPL v3.0 保护
 *
 * 使用方式：
 *   window.L4Viewer.show(entityId)
 *
 * 注意：如果容器不存在，静默跳过（不报错）
 */
(function () {
    'use strict';

    function findContainer() {
        var ids = ['l4-viewer-container', 'l4-panel', 'l4Viewer', 'l4-viewer'];
        for (var i = 0; i < ids.length; i++) {
            var el = document.getElementById(ids[i]);
            if (el) return el;
        }
        return null;
    }

    function render(data) {
        var container = findContainer();
        if (!container) return;

        var events = data.events || [];
        var entityType = data.entity_type || '';
        var html = '';

        html += '<div style="padding:8px 12px;border-bottom:1px solid #333;color:#ddd;font-size:13px;">';
        html += '<span style="font-weight:600;">📜 L4 履历</span>';
        html += '<span style="color:#999;font-size:12px;margin-left:8px;">' + entityType + '</span>';
        html += '</div>';

        if (events.length === 0) {
            html += '<div style="padding:12px;color:#666;font-size:12px;text-align:center;">暂无履历</div>';
        } else {
            html += '<div style="padding:8px 12px;max-height:300px;overflow-y:auto;">';
            for (var i = events.length - 1; i >= 0; i--) {
                var ev = events[i];
                html += '<div style="padding:6px 0;border-bottom:1px solid #2a2a2a;">';
                html += '<div style="color:#666;font-size:11px;">' + (ev.time || '') + '</div>';
                html += '<div style="color:#ddd;font-size:12px;">' + (ev.event || '') + '</div>';
                if (ev.detail) {
                    html += '<div style="color:#999;font-size:11px;">' + ev.detail + '</div>';
                }
                html += '</div>';
            }
            html += '</div>';
        }

        container.innerHTML = html;
    }

    function show(entityId) {
        if (!entityId) return;

        // 如果容器不存在，直接跳过（不报错）
        var container = findContainer();
        if (!container) {
            console.log('[L4Viewer] 无容器，跳过 L4 渲染');
            return;
        }

        fetch('/api/l4/' + entityId)
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data && data.success) {
                    render(data);
                }
            })
            .catch(function (err) {
                console.warn('[L4Viewer] 加载失败:', err);
            });
    }

    // 暴露为全局单例
    window.L4Viewer = {
        show: show,
        render: render
    };
})();