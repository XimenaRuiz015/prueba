/**
 * EQUIGRUP MVVM - MODEL: AuthModel
 * Responsabilidad: Gestión de llamadas a la API REST de Autenticación, Sesiones y Seguridad.
 */
class AuthModel {
    constructor() {
        this.baseUrl = '/api/auth';
        this.tokenKey = 'equi_auth_token';
        this.userKey = 'equi_user';
    }

    getToken() {
        return localStorage.getItem(this.tokenKey);
    }

    getUser() {
        const u = localStorage.getItem(this.userKey);
        try {
            return u ? JSON.parse(u) : null;
        } catch {
            return null;
        }
    }

    setSession(token, usuario) {
        localStorage.setItem(this.tokenKey, token);
        if (usuario) {
            localStorage.setItem(this.userKey, JSON.stringify(usuario));
        }
    }

    clearSession() {
        localStorage.removeItem(this.tokenKey);
        localStorage.removeItem(this.userKey);
    }

    async login(username, password) {
        const res = await fetch(`${this.baseUrl}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || 'Credenciales incorrectas');
        }
        this.setSession(data.token, data.usuario);
        return data;
    }

    async solicitarCodigo(emailOUsername) {
        const res = await fetch(`${this.baseUrl}/solicitar-codigo`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email_o_username: emailOUsername })
        });
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || 'No se pudo generar el código');
        }
        return data;
    }

    async cambiarPassword(email, codigo, nuevaPassword) {
        const res = await fetch(`${this.baseUrl}/verificar-y-cambiar-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, codigo, nueva_password: nuevaPassword })
        });
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || 'Código inválido o expirado');
        }
        return data;
    }
}

// Exportar al ámbito global para la arquitectura MVVM
window.AuthModel = AuthModel;

