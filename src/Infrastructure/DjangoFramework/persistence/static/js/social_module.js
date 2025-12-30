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
    async loadComments(entityKey) {
        const slug = entityKey.replace(/[^a-z0-9]/gi, '-').toLowerCase();
        const listEl = document.getElementById(`comments-list-${slug}`);

        try {
            const response = await fetch(`/api/comments/get/?entity_key=${encodeURIComponent(entityKey)}`);
            const data = await response.json();

            if (data.comments && data.comments.length > 0) {
                listEl.innerHTML = data.comments.map(comment => this.renderComment(comment, entityKey)).join('');
            } else {
                listEl.innerHTML = '<p class="text-gray-500 text-center py-4">No hay comentarios aún. ¡Sé el primero!</p>';
            }

            // Actualizar contador
            this.updateCommentCount(entityKey, data.comments.length);
        } catch (error) {
            console.error('Error loading comments:', error);
            listEl.innerHTML = '<p class="text-red-500 text-center py-4">Error al cargar comentarios</p>';
        }
    }

    /**
     * Renderiza un comentario individual
     */
    renderComment(comment, entityKey) {
        const avatarUrl = comment.avatar_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(comment.username)}&size=48`;
        
        return `
            <div class="comment-item bg-gray-800/50 rounded-lg p-4">
                <div class="flex gap-3">
                    <img src="${avatarUrl}" alt="${comment.username}" class="w-10 h-10 rounded-full">
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
                            <button onclick="socialModule.replyToComment(${comment.id}, '${comment.username}')" 
                                    class="text-gray-500 hover:text-blue-400 transition">
                                ↩️ Responder
                            </button>
                        </div>
                        
                        ${comment.replies && comment.replies.length > 0 ? `
                            <div class="ml-8 mt-2 space-y-2 border-l-2 border-gray-700 pl-4">
                                ${comment.replies.map(reply => this.renderComment(reply, entityKey)).join('')}
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
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
        // TODO: Implementar respuestas a comentarios
        console.log(`Reply to comment ${commentId} by ${username}`);
    }

    /**
     * Publica un nuevo comentario
     */
    async postComment(entityKey, parentId = null) {
        const slug = entityKey.replace(/[^a-z0-9]/gi, '-').toLowerCase();
        const inputEl = document.getElementById(`comment-input-${slug}`);
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

            const data = await response.json();
            if (data.status === 'ok') {
                inputEl.value = '';
                await this.loadComments(entityKey);
            }
        } catch (error) {
            console.error('Error posting comment:', error);
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
                alert('¡Link copiado al portapapeles!');
            } catch (error) {
                console.error('Error copying to clipboard:', error);
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
