/**
 * EQUIGRUP MVVM - MODEL: BlogModel
 * Responsabilidad: Gestión de publicaciones y contenido del Banner Web (/api/blog).
 */
class BlogModel {
    constructor() {
        this.baseUrl = '/api/blog';
    }

    async obtenerPublicaciones() {
        const res = await fetch(this.baseUrl);
        if (!res.ok) throw new Error('No se pudieron obtener las publicaciones del blog');
        return await res.json();
    }

    async publicar(formData) {
        const res = await fetch(`${this.baseUrl}/publicar`, {
            method: 'POST',
            body: formData
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Error al publicar en el blog');
        }
        return await res.json();
    }

    async actualizar(id, datos) {
        const res = await fetch(`${this.baseUrl}/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datos)
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Error al actualizar publicación');
        }
        return await res.json();
    }

    async eliminar(id) {
        const res = await fetch(`${this.baseUrl}/${id}`, {
            method: 'DELETE'
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Error al eliminar publicación');
        }
        return await res.json();
    }

    async alternarBanner(id) {
        const res = await fetch(`${this.baseUrl}/${id}/toggle-banner`, {
            method: 'POST'
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Error al alternar estado de banner');
        }
        return await res.json();
    }
}

// Exportar al ámbito global para la arquitectura MVVM
window.BlogModel = BlogModel;

