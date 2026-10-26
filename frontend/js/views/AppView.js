/**
 * EQUIGRUP MVVM - VIEW: AppView
 * Responsabilidad: Enlace con el DOM, renderizado de componentes visuales y suscripción a los ViewModels.
 */
class AppView {
    constructor(authVM, projectsVM, chatVM, blogVM) {
        this.authVM = authVM;
        this.projectsVM = projectsVM;
        this.chatVM = chatVM;
        this.blogVM = blogVM;

        this.currentMainView = 'chat';
    }

    init() {
        this.cacheDom();
        this.bindEvents();
        this.subscribeViewModels();

        // Inicializar estado inicial
        this.authVM.init();
    }

    cacheDom() {
        // Auth
        this.authOverlay = document.getElementById('authPortalOverlay');
        this.mainApp = document.getElementById('mainAppContainer');
        this.userDisplayName = document.getElementById('userDisplayName');
        this.vAuthLogin = document.getElementById('authViewLogin');
        this.vAuthRecuperar = document.getElementById('authViewRecuperar');
        this.vAuthCambiar = document.getElementById('authViewCambiarPassword');

        // Navegación
        this.navBtns = document.querySelectorAll('.nav-btn');
        this.viewSections = document.querySelectorAll('.view-section');

        // Chat
        this.messagesContainer = document.getElementById('messagesContainer');
        this.userInput = document.getElementById('userInput');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.sendBtn = document.getElementById('sendBtn');
        this.chatForm = document.getElementById('chatForm');

        // Proyectos
        this.projectsGrid = document.getElementById('projectsGrid');
        this.contadorProyectos = document.getElementById('contadorProyectos');
        this.searchProyectosInput = document.getElementById('searchProyectosInput');
        this.filterEstado = document.getElementById('filterEstado');
        this.filterCategoria = document.getElementById('filterCategoria');

        // Blog
        this.blogGrid = document.getElementById('blogGrid');
        this.heroBannerShowcase = document.getElementById('heroBannerShowcase');
        this.blogCountBadge = document.getElementById('blogCountBadge');
        this.mediaProyectoSelect = document.getElementById('mediaProyectoSelect');
        this.blogProyectoSelect = document.getElementById('blogProyectoSelect');
    }

    subscribeViewModels() {
        // 1. Suscripción Auth
        this.authVM.subscribe(vm => this.renderAuth(vm));

        // 2. Suscripción Proyectos
        this.projectsVM.subscribe(vm => this.renderProjects(vm));

        // 3. Suscripción Chat
        this.chatVM.subscribe(vm => this.renderChat(vm));

        // 4. Suscripción Blog
        this.blogVM.subscribe(vm => this.renderBlog(vm));
    }

    bindEvents() {
        // Auto-ajuste de altura en textarea de chat
        if (this.userInput) {
            this.userInput.addEventListener('input', () => {
                this.userInput.style.height = 'auto';
                this.userInput.style.height = Math.min(this.userInput.scrollHeight, 100) + 'px';
            });
        }
    }

    // --- RENDERIZADO AUTH ---
    renderAuth(vm) {
        if (vm.isAuthenticated) {
            if (this.authOverlay) this.authOverlay.style.display = 'none';
            if (this.mainApp) this.mainApp.style.display = 'flex';
            if (this.userDisplayName && vm.currentUser) {
                this.userDisplayName.textContent = vm.currentUser.nombre_completo || vm.currentUser.username || 'Freddy';
            }
            this.projectsVM.loadProjects();
        } else {
            if (this.authOverlay) this.authOverlay.style.display = 'flex';
            if (this.mainApp) this.mainApp.style.display = 'none';

            if (this.vAuthLogin) this.vAuthLogin.style.display = (vm.activeAuthView === 'login') ? 'block' : 'none';
            if (this.vAuthRecuperar) this.vAuthRecuperar.style.display = (vm.activeAuthView === 'recuperar') ? 'block' : 'none';
            if (this.vAuthCambiar) this.vAuthCambiar.style.display = (vm.activeAuthView === 'cambiar') ? 'block' : 'none';
        }
    }

