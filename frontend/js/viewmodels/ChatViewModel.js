/**
 * EQUIGRUP MVVM - VIEWMODEL: ChatViewModel
 * Responsabilidad: Manejo del estado del chat con IA, formateo Markdown, enlaces a documentos y gestión de fuentes.
 */
class ChatViewModel {
    constructor(chatModel) {
        this.model = chatModel || new ChatModel();
        this.messages = [];
        this.isTyping = false;
        this.listeners = [];
    }

    subscribe(listener) {
        this.listeners.push(listener);
    }

    notify() {
        this.listeners.forEach(cb => cb(this));
    }

    escaparHTML(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    formatMarkdown(texto) {
        if (!texto) return '';

        let resultado = this.escaparHTML(texto);

        // 1. Negrita **texto** -> <strong>texto</strong>
        resultado = resultado.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // 2. Enlaces Markdown [Texto](URL)
        resultado = resultado.replace(/\[(.*?)\]\((.*?)\)/g, (match, label, url) => {
            let cleanUrl = url.trim();
            let isDoc = cleanUrl.includes('/api/documentos') || cleanUrl.includes('/documents') || /\.(pdf|docx?|xlsx?|png|jpe?g)/i.test(cleanUrl) || /\.(pdf|docx?|xlsx?)/i.test(label);
            if (isDoc) {
                return `\n<div class="doc-reference-card"><div class="doc-ref-left"><span class="doc-ref-icon">📄</span><span class="doc-ref-name">${label}</span></div><a href="${cleanUrl}" target="_blank" rel="noopener noreferrer" class="doc-ref-btn">Abrir Documento ↗</a></div>\n`;
            }
            return `<a href="${cleanUrl}" target="_blank" rel="noopener noreferrer" class="chat-custom-link">${label} ↗</a>`;
        });

        // 3. Detectar menciones de archivos en texto plano (.pdf o .docx)
        const docRegex = /(?:^|\n)(?:[\*\-]\s*)?([a-zA-Z0-9_\-\s,\.áéíóúÁÉÍÓÚ°#]+\.(?:pdf|docx|doc|xlsx))\b(?![^<]*<\/a>)/gi;
        resultado = resultado.replace(docRegex, (match, filename) => {
            let cleanName = filename.trim();
            let fileUrl = `/api/documentos/${encodeURIComponent(cleanName)}`;
            return `\n<div class="doc-reference-card"><div class="doc-ref-left"><span class="doc-ref-icon">📄</span><span class="doc-ref-name">${cleanName}</span></div><a href="${fileUrl}" target="_blank" rel="noopener noreferrer" class="doc-ref-btn">Abrir Documento ↗</a></div>\n`;
        });

        // 4. Saltos de línea
        resultado = resultado.replace(/\n/g, '<br>');

        // Limpiar espaciados alrededor de tarjetas
        resultado = resultado.replace(/(?:<br>\s*)+<div class="doc-reference-card">/g, '<div class="doc-reference-card">');
        resultado = resultado.replace(/<\/div>(?:\s*<br>)+/g, '</div>');

        return resultado;
    }

    async sendMessage(texto) {
        const query = (texto || '').trim();
        if (!query) return;

        // Agregar mensaje del usuario al historial
        this.messages.push({
            role: 'user',
            text: query,
            formattedText: this.escaparHTML(query).replace(/\n/g, '<br>'),
            sources: []
        });

        this.isTyping = true;
        this.notify();

        try {
            const data = await this.model.enviarMensaje(query);
            this.messages.push({
                role: 'assistant',
                text: data.respuesta,
                formattedText: this.formatMarkdown(data.respuesta),
                sources: data.fuentes_consultadas || []
            });
        } catch (e) {
            this.messages.push({
                role: 'assistant',
                text: `⚠️ Error al procesar solicitud: ${e.message}`,
                formattedText: `⚠️ <strong>Error al procesar solicitud:</strong> ${this.escaparHTML(e.message)}`,
                sources: []
            });
        } finally {
            this.isTyping = false;
            this.notify();
        }
    }
}

// Exportar al ámbito global para la arquitectura MVVM
window.ChatViewModel = ChatViewModel;

