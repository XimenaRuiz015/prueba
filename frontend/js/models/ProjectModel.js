/**
 * EQUIGRUP MVVM - MODEL: ProjectModel
 * Responsabilidad: Gestión de llamadas a la API REST de Proyectos y Carga de Archivos.
 */
class ProjectModel {
    constructor() {
        this.baseUrl = '/api/proyectos';
        this.uploadUrl = '/api/upload';
    }

    async obtenerTodos() {
        const res = await fetch(this.baseUrl);
        if (!res.ok) throw new Error('No se pudo obtener el listado de proyectos');
        return await res.json();
    }

    async obtenerPorId(id) {
        const res = await fetch(`${this.baseUrl}/${id}`);
        if (!res.ok) throw new Error('Proyecto no encontrado');
        return await res.json();
    }

    async crear(datosProyecto) {
        const res = await fetch(this.baseUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datosProyecto)
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'No se pudo registrar el proyecto');
        }
        return await res.json();
    }

    async actualizar(id, datosActualizados) {
        const res = await fetch(`${this.baseUrl}/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datosActualizados)
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Error al actualizar el proyecto');
        }
        return await res.json();
    }

    async eliminar(id) {
        const res = await fetch(`${this.baseUrl}/${id}`, {
            method: 'DELETE'
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Error al eliminar el proyecto');
        }
        return await res.json();
    }

    async subirArchivo(formData) {
        const res = await fetch(this.uploadUrl, {
            method: 'POST',
            body: formData
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Error al subir el archivo');
        }
        return await res.json();
    }
}

// Exportar al ámbito global para la arquitectura MVVM
window.ProjectModel = ProjectModel;