    // --- RENDERIZADO NAVEGACIÓN ---
    switchMainView(vista) {
        this.currentMainView = vista;
        this.navBtns.forEach(btn => btn.classList.remove('active'));
        this.viewSections.forEach(sec => sec.classList.remove('active'));

        const mapaNav = {
            'chat': { btn: 'navChat', sec: 'vistaChat' },
            'proyectos': { btn: 'navVer', sec: 'vistaProyectos' },
            'agregar': { btn: 'navAgregar', sec: 'vistaAgregar' },
            'multimedia': { btn: 'navMedia', sec: 'vistaMultimedia' },
            'blog': { btn: 'navBlog', sec: 'vistaBlog' },
            'microservicios': { btn: 'navMicroservicios', sec: 'vistaMicroservicios' }
        };

        const target = mapaNav[vista];
        if (target) {
            const b = document.getElementById(target.btn);
            const s = document.getElementById(target.sec);
            if (b) b.classList.add('active');
            if (s) s.classList.add('active');
        }

        if (vista === 'chat' && this.userInput) {
            this.userInput.focus();
        } else if (vista === 'proyectos') {
            this.projectsVM.loadProjects();
        } else if (vista === 'multimedia') {
            this.cargarOpcionesMultimedia();
        } else if (vista === 'blog') {
            this.blogVM.loadProjectOptions();
            this.blogVM.loadPosts();
        } else if (vista === 'microservicios' && typeof cargarDatosMicroservicioAuditoria === 'function') {
            cargarDatosMicroservicioAuditoria();
        }
    }

