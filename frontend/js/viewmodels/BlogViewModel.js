/**
 * EQUIGRUP MVVM - VIEWMODEL: BlogViewModel
 * Responsabilidad: Manejo del feed del blog, banner hero principal, pestañas de publicación y autocompletado.
 */
class BlogViewModel {
    constructor(blogModel, projectModel) {
        this.model = blogModel || new BlogModel();
        this.projectModel = projectModel || new ProjectModel();
        this.posts = [];
        this.bannerPost = null;
        this.activeTab = 'feed'; // 'feed' | 'publicar'
        this.projectOptions = [];
        this.isLoading = false;
        this.listeners = [];
    }

    subscribe(listener) {
        this.listeners.push(listener);
    }

    notify() {
        this.listeners.forEach(cb => cb(this));
    }

    setTab(tabName) {
        this.activeTab = tabName;
        this.notify();
    }

    async loadPosts() {
        this.isLoading = true;
        this.notify();

        try {
            this.posts = await this.model.obtenerPublicaciones();
            const bannerItems = this.posts.filter(p => p.es_banner);
            this.bannerPost = bannerItems.length > 0 ? bannerItems[0] : (this.posts[0] || null);
        } catch (e) {
            console.error('Error cargando blog:', e);
            this.posts = [];
            this.bannerPost = null;
        } finally {
            this.isLoading = false;
            this.notify();
        }
    }

    async loadProjectOptions() {
        try {
            this.projectOptions = await this.projectModel.obtenerTodos();
            this.notify();
        } catch (e) {
            console.error('Error cargando proyectos para blog:', e);
        }
    }

    getProjectForAutofill(projectId) {
        return this.projectOptions.find(p => p.id === parseInt(projectId));
    }

    async publishPost(formData) {
        const resultado = await this.model.publicar(formData);
        await this.loadPosts();
        this.activeTab = 'feed';
        this.notify();
        return resultado;
    }

    async updatePost(id, datos) {
        const resultado = await this.model.actualizar(id, datos);
        await this.loadPosts();
        return resultado;
    }

    async deletePost(id) {
        const resultado = await this.model.eliminar(id);
        await this.loadPosts();
        return resultado;
    }

    async toggleBanner(id) {
        const resultado = await this.model.alternarBanner(id);
        await this.loadPosts();
        return resultado;
    }

    getPostById(id) {
        return this.posts.find(p => p.id === id);
    }
}

// Exportar al ámbito global para la arquitectura MVVM
window.BlogViewModel = BlogViewModel;

