/**
 * EQUIGRUP MVVM - VIEWMODEL: AuthViewModel
 * Responsabilidad: Manejo del estado reactivo de autenticación, control de vistas de login/recuperación y validaciones.
 */
class AuthViewModel {
    constructor(authModel) {
        this.model = authModel || new AuthModel();
        this.isAuthenticated = false;
        this.currentUser = null;
        this.activeAuthView = 'login'; // 'login' | 'recuperar' | 'cambiar'
        this.listeners = [];
    }

    subscribe(listener) {
        this.listeners.push(listener);
    }

    notify() {
        this.listeners.forEach(cb => cb(this));
    }

    init() {
        const token = this.model.getToken();
        const user = this.model.getUser();
        if (token) {
            this.isAuthenticated = true;
            this.currentUser = user || { nombre_completo: 'Freddy', username: 'freddy' };
        } else {
            this.isAuthenticated = false;
            this.currentUser = null;
            this.activeAuthView = 'login';
        }
        this.notify();
    }

    switchView(viewName) {
        this.activeAuthView = viewName;
        this.notify();
    }

    async login(username, password) {
        if (!username || !password) {
            throw new Error('Por favor ingresa tu usuario y contraseña.');
        }
        const data = await this.model.login(username, password);
        this.isAuthenticated = true;
        this.currentUser = data.usuario || { nombre_completo: username, username: username };
        this.notify();
        return data;
    }

    async requestOtp(emailOUsername) {
        if (!emailOUsername) {
            throw new Error('Por favor ingresa tu correo o nombre de usuario.');
        }
        const data = await this.model.solicitarCodigo(emailOUsername);
        this.activeAuthView = 'cambiar';
        this.notify();
        return data;
    }

    async resetPassword(email, codigo, nuevaPass, confirmarPass) {
        if (!codigo || codigo.length < 6) {
            throw new Error('Por favor ingresa el código completo de 6 dígitos.');
        }
        if (nuevaPass !== confirmarPass) {
            throw new Error('Las contraseñas no coinciden. Verifícalas.');
        }
        if (nuevaPass.length < 4) {
            throw new Error('La nueva contraseña debe tener al menos 4 caracteres.');
        }

        const data = await this.model.cambiarPassword(email, codigo, nuevaPass);
        return data;
    }

    logout() {
        this.model.clearSession();
        this.isAuthenticated = false;
        this.currentUser = null;
        this.activeAuthView = 'login';
        this.notify();
    }
}

// Exportar al ámbito global para la arquitectura MVVM
window.AuthViewModel = AuthViewModel;

