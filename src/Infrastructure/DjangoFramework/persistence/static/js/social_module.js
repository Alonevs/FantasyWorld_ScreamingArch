/**
 * Social Module - Sistema de Interacción Social Universal
 * Maneja likes, comentarios y compartir para cualquier tipo de contenido
 */

class SocialModule {
    constructor() {
        this.activeCommentPanels = new Set();
    }

    /**
     * Inicializa todos los componentes sociales en la página
     */
    init() {
        document.querySelectorAll('.social-card').forEach(card => {
            const entityKey = card.dataset.entityKey;
            if (entityKey) {
                this.loadLikeStatus(entityKey);
                this.loadCommentCount(entityKey);
            }
        });
    }

    /**
     * Toggle like en un contenido
     */
    async toggleLike(entityKey) {
        try {
            const response = await fetch('/api/likes/toggle/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: `entity_key=${encodeURIComponent(entityKey)}`
            });

            if (response.status === 401 || response.status === 403 || response.redirected) {
                if (window.CaosModal) {
                    CaosModal.alert('Acceso Restringido', 'Debes iniciar sesión para dar "Me gusta".');
                } else {
                    alert('Debes iniciar sesión para dar "Me gusta".');
                }
                return;
            }

            const data = await response.json();
            this.updateLikeUI(entityKey, data);
        } catch (error) {
            console.error('Error toggling like:', error);
        }
    }

    /**
     * Carga el estado de like actual
     */
    async loadLikeStatus(entityKey) {
        try {
            const response = await fetch(`/api/likes/status/?entity_key=${encodeURIComponent(entityKey)}`);
            const data = await response.json();
            this.updateLikeUI(entityKey, data);
        } catch (error) {
            console.error('Error loading like status:', error);
        }
    }

    /**
     * Actualiza la UI de likes
     */
    updateLikeUI(entityKey, data) {
        const slug = entityKey.replace(/[^a-z0-9]/gi, '-').toLowerCase();
        const iconEl = document.getElementById(`like-icon-${slug}`);
        const countEl = document.getElementById(`like-count-${slug}`);

        if (iconEl) {
            iconEl.textContent = data.user_has_liked ? '❤️' : '🤍';
        }
        if (countEl) {
            countEl.textContent = data.count || 0;
        }
    }

    /**
     * Toggle panel de comentarios
     */
    async toggleComments(entityKey) {
        const panelId = `comments-panel-${entityKey.replace(/[^a-z0-9]/gi, '-').toLowerCase()}`;
        let panel = document.getElementById(panelId);

        if (panel) {
            // Si ya existe, toggle visibility
            panel.classList.toggle('hidden');
            if (!panel.classList.contains('hidden')) {
                await this.loadComments(entityKey);
            }
        } else {
            // Crear panel
            await this.createCommentsPanel(entityKey);
        }
    }

    /**
     * Crea el panel de comentarios
     */
    async createCommentsPanel(entityKey) {
        const slug = entityKey.replace(/[^a-z0-9]/gi, '-').toLowerCase();
        const panelId = `comments-panel-${slug}`;

        // Buscar el contenedor (puede variar según el contexto)
        const container = document.querySelector(`[data-entity-key="${entityKey}"]`)?.parentElement || document.body;

        const panel = document.createElement('div');
        panel.id = panelId;
        panel.className = 'comments-panel bg-gray-900/95 border border-gray-800 rounded-2xl p-6 mt-4';
        panel.innerHTML = `
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-bold text-white">Comentarios</h3>
                <button onclick="socialModule.toggleComments('${entityKey}')" class="text-gray-500 hover:text-white">✕</button>
            </div>
            
            <div id="comments-list-${slug}" class="space-y-4 mb-4 max-h-96 overflow-y-auto">
                <p class="text-gray-500 text-center py-4">Cargando comentarios...</p>
            </div>
            
            <div class="comment-input-wrapper flex gap-2">
                <input type="text" 
                       id="comment-input-${slug}" 
                       placeholder="Escribe un comentario..." 
                       class="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none">
                <button onclick="socialModule.postComment('${entityKey}')" 
                        class="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-lg font-bold transition">
                    Enviar
                </button>
            </div>
        `;

        container.appendChild(panel);
        await this.loadComments(entityKey);
    }

    /**
     * Carga comentarios de un contenido
     */
    async loadComments(entityKey, customContainerId = null) {
        const slug = entityKey.replace(/[^a-z0-9]/gi, '-').toLowerCase();
        const listEl = customContainerId ? document.getElementById(customContainerId) : document.getElementById(`comments-list-${slug}`);
        
        if (!listEl) {
            console.warn(`Comments container not found: ${customContainerId || 'comments-list-' + slug}`);
            return;
        }

        try {
            const response = await fetch(`/api/comments/get/?entity_key=${encodeURIComponent(entityKey)}`);
            const data = await response.json();

            // Handle UI for anonymous users
            this.updateCommentInputVisibility(entityKey, data.authenticated);

            if (data.comments && data.comments.length > 0) {
                const validComments = data.comments.filter(c => c !== null);
                listEl.innerHTML = validComments.map(c => this.renderComment(c, entityKey, customContainerId, data.authenticated)).join('');
            } else {
                listEl.innerHTML = '<p class="text-gray-500 text-center py-4">No hay comentarios aún. ¡Sé el primero!</p>';
            }

            // Actualizar contador
            this.updateCommentCount(entityKey, data.comments.length);
        } catch (error) {
            console.error('Error loading comments:', error);
            const errorText = error.message.includes('Unexpected token') ? 'Error de servidor (Respuesta no válida)' : error.message;
            listEl.innerHTML = `<p class="text-red-500 text-center py-4">Error al cargar comentarios: ${errorText}. Por favor, recarga la página.</p>`;
        }
    }

    /**
     * Actualiza la visibilidad de la caja de comentarios según si el usuario está logueado
     */
    updateCommentInputVisibility(entityKey, isAuthenticated) {
        const slug = entityKey.replace(/[^a-z0-9]/gi, '-').toLowerCase();
        const inputWrappers = document.querySelectorAll(`[id^="comment-input-wrapper-${slug}"], #comments-panel-${slug} .comment-input-wrapper`);
        
        inputWrappers.forEach(wrapper => {
            if (!isAuthenticated) {
                wrapper.innerHTML = `
                    <div class="w-full p-4 bg-gray-800/30 border border-dashed border-gray-700 rounded-xl text-center">
                        <p class="text-xs text-gray-500 italic">
                            Inicia sesión para participar en la conversación.
                        </p>
                    </div>
                `;
            }
        });
    }

    /**
     * Renderiza un comentario individual
     */
    renderComment(comment, entityKey, customContainerId = null, isAuthenticated = true) {
        const avatarUrl = comment.avatar_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(comment.username)}&size=48`;
        const userIsOwner = comment.can_delete;
        
        const replyCount = comment.replies ? comment.replies.length : 0;
        const hasReplies = replyCount > 0;
        
        return `
            <div class="comment-item bg-gray-800/50 rounded-lg p-4">
                <div class="flex gap-3">
                    <img src="${avatarUrl}" alt="${comment.username}" class="w-8 h-8 rounded-full shrink-0">
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-1">
                            <span class="font-bold text-white text-sm">${comment.username}</span>
                            <span class="text-xs text-gray-500">${comment.date}</span>
                        </div>
                        <p class="text-gray-300 text-sm mb-2">${comment.content}</p>
                        
                        <!-- Comment Actions -->
                        <div class="flex items-center gap-3 text-xs">
                            <button onclick="socialModule.toggleCommentLike(${comment.id})" 
                                    class="flex items-center gap-1 text-gray-500 hover:text-yellow-400 transition">
                                <span id="comment-like-icon-${comment.id}">🤍</span>
                                <span id="comment-like-count-${comment.id}">0</span>
                            </button>
                            
                            ${isAuthenticated ? `
                            <button onclick="socialModule.replyToComment(${comment.id}, '${comment.username}')" 
                                    class="text-gray-500 hover:text-blue-400 transition font-medium">
                                Responder
                            </button>
                            ` : ''}

                            ${userIsOwner ? `
                            <button onclick="socialModule.deleteComment(${comment.id}, '${entityKey}', '${customContainerId || ''}')" 
                                    class="text-gray-500 hover:text-red-400 transition">
                                🗑️
                            </button>
                            ` : ''}
                        </div>
                        
                        <!-- Reply Form Container (Modern Pill Style) -->
                        <div id="reply-form-${comment.id}" class="mt-3 hidden">
                            <div class="flex items-center gap-2 bg-gray-900/50 rounded-full px-3 py-2 border border-gray-700 focus-within:border-blue-500 transition">
                                <input type="text" 
                                       id="reply-input-${comment.id}" 
                                       placeholder="Responde a ${comment.username}..." 
                                       class="flex-1 bg-transparent text-sm text-white focus:outline-none placeholder-gray-500"
                                       onkeypress="if(event.key === 'Enter') socialModule.postComment('${entityKey}', ${comment.id}, null, '${customContainerId || ''}')">
                                <button onclick="socialModule.postComment('${entityKey}', ${comment.id}, null, '${customContainerId || ''}')" 
                                        class="text-blue-500 hover:text-blue-400 transition">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
                                </button>
                            </div>
                        </div>
                        
                        ${hasReplies ? `
                            <!-- Collapsible Replies Toggle -->
                            <button onclick="socialModule.toggleReplies(${comment.id})" 
                                    id="toggle-replies-${comment.id}"
                                    class="mt-3 flex items-center gap-2 text-xs font-bold text-blue-500 hover:text-blue-400 transition">
                                <span id="toggle-icon-${comment.id}">▼</span>
                                <span>${replyCount} ${replyCount === 1 ? 'respuesta' : 'respuestas'}</span>
                            </button>
                            
                            <!-- Replies Container (Collapsible) -->
                            <div id="replies-${comment.id}" class="ml-8 mt-3 space-y-3 border-l-2 border-gray-700/50 pl-4 hidden">
                                ${comment.replies.map(r => this.renderComment(r, entityKey, customContainerId, isAuthenticated)).join('')}
                            </div>
                        ` : ''}
                </div>
            </div>
        </div>
        `;
    }

    /**
     * Toggle visibility of replies
     */
    toggleReplies(commentId) {
        const repliesContainer = document.getElementById(`replies-${commentId}`);
        const toggleIcon = document.getElementById(`toggle-icon-${commentId}`);
        
        if (repliesContainer && toggleIcon) {
            const isHidden = repliesContainer.classList.contains('hidden');
            
            if (isHidden) {
                repliesContainer.classList.remove('hidden');
                toggleIcon.textContent = '▲';
            } else {
                repliesContainer.classList.add('hidden');
                toggleIcon.textContent = '▼';
            }
        }
    }

    /**
     * Toggle like en un comentario específico
     */
    async toggleCommentLike(commentId) {
        try {
            const response = await fetch('/api/comments/like/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({ comment_id: commentId })
            });

            const data = await response.json();
            
            // Actualizar UI
            const iconEl = document.getElementById(`comment-like-icon-${commentId}`);
            const countEl = document.getElementById(`comment-like-count-${commentId}`);
            
            if (iconEl) {
                iconEl.textContent = data.user_has_liked ? '❤️' : '🤍';
            }
            if (countEl) {
                countEl.textContent = data.count;
            }
        } catch (error) {
            console.error('Error toggling comment like:', error);
        }
    }


    /**
     * Responder a un comentario
     */
    replyToComment(commentId, username) {
        const formEl = document.getElementById(`reply-form-${commentId}`);
        const inputEl = document.getElementById(`reply-input-${commentId}`);
        
        if (formEl) {
            formEl.classList.toggle('hidden');
            if (!formEl.classList.contains('hidden')) {
                inputEl.focus();
            }
        }
    }

    /**
     * Publica un nuevo comentario
     */
    async postComment(entityKey, parentId = null, customInputId = null, customContainerId = null) {
        const slug = entityKey.replace(/[^a-z0-9]/gi, '-').toLowerCase();
        const inputEl = parentId ? document.getElementById(`reply-input-${parentId}`) : 
                       (customInputId ? document.getElementById(customInputId) : document.getElementById(`comment-input-${slug}`));
        
        if (!inputEl) {
            console.warn(`Comment input not found: ${customInputId || (parentId ? 'reply-input-' + parentId : 'comment-input-' + slug)}`);
            return;
        }
        
        const content = inputEl.value.trim();

        if (!content) return;

        try {
            const response = await fetch('/api/comments/post/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: `entity_key=${encodeURIComponent(entityKey)}&content=${encodeURIComponent(content)}&parent_comment_id=${parentId || ''}`
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.error || `Error ${response.status}`);
            }

            const data = await response.json();
            if (data.status === 'ok') {
                inputEl.value = '';
                if (parentId) {
                    const form = document.getElementById(`reply-form-${parentId}`);
                    if (form) form.classList.add('hidden');
                }
                await this.loadComments(entityKey, customContainerId);
            } else {
                throw new Error(data.message || 'Error desconocido');
            }
        } catch (error) {
            console.error('Error posting comment:', error);
            if (window.CaosModal) {
                CaosModal.alert("Error", "No se pudo enviar el comentario: " + error.message);
            } else {
                alert("Error: " + error.message);
            }
        }
    }

    /**
     * Carga el contador de comentarios
     */
    async loadCommentCount(entityKey) {
        try {
            const response = await fetch(`/api/comments/get/?entity_key=${encodeURIComponent(entityKey)}`);
            const data = await response.json();
            this.updateCommentCount(entityKey, data.comments?.length || 0);
        } catch (error) {
            console.error('Error loading comment count:', error);
        }
    }

    /**
     * Actualiza el contador de comentarios en la UI
     */
    updateCommentCount(entityKey, count) {
        const slug = entityKey.replace(/[^a-z0-9]/gi, '-').toLowerCase();
        const countEl = document.getElementById(`comment-count-${slug}`);
        if (countEl) {
            countEl.textContent = count;
        }
        
        // Sincronizar también el contador del lightbox si está abierto
        const lbCountEl = document.getElementById('lb-overlay-count');
        if (lbCountEl && entityKey.startsWith('IMG_')) {
            lbCountEl.textContent = count;
        }
        const lbBadge = document.getElementById('lb-comment-count-badge');
        if (lbBadge && entityKey.startsWith('IMG_')) {
            lbBadge.textContent = count;
        }
    }

    /**
     * Compartir contenido
     */
    async shareContent(entityKey) {
        const url = window.location.href;
        
        if (navigator.share) {
            try {
                await navigator.share({
                    title: 'Compartir contenido',
                    url: url
                });
            } catch (error) {
                console.log('Share cancelled or failed:', error);
            }
        } else {
            // Fallback: copiar al portapapeles
            try {
                await navigator.clipboard.writeText(url);
                if (window.CaosModal) {
                    CaosModal.alert('Enlace Copiado', '¡El link se ha copiado al portapapeles!');
                } else {
                    alert('¡Link copiado al portapapeles!');
                }
            } catch (error) {
                console.error('Error copying to clipboard:', error);
            }
        }
    }

    /**
     * Borrar un comentario
     */
    async deleteComment(commentId, entityKey, customContainerId = null) {
        let confirmed = false;
        if (window.CaosModal) {
            confirmed = await CaosModal.confirm('Borrar Comentario', '¿Estás seguro de que quieres borrar este comentario? Esta acción eliminará también todas sus respuestas.', true);
        } else {
            confirmed = confirm('¿Estás seguro de que quieres borrar este comentario?');
        }

        if (!confirmed) return;

        try {
            const response = await fetch('/api/comments/delete/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({ comment_id: commentId })
            });

            const data = await response.json().catch(() => ({}));

            if (response.ok && data.status === 'ok') {
                this.loadComments(entityKey, customContainerId);
            } else {
                const errorMsg = data.error || 'No se pudo borrar el comentario';
                if (window.CaosModal) {
                    CaosModal.alert('Error de Moderación', errorMsg);
                } else {
                    alert(errorMsg);
                }
            }
        } catch (error) {
            console.error('Error deleting comment:', error);
            if (window.CaosModal) {
                CaosModal.alert('Error', 'Hubo un problema de conexión al intentar borrar el comentario.');
            }
        }
    }

    /**
     * Obtiene cookie CSRF
     */
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Instancia global
const socialModule = new SocialModule();

// Inicializar al cargar la página
document.addEventListener('DOMContentLoaded', () => {
    socialModule.init();
});
