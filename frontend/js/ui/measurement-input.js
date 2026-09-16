/**
 * 实测实量录入
 * 受 GPL v3.0 保护
 */
class MeasurementInput {
    constructor(containerId = 'measurementInput') {
        this.containerId = containerId;
        this.targetId = '';
        this.designValue = 2500;
        this.value = 0;
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
                <h3>实测实量录入</h3>
                <div>测量对象：<input id="measTarget" placeholder="SUP-001" onchange="window.measurementInput.targetId=this.value"></div>
                <div>设计值：<input id="measDesign" type="number" value="2500" onchange="window.measurementInput.designValue=parseFloat(this.value)"></div>
                <div>测量值：<input id="measValue" type="number" onchange="window.measurementInput.inputMeasurement('楼板高度', parseFloat(this.value))"></div>
                <div id="measResult" style="margin-top:8px;"></div>
                <button onclick="window.measurementInput.submitMeasurement()" style="margin-top:8px;">提交</button>
            </div>
        `;
    }

    selectTarget(entityId) { this.targetId = entityId; }
    renderTargetInfo(entity) {}

    inputMeasurement(type, value) {
        this.value = value;
        const deviation = this.calcDeviation();
        const qualified = this.checkThreshold();
        const adjust = this.suggestAdjustment();
        const el = document.getElementById('measResult');
        if (el) {
            el.innerHTML = `
                <div>偏差：${deviation > 0 ? '+' : ''}${deviation}mm</div>
                <div>阈值：±5mm</div>
                <div>状态：${qualified ? '✅ 合格' : '❌ 不合格'}</div>
                <div>调节建议：${adjust.supportAdjust > 0 ? '+' : ''}${adjust.supportAdjust}mm</div>
            `;
        }
    }

    calcDeviation() {
        return Math.round((this.value - this.designValue) * 100) / 100;
    }

    checkThreshold() {
        return Math.abs(this.calcDeviation()) <= 5;
    }

    suggestAdjustment() {
        return { supportAdjust: -this.calcDeviation(), reason: '楼板高度偏差' };
    }

    submitMeasurement() {
        APIClient._fetch('/api/cbm/check', {
            method: 'POST',
            body: JSON.stringify({
                entity_id: this.targetId,
                check_type: 'boundary',
                value: this.value,
            }),
        }).then(() => alert('提交成功')).catch(e => alert('提交失败：' + e.message));
    }

    renderHistory(entityId) {}
    _subscribe_events() {}
    _on_event(eventType, data) {}
}

window.MeasurementInput = MeasurementInput;
window.measurementInput = new MeasurementInput();