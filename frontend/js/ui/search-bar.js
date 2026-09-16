/**
 * 搜索栏
 * 受 GPL v3.0 保护
 */
class SearchBar {
    constructor(containerId = 'searchBar') {
        this.containerId = containerId;
    }

    init() { this.render(); }

    render() {
        let el = document.getElementById(this.containerId);
        if (!el) {
            el = document.createElement('div');
            el.id = this.containerId;
            document.body.appendChild(el);
        }
        el.innerHTML = `
            <div style="padding:12px;">
                <h3>搜索</h3>
                <input id="searchInput" placeholder="搜索实体..." style="width:100%;padding:6px;border:1px solid #d9d9d9;border-radius:4px;"
                    onkeyup="if(event.key==='Enter')window.searchBar.search(this.value)">
                <div id="searchResults" style="margin-top:8px;"></div>
            </div>
        `;
    }

    async search(keyword) {
        if (!keyword) return;
        try {
            const res = await APIClient._fetch(`/api/search/?keyword=${encodeURIComponent(keyword)}`);
            if (res && res.success) this.renderResults(res.data || []);
        } catch (e) {
            console.warn('搜索失败', e);
        }
    }

    searchByType(entityType) {
        return APIClient._fetch(`/api/search/type/${entityType}`);
    }

    searchByPosition(x, y, z, radius) {
        return APIClient._fetch(`/api/search/position?x=${x}&y=${y}&z=${z}&radius=${radius}`);
    }

    searchByForcePoint(min, max) {
        return APIClient._fetch(`/api/search/force_point?min=${min}&max=${max}`);
    }

    searchByContactFace(cfType) {
        return APIClient._fetch(`/api/search/contact_face?cf_type=${cfType}`);
    }

    renderResults(results) {
        const el = document.getElementById('searchResults');
        if (!el) return;
        if (!results || results.length === 0) {
            el.innerHTML = '<div style="color:#999;">无结果</div>';
            return;
        }
        el.innerHTML = results.map(r => `
            <div onclick="window.searchBar.selectResult('${r.id}')"
                style="padding:6px;margin-bottom:4px;background:#fafafa;border-radius:4px;cursor:pointer;font-size:12px;">
                <strong>${r.id}</strong> · ${r.entity_type || ''}
            </div>
        `).join('');
    }

    onResultClick(entityId) { this.selectResult(entityId); }

    selectResult(entityId) {
        if (window.showEntity) window.showEntity(entityId);
        if (window.state && window.state.renderer) window.state.renderer.select(entityId);
    }
}

window.SearchBar = SearchBar;
window.searchBar = new SearchBar();