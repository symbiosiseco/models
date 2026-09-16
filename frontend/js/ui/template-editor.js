/**
 * 模板编辑器
 * 受 GPL v3.0 保护
 */
class TemplateEditor {
    constructor(containerId = 'templateEditor') {
        this.containerId = containerId;
        this.template = {
            template_id: '',
            category: '物品',
            entity_type: '阀门',
            name: '',
            manufacturer: '',
            params: {},
            anchors: [],
            force_points: [],
            contact_faces: [],
            cbm: {},
            '硬性要求': { '必须包含': [], '可选包含': [], 'AI补全规则': [], '验证规则': [] },
        };
    }

    init() {
        this.render();
    }

    render() {
        let el = document.getElementById(this.containerId);
        if (!el) {
            el = document.createElement('div');
            el.id = this.containerId;
            document.body.appendChild(el);
        }
        el.innerHTML = `
            <div style="padding:12px;">
                <h3>模板编辑器</h3>
                ${this.renderBasicFields()}
                ${this.renderParamsEditor()}
                ${this.renderAnchorsEditor()}
                ${this.renderForcePointsEditor()}
                ${this.renderContactFacesEditor()}
                ${this.renderCBMEditor()}
                ${this.renderRequirementsEditor()}
                <div style="margin-top:12px;">
                    <button onclick="window.templateEditor.validate()">校验</button>
                    <button onclick="window.templateEditor.save()">保存</button>
                </div>
            </div>
        `;
    }

    renderBasicFields() {
        return `
            <div style="margin-bottom:12px;">
                <h4>基础信息</h4>
                <div>模板ID：<input value="${this.template.template_id}" onchange="window.templateEditor.template.template_id=this.value"></div>
                <div>类别：<input value="${this.template.category}" onchange="window.templateEditor.template.category=this.value"></div>
                <div>实体类型：<input value="${this.template.entity_type}" onchange="window.templateEditor.template.entity_type=this.value"></div>
                <div>名称：<input value="${this.template.name}" onchange="window.templateEditor.template.name=this.value"></div>
                <div>厂家：<input value="${this.template.manufacturer}" onchange="window.templateEditor.template.manufacturer=this.value"></div>
            </div>
        `;
    }

    renderParamsEditor() {
        return `<div style="margin-bottom:12px;"><h4>参数</h4><textarea style="width:100%;height:60px;" onchange="window.templateEditor.template.params=JSON.parse(this.value||'{}')">${JSON.stringify(this.template.params, null, 2)}</textarea></div>`;
    }

    renderAnchorsEditor() {
        return `<div style="margin-bottom:12px;"><h4>锚点</h4><textarea style="width:100%;height:60px;" onchange="window.templateEditor.template.anchors=JSON.parse(this.value||'[]')">${JSON.stringify(this.template.anchors, null, 2)}</textarea></div>`;
    }

    renderForcePointsEditor() {
        return `<div style="margin-bottom:12px;"><h4>受力点</h4><textarea style="width:100%;height:60px;" onchange="window.templateEditor.template.force_points=JSON.parse(this.value||'[]')">${JSON.stringify(this.template.force_points, null, 2)}</textarea></div>`;
    }

    renderContactFacesEditor() {
        return `<div style="margin-bottom:12px;"><h4>接触面</h4><textarea style="width:100%;height:60px;" onchange="window.templateEditor.template.contact_faces=JSON.parse(this.value||'[]')">${JSON.stringify(this.template.contact_faces, null, 2)}</textarea></div>`;
    }

    renderCBMEditor() {
        return `<div style="margin-bottom:12px;"><h4>CBM</h4><textarea style="width:100%;height:80px;" onchange="window.templateEditor.template.cbm=JSON.parse(this.value||'{}')">${JSON.stringify(this.template.cbm, null, 2)}</textarea></div>`;
    }

    renderRequirementsEditor() {
        return `<div style="margin-bottom:12px;"><h4>硬性要求</h4><textarea style="width:100%;height:60px;" onchange="window.templateEditor.template['硬性要求']=JSON.parse(this.value||'{}')">${JSON.stringify(this.template['硬性要求'], null, 2)}</textarea></div>`;
    }

    loadTemplate(templateId) {
        return APIClient.getTemplate(templateId).then(res => {
            if (res && res.success) {
                this.template = res.data;
                this.render();
            }
        });
    }

    validate() {
        const result = ValidatorUtils.validateEntity({
            entity_type: this.template.entity_type,
            layer: {
                r_layer: { '类别': this.template.entity_type },
                l1_identity: { '唯一ID': this.template.template_id },
                l2_static_attributes: {
                    ...this.template.params,
                    '受力点': this.template.force_points,
                    '接触面': this.template.contact_faces,
                },
                l3_dynamic_state: {},
                l4_event_chain: [],
                cbm_abilities: this.template.cbm,
            },
        });
        if (result.valid) {
            alert('校验通过');
        } else {
            alert('校验失败：' + result.errors.join(', '));
        }
        return result;
    }

    save() {
        const validation = this.validate();
        if (!validation.valid) return;
        APIClient._fetch('/api/templates/', {
            method: 'POST',
            body: JSON.stringify(this.template),
        }).then(() => alert('保存成功')).catch(e => alert('保存失败：' + e.message));
    }
}

window.TemplateEditor = TemplateEditor;
window.templateEditor = new TemplateEditor();