    // --- RENDERIZADO PROYECTOS ---
    renderProjects(vm) {
        if (!this.projectsGrid) return;

        if (this.contadorProyectos) {
            this.contadorProyectos.textContent = vm.projects.length;
        }

        if (vm.isLoading) {
            this.projectsGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #94a3b8;">🔄 Cargando proyectos sincronizados...</div>';
            return;
        }

        if (vm.error) {
            this.projectsGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: #ef4444;">Error: ${vm.error}</div>`;
            return;
        }

        if (!vm.filteredProjects || vm.filteredProjects.length === 0) {
            this.projectsGrid.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #94a3b8;">
                    <p>🔍 No se encontraron proyectos con los filtros seleccionados.</p>
                    <button class="btn-secondary" onclick="limpiarFiltros()" style="margin-top: 12px;">Ver todos los proyectos</button>
                </div>
            `;
            return;
        }

        this.projectsGrid.innerHTML = '';

        vm.filteredProjects.forEach(p => {
            const card = document.createElement('div');
            card.className = 'project-card';

            const titulo = p.titulo || 'Proyecto Sin Título';
            const cliente = p.cliente || 'No especificado';
            const ubicacion = p.ubicacion || 'Planta / Campo';
            const maquinaria = p.maquinaria || 'No especificada';
            const estado = p.estado || 'Completado';
            const categoria = p.categoria || 'Informe Técnico';
            const descripcion = p.descripcion || 'Sin detalles adicionales.';

            const tieneDoc = Boolean(p.tiene_documento && p.documento_url);
            const botonDoc = tieneDoc
                ? `<button class="btn-act btn-doc" onclick="window.open('${p.documento_url}', '_blank')" title="Abrir informe técnico original (${this.escaparHTML(p.documento_nombre || 'PDF')})">📄 Doc</button>`
                : `<button class="btn-act btn-doc-disabled" onclick="mostrarAvisoSinDoc('${this.escaparHTML(titulo).replace(/'/g, "\\'")}', ${p.id})" title="Proyecto sin archivo físico adjunto">📄 Sin Doc</button>`;

            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="badge badge-cat">${this.escaparHTML(categoria)}</span>
                    <span class="badge badge-status">${this.escaparHTML(estado)}</span>
                </div>
                <h3 class="project-card-title">${this.escaparHTML(titulo)}</h3>
                <div class="meta-row">
                    <div>🏢 <strong>Cliente:</strong> ${this.escaparHTML(cliente)}</div>
                    <div>📍 <strong>Ubicación:</strong> ${this.escaparHTML(ubicacion)}</div>
                    <div>⚙️ <strong>Maquinaria:</strong> ${this.escaparHTML(maquinaria)}</div>
                </div>
                <div class="desc-box">${this.escaparHTML(descripcion)}</div>
                <div class="btn-group">
                    <button class="btn-act btn-ask" onclick="consultarEquiSobreProyecto('${this.escaparHTML(titulo).replace(/'/g, "\\'")}')">💬 Preguntar</button>
                    ${botonDoc}
                    <button class="btn-act" onclick="abrirModalEditarPorId(${p.id})">✏️ Editar</button>
                    <button class="btn-act btn-del" onclick="eliminarProyecto(${p.id}, '${this.escaparHTML(titulo).replace(/'/g, "\\'")}')">🗑️</button>
                </div>
            `;

            this.projectsGrid.appendChild(card);
        });
    }

    // --- RENDERIZADO CHAT ---
    renderChat(vm) {
        if (!this.messagesContainer) return;

        if (this.typingIndicator) {
            this.typingIndicator.style.display = vm.isTyping ? 'flex' : 'none';
        }
        if (this.userInput) this.userInput.disabled = vm.isTyping;
        if (this.sendBtn) this.sendBtn.disabled = vm.isTyping;

        // Renderizar todos los mensajes
        this.messagesContainer.innerHTML = '';

        vm.messages.forEach(msg => {
            const msgDiv = document.createElement('div');
            if (msg.role === 'user') {
                msgDiv.className = 'message user-message';
                msgDiv.innerHTML = `
                    <div class="message-avatar">👤</div>
                    <div class="message-content">
                        <div class="message-bubble">${msg.formattedText}</div>
                    </div>
                `;
            } else {
                msgDiv.className = 'message assistant-message';

                let fuentesHTML = '';
                if (msg.sources && msg.sources.length > 0) {
                    const listaFuentes = msg.sources.map(f => {
                        const matchDoc = f.match(/Documento:\s*([^\(]+?)(?:\s*\((.*?)\))?$/i);
                        if (matchDoc) {
                            const docNombre = matchDoc[1].trim();
                            const extra = matchDoc[2] ? `(${matchDoc[2]})` : '';
                            const url = `/api/documentos/${encodeURIComponent(docNombre)}`;
                            return `
                                <li class="source-item source-doc">
                                    <div class="source-left">
                                        <span class="source-icon">📄</span>
                                        <span class="source-text"><strong>${this.escaparHTML(docNombre)}</strong> <small class="source-tag">${this.escaparHTML(extra)}</small></span>
                                    </div>
                                    <a href="${url}" target="_blank" rel="noopener noreferrer" class="source-action-btn" title="Abrir documento original">
                                        <span>Abrir Documento</span> ↗
                                    </a>
                                </li>
                            `;
                        }

                        const matchBD = f.match(/Base de Datos:\s*Proyecto\s*#(\d+)\s*-\s*(.+)/i);
                        if (matchBD) {
                            const pId = matchBD[1];
                            const pTitulo = matchBD[2];
                            return `
                                <li class="source-item source-bd">
                                    <div class="source-left">
                                        <span class="source-icon">🗄️</span>
                                        <span class="source-text"><strong>Proyecto #${pId}:</strong> ${this.escaparHTML(pTitulo)}</span>
                                    </div>
                                    <button type="button" onclick="cambiarVista('proyectos')" class="source-action-btn source-btn-cat" title="Consultar en el Catálogo">
                                        <span>Catálogo</span> ↗
                                    </button>
                                </li>
                            `;
                        }

                        return `
                            <li class="source-item">
                                <div class="source-left">
                                    <span class="source-icon">📌</span>
                                    <span class="source-text">${this.escaparHTML(f)}</span>
                                </div>
                            </li>
                        `;
                    }).join('');

                    fuentesHTML = `
                        <div class="sources-card">
                            <div class="sources-title">
                                <span class="sources-title-icon">📚</span> Documentos y Fuentes de Referencia:
                            </div>
                            <ul class="sources-list">${listaFuentes}</ul>
                        </div>
                    `;
                }

                msgDiv.innerHTML = `
                    <div class="message-avatar">🤖</div>
                    <div class="message-content">
                        <div class="message-bubble">
                            ${msg.formattedText}
                            ${fuentesHTML}
                        </div>
                    </div>
                `;
            }
            this.messagesContainer.appendChild(msgDiv);
        });

        this.scrollChatBottom();
    }

    scrollChatBottom() {
        if (this.messagesContainer) {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
    }

    // --- RENDERIZADO BLOG ---
    renderBlog(vm) {
        // 1. Contador
        if (this.blogCountBadge) {
            this.blogCountBadge.textContent = vm.posts.length;
        }

        // 2. Opciones de Proyectos en Select
        if (this.blogProyectoSelect && vm.projectOptions.length > 0) {
            const curVal = this.blogProyectoSelect.value;
            this.blogProyectoSelect.innerHTML = '<option value="">-- Redactar publicación libre (Sin vincular a proyecto) --</option>';
            vm.projectOptions.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.id;
                opt.textContent = `[#${p.id}] ${p.titulo} (${p.cliente || 'Equigrup'})`;
                this.blogProyectoSelect.appendChild(opt);
            });
            if (curVal) this.blogProyectoSelect.value = curVal;
        }

        // 3. Renderizar Banner Hero
        this.renderHeroBanner(vm.bannerPost);

        // 4. Renderizar Feed de Tarjetas
        this.renderBlogFeed(vm.posts);
    }

    renderHeroBanner(destacado) {
        if (!this.heroBannerShowcase) return;

        if (!destacado) {
            this.heroBannerShowcase.innerHTML = `
                <div style="background: linear-gradient(135deg, #1e293b, #0f172a); border: 2px dashed #334155; border-radius: 16px; padding: 40px; text-align: center; color: #94a3b8;">
                    <div style="font-size: 36px; margin-bottom: 8px;">🌐</div>
                    <h3 style="color: #f1f5f9; font-size: 18px; margin-bottom: 6px;">No hay publicaciones destacadas en el Banner Web aún</h3>
                    <p style="font-size: 13.5px; margin-bottom: 16px;">Crea una publicación marcando la casilla "⭐ Destacar en el Banner Principal" para ver cómo lucirá en la cabecera de la web.</p>
                    <button class="btn-primary-action" onclick="cambiarPestanaBlog('publicar')" style="padding: 10px 20px;">➕ Crear Primera Publicación para el Banner</button>
                </div>
            `;
            return;
        }

        let mediaHTML = '';
        if (destacado.tipo_multimedia === 'video' && destacado.multimedia_url) {
            mediaHTML = `
                <video autoplay muted loop playsinline style="width: 100%; height: 100%; object-fit: cover; position: absolute; top: 0; left: 0; filter: brightness(0.38);">
                    <source src="${destacado.multimedia_url}">
                </video>
            `;
        } else if (destacado.multimedia_url) {
            mediaHTML = `
                <div style="width: 100%; height: 100%; position: absolute; top: 0; left: 0; background-image: url('${destacado.multimedia_url}'); background-size: cover; background-position: center; filter: brightness(0.38);"></div>
            `;
        } else {
            mediaHTML = `
                <div style="width: 100%; height: 100%; position: absolute; top: 0; left: 0; background: linear-gradient(135deg, #0f172a, #1e3a8a); filter: brightness(0.6);"></div>
            `;
        }

        this.heroBannerShowcase.innerHTML = `
            <div style="position: relative; border-radius: 18px; overflow: hidden; min-height: 290px; border: 1px solid #38bdf8; box-shadow: 0 10px 30px rgba(0,0,0,0.6); display: flex; align-items: flex-end; padding: 32px; box-sizing: border-box;">
                ${mediaHTML}
                <div style="position: relative; z-index: 2; max-width: 720px;">
                    <div style="display: flex; gap: 8px; margin-bottom: 10px; align-items: center; flex-wrap: wrap;">
                        <span style="background: #2563eb; color: #fff; font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 20px; text-transform: uppercase; letter-spacing: 0.5px; box-shadow: 0 2px 8px rgba(37,99,235,0.5);">⭐ EN BANNER PRINCIPAL</span>
                        <span style="background: rgba(15,23,42,0.85); color: #38bdf8; font-size: 11.5px; font-weight: 600; padding: 4px 10px; border-radius: 6px; border: 1px solid #38bdf8;">${this.escaparHTML(destacado.categoria)}</span>
                        ${destacado.proyecto_titulo ? `<span style="background: rgba(16,185,129,0.2); color: #34d399; font-size: 11px; padding: 3px 8px; border-radius: 4px; border: 1px solid #10b981;">Obra: ${this.escaparHTML(destacado.proyecto_titulo)}</span>` : ''}
                    </div>
                    <h1 style="color: #ffffff; font-size: 24px; font-weight: 800; line-height: 1.25; margin: 0 0 8px 0; text-shadow: 0 2px 10px rgba(0,0,0,0.85);">${this.escaparHTML(destacado.titulo)}</h1>
                    <p style="color: #e2e8f0; font-size: 14px; line-height: 1.5; margin: 0 0 16px 0; text-shadow: 0 1px 6px rgba(0,0,0,0.85);">${this.escaparHTML(destacado.resumen || destacado.contenido.slice(0, 160) + '...')}</p>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <button class="btn-primary-action" onclick="consultarEquiSobreProyecto('${this.escaparHTML(destacado.titulo).replace(/'/g, "\\'")}')" style="padding: 9px 18px; font-size: 13px;">
                            💬 Consultar a Equi sobre esta Obra
                        </button>
                        <button class="btn-secondary" onclick="abrirModalEditarBlog(${destacado.id})" style="padding: 9px 16px; font-size: 13px;">
                            ✏️ Editar Banner
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    renderBlogFeed(lista) {
        if (!this.blogGrid) return;

        if (!lista || lista.length === 0) {
            this.blogGrid.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #94a3b8; background: #0f172a; border-radius: 12px; border: 1px solid #334155;">
                    <p>📭 No hay publicaciones registradas en el blog aún.</p>
                    <button class="btn-primary-action" onclick="cambiarPestanaBlog('publicar')" style="margin-top: 10px; padding: 8px 16px;">
                        ➕ Crear Primera Publicación
                    </button>
                </div>
            `;
            return;
        }

        this.blogGrid.innerHTML = '';

        lista.forEach(item => {
            const card = document.createElement('div');
            card.className = 'blog-card';

            let mediaThumb = '';
            if (item.tipo_multimedia === 'video' && item.multimedia_url) {
                mediaThumb = `
                    <div class="blog-media-box">
                        <video controls preload="metadata" style="width: 100%; height: 180px; object-fit: cover; background: #000; border-radius: 10px 10px 0 0;">
                            <source src="${item.multimedia_url}">
                        </video>
                        <span class="media-type-badge">🎬 Video</span>
                    </div>
                `;
            } else if (item.multimedia_url) {
                mediaThumb = `
                    <div class="blog-media-box" style="height: 180px; background-image: url('${item.multimedia_url}'); background-size: cover; background-position: center; border-radius: 10px 10px 0 0; position: relative;">
                        <span class="media-type-badge">📸 Foto</span>
                    </div>
                `;
            } else {
                mediaThumb = `
                    <div class="blog-media-box" style="height: 140px; background: linear-gradient(135deg, #1e293b, #0f172a); display: flex; align-items: center; justify-content: center; border-radius: 10px 10px 0 0;">
                        <span style="font-size: 36px; opacity: 0.6;">📰</span>
                    </div>
                `;
            }

            const bannerBadge = item.es_banner
                ? `<span class="badge" style="background: rgba(37,99,235,0.2); color: #60a5fa; border: 1px solid #3b82f6;">⭐ En Banner</span>`
                : `<span class="badge" style="background: rgba(100,116,139,0.2); color: #94a3b8; border: 1px solid #475569;">Blog Normal</span>`;

            card.innerHTML = `
                ${mediaThumb}
                <div class="blog-card-body" style="padding: 16px; display: flex; flex-direction: column; flex: 1;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span class="badge badge-cat">${this.escaparHTML(item.categoria)}</span>
                        ${bannerBadge}
                    </div>
                    <h3 style="font-size: 15px; font-weight: 700; color: #ffffff; margin: 0 0 6px 0; line-height: 1.35;">${this.escaparHTML(item.titulo)}</h3>
                    ${item.resumen ? `<p style="font-size: 12.5px; color: #38bdf8; font-weight: 500; margin: 0 0 8px 0;">${this.escaparHTML(item.resumen)}</p>` : ''}
                    <div style="font-size: 12px; color: #cbd5e1; line-height: 1.45; margin-bottom: 12px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;">
                        ${this.escaparHTML(item.contenido)}
                    </div>
                    <div style="margin-top: auto; padding-top: 10px; border-top: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: #94a3b8; margin-bottom: 10px;">
                        <span>✍️ ${this.escaparHTML(item.autor)}</span>
                        <span>📅 ${item.creado_en || ''}</span>
                    </div>
                    <div class="btn-group" style="margin-top: 0; padding-top: 0; border-top: none;">
                        <button class="btn-act ${item.es_banner ? 'btn-ask' : ''}" onclick="toggleBannerPublicacion(${item.id})" title="Alternar presencia en el Banner Hero">
                            ${item.es_banner ? '⭐ Quitar Banner' : '⭐ Destacar'}
                        </button>
                        <button class="btn-act" onclick="abrirModalEditarBlog(${item.id})">✏️ Editar</button>
                        <button class="btn-act btn-del" onclick="eliminarPublicacionBlog(${item.id}, '${this.escaparHTML(item.titulo).replace(/'/g, "\\'")}')">🗑️</button>
                    </div>
                </div>
            `;

            this.blogGrid.appendChild(card);
        });
    }

    async cargarOpcionesMultimedia() {
        if (!this.mediaProyectoSelect) return;
        try {
            const proyectos = await this.projectsVM.model.obtenerTodos();
            this.mediaProyectoSelect.innerHTML = '<option value="">-- Sin asociar / Galería General --</option>';
            proyectos.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.id;
                opt.textContent = `[#${p.id}] ${p.titulo}`;
                this.mediaProyectoSelect.appendChild(opt);
            });
        } catch (e) {
            console.error('Error cargando multimedia select:', e);
        }
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
}

// Exportar al ámbito global para la arquitectura MVVM
window.AppView = AppView;

