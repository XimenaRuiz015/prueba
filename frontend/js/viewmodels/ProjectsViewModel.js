/**
 * EQUIGRUP MVVM - VIEWMODEL: ProjectsViewModel
 * Responsabilidad: Manejo del estado del catálogo de proyectos, filtros en tiempo real, normalización y operaciones CRUD.
 */
class ProjectsViewModel {
    constructor(projectModel) {
        this.model = projectModel || new ProjectModel();
        this.projects = [];
        this.filteredProjects = [];
        this.selectedProject = null;
        this.filterText = '';
        this.filterEstado = '';
        this.filterCategoria = '';
        this.isLoading = false;
        this.error = null;
        this.listeners = [];
    }

    subscribe(listener) {
        this.listeners.push(listener);
    }

    notify() {
        this.listeners.forEach(cb => cb(this));
    }

    normalizarTexto(txt) {
        if (!txt) return '';
        return txt.toString().toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim();
    }

    async loadProjects() {
        this.isLoading = true;
        this.error = null;
        this.notify();

        try {
            this.projects = await this.model.obtenerTodos();
            this.applyFilters();
        } catch (e) {
            this.error = e.message;
            this.projects = [];
            this.filteredProjects = [];
        } finally {
            this.isLoading = false;
            this.notify();
        }
    }

    setFilters(text, estado, categoria) {
        this.filterText = text !== undefined ? text : this.filterText;
        this.filterEstado = estado !== undefined ? estado : this.filterEstado;
        this.filterCategoria = categoria !== undefined ? categoria : this.filterCategoria;
        this.applyFilters();
    }

    applyFilters() {
        const texto = this.normalizarTexto(this.filterText);
        const estado = this.normalizarTexto(this.filterEstado);
        const categoria = this.normalizarTexto(this.filterCategoria);

        this.filteredProjects = this.projects.filter(p => {
            const pTitulo = this.normalizarTexto(p.titulo);
            const pCliente = this.normalizarTexto(p.cliente);
            const pUbicacion = this.normalizarTexto(p.ubicacion);
            const pMaquinaria = this.normalizarTexto(p.maquinaria);
            const pDesc = this.normalizarTexto(p.descripcion);
            const pEstado = this.normalizarTexto(p.estado);
            const pCategoria = this.normalizarTexto(p.categoria);

            const coincideTexto = !texto || (
                pTitulo.includes(texto) ||
                pCliente.includes(texto) ||
                pUbicacion.includes(texto) ||
                pMaquinaria.includes(texto) ||
                pDesc.includes(texto)
            );

            const coincideEstado = !estado || pEstado.includes(estado);
            const coincideCategoria = !categoria || pCategoria.includes(categoria);

            return coincideTexto && coincideEstado && coincideCategoria;
        });

        this.notify();
    }

    clearFilters() {
        this.filterText = '';
        this.filterEstado = '';
        this.filterCategoria = '';
        this.applyFilters();
    }

    async saveProject(datos, archivoFoto) {
        let imagenUrl = null;

        if (archivoFoto) {
            const formData = new FormData();
            formData.append('archivo', archivoFoto);
            formData.append('titulo', 'Foto Principal');
            formData.append('seccion', 'portada');

            const uploadRes = await this.model.subirArchivo(formData);
            imagenUrl = uploadRes.url;
        }

        const nuevoProyecto = {
            titulo: datos.titulo.trim(),
            cliente: datos.cliente.trim() || 'Cliente No Especificado',
            ubicacion: datos.ubicacion.trim() || 'Planta / Campo',
            categoria: datos.categoria,
            estado: datos.estado,
            maquinaria: datos.maquinaria.trim() || 'No especificada',
            descripcion: datos.descripcion.trim(),
            imagen_url: imagenUrl,
            creado_por: 'Freddy'
        };

        const resultado = await this.model.crear(nuevoProyecto);
        await this.loadProjects();
        return resultado;
    }

    async updateProject(id, datos) {
        const resultado = await this.model.actualizar(id, datos);
        await this.loadProjects();
        return resultado;
    }

    async deleteProject(id) {
        const resultado = await this.model.eliminar(id);
        await this.loadProjects();
        return resultado;
    }

    getProjectById(id) {
        return this.projects.find(p => p.id === id);
    }
}

// Exportar al ámbito global para la arquitectura MVVM
window.ProjectsViewModel = ProjectsViewModel;

