/**
 * 登录界面
 * 受 GPL v3.0 保护
 */
class LoginUI {
    constructor(containerId = 'loginContainer') {
        this.containerId = containerId;
        this.container = null;
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
            <div style="display:flex;align-items:center;justify-content:center;height:100vh;background:#f0f2f5;">
                <div style="background:#fff;padding:32px;border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,0.1);width:360px;">
                    <h2 style="text-align:center;margin-bottom:24px;">六层架构演示系统</h2>
                    <div style="margin-bottom:12px;">
                        <input id="loginUsername" placeholder="用户名" style="width:100%;padding:8px;border:1px solid #d9d9d9;border-radius:4px;" value="worker">
                    </div>
                    <div style="margin-bottom:16px;">
                        <input id="loginPassword" type="password" placeholder="密码" style="width:100%;padding:8px;border:1px solid #d9d9d9;border-radius:4px;" value="123456">
                    </div>
                    <button id="loginBtn" style="width:100%;padding:10px;background:#1677ff;color:#fff;border:none;border-radius:4px;cursor:pointer;">登录</button>
                    <div id="loginError" style="color:#ff4d4f;font-size:12px;margin-top:8px;"></div>
                    <div style="margin-top:16px;font-size:12px;color:#999;">
                        演示账号：<br>
                        worker / 123456（施工员）<br>
                        owner / 123456（甲方）<br>
                        supervisor / 123456（监理）
                    </div>
                </div>
            </div>
        `;
        document.getElementById('loginBtn').onclick = () => this.doLogin();
        this.container = el;
    }

    async doLogin() {
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        try {
            const res = await APIClient._fetch('/api/auth/login', {
                method: 'POST',
                body: JSON.stringify({ username, password }),
            });
            if (res && res.success) {
                this.saveToken(res.token);
                StorageUtils.setUser(res.user);
                this.onLoginSuccess(res.user);
            } else {
                this.showError(res.message || '登录失败');
            }
        } catch (e) {
            this.showError('网络错误：' + e.message);
        }
    }

    doLogout() {
        this.clearToken();
        StorageUtils.remove('user');
        window.location.reload();
    }

    checkToken() {
        const token = this.getToken();
        return !!token;
    }

    saveToken(token) {
        StorageUtils.setToken(token);
    }

    getToken() {
        return StorageUtils.getToken();
    }

    clearToken() {
        StorageUtils.clearToken();
    }

    refreshToken() {
        return APIClient._fetch('/api/auth/refresh', {
            method: 'POST',
            body: JSON.stringify({ token: this.getToken() }),
        });
    }

    onLoginSuccess(user) {
        console.log('登录成功', user);
        if (this.container) this.container.style.display = 'none';
        if (window.dashboard) window.dashboard.init();
    }

    showError(message) {
        const el = document.getElementById('loginError');
        if (el) el.textContent = message;
    }
}

window.LoginUI = LoginUI;
window.loginUI = new LoginUI();