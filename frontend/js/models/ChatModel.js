/**
 * EQUIGRUP MVVM - MODEL: ChatModel
 * Responsabilidad: Comunicación con el servicio de IA y RAG (/chat).
 */
class ChatModel {
    constructor() {
        this.chatUrl = '/chat';
    }

    async enviarMensaje(mensaje) {
        const res = await fetch(this.chatUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mensaje: mensaje })
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `Error en el servidor: ${res.status}`);
        }
        return await res.json();
    }
}

// Exportar al ámbito global para la arquitectura MVVM
window.ChatModel = ChatModel;

