/**
 * Narrative Editor Logic
 * Handles File Import, AI Editing, and Title Generation.
 */

function toggleEdit() {
    const el = document.getElementById('editor');
    el.style.display = (el.style.display === 'block') ? 'none' : 'block';
}

function initEditor(isCreationMode, editParam) {
    // Auto-open if ?edit=true or Creation Mode
    if(editParam === 'true') {
        toggleEdit();
    }
    if (isCreationMode) {
        // Ensure it's open if not already (logic handled by toggleEdit call in template usually, but safe here)
        const el = document.getElementById('editor');
        if (el.style.display !== 'block') toggleEdit();
    }

    // Init Word Count
    setTimeout(() => {
        const ta = document.querySelector('textarea[name="content"]') || document.querySelector('textarea[name="contenido"]');
        if(ta) updateWordCount(ta);
    }, 500);
}

async function uploadNarrativeFile(input) {
    if (input.files && input.files[0]) {
        const file = input.files[0];
        const status = document.getElementById('upload-status');
        // Select textarea safely (creation vs edit mode names)
        const textarea = document.querySelector('textarea[name="content"]') || document.querySelector('textarea[name="contenido"]');

        if (!textarea) return;

        status.innerText = "⏳ Extrayendo...";
        status.style.color = "#aaa";
        
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/narrative/import-file/', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                const currentVal = textarea.value;
                // Avoid double newlines if empty
                textarea.value = currentVal ? currentVal + "\n\n" + data.text : data.text;
                status.innerText = "✅ Texto importado";
                status.style.color = "#2ecc71";
                updateWordCount(textarea); // Update count
            } else {
                status.innerText = "⚠️ " + data.error;
                status.style.color = "#e74c3c";
            }
        } catch (error) {
            console.error('Error:', error);
            status.innerText = "❌ Error de red";
            status.style.color = "#e74c3c";
        }
        
        // Clear input to allow re-uploading same file
        input.value = '';
        setTimeout(() => { if(status) status.innerText = ''; }, 4000);
    }
}

// Word Count Logic
function updateWordCount(textarea) {
    const count = textarea.value.trim().split(/\s+/).filter(w => w.length > 0).length;
    const el = document.getElementById('word-count');
    if(el) {
        el.innerText = count + " palabras";
        if(count > 4000) el.style.color = "#e74c3c"; // Red warn
        else el.style.color = "#666";
    }
}

// AI Edit Logic
async function requestAIEdit(mode) {
     const textarea = document.querySelector('textarea[name="content"]') || document.querySelector('textarea[name="contenido"]');
     if(!textarea || !textarea.value.trim()) return alert("El texto está vacío.");
     
     const status = document.getElementById('ai-status');
     const originalText = textarea.value;
     
     if(!confirm("⚠️ Esto reemplazará el contenido actual con la versión de la IA.\n¿Continuar?")) return;

     status.innerText = "🤖 La IA está escribiendo...";
     textarea.disabled = true;
     textarea.style.opacity = "0.5";

     try {
         // Extract world_id for context
         const paperDiv = document.querySelector('.paper');
         const worldId = paperDiv ? paperDiv.getAttribute('data-world-id') : null;
         
         const response = await fetch('/api/ai/edit-narrative/', {
             method: 'POST',
             headers: {
                 'Content-Type': 'application/json',
                 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
             },
             body: JSON.stringify({ 
                 text: originalText, 
                 mode: mode,
                 world_id: worldId  // NUEVO: Para herencia de lore
             })
         });
        
        const data = await response.json();
        
        if (data.success) {
            textarea.value = data.text;
            updateWordCount(textarea);
            status.innerText = "✨ ¡Hecho!";
            setTimeout(() => status.innerText = "", 3000);
        } else {
            alert("Error IA: " + data.error);
            status.innerText = "❌ Error";
        }
     } catch (e) {
        alert("Error de conexión: " + e);
        status.innerText = "❌ Error Red";
     } finally {
        textarea.disabled = false;
        textarea.style.opacity = "1";
     }
}

// AI Title Generator Logic
async function generateTitle() {
    const textarea = document.querySelector('textarea[name="content"]') || document.querySelector('textarea[name="contenido"]');
    // FIX: Selector must handle both 'title' (creation) and 'titulo' (edit)
    const titleInput = document.querySelector('input[name="titulo"]') || document.querySelector('input[name="title"]');
    
    if(!titleInput) {
        return alert("❌ Error interno: No encuentro el campo de título.");
    }
    
    if(!textarea || !textarea.value.trim() || textarea.value.length < 50) {
        return alert("⚠️ Escribe al menos 50 caracteres en el contenido para generar un título.");
    }

    const originalTitle = titleInput.value;
    titleInput.value = "🔮 Consultando a los Oráculos...";
    titleInput.disabled = true;
    
    const worldIdAttr = document.querySelector('[data-world-id]');
    const worldId = worldIdAttr ? worldIdAttr.getAttribute('data-world-id') : null;
    
    try {
        const response = await fetch('/api/ai/generate-title/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                text: textarea.value,
                world_id: worldId  // NUEVO: Para contexto jerárquico
            })
        });

        const data = await response.json();

        if (data.success) {
            titleInput.value = data.title;
            // Flash effect
            titleInput.style.borderColor = "#d633ff";
            titleInput.style.boxShadow = "0 0 15px #d633ff";
            setTimeout(() => {
                titleInput.style.borderColor = "#444";
                titleInput.style.boxShadow = "none";
            }, 1000);
        } else {
            alert("Error IA: " + data.error);
            titleInput.value = originalTitle; // Revert
        }

    } catch (e) {
        alert("Error de conexión: " + e);
        titleInput.value = originalTitle;
    } finally {
        titleInput.disabled = false;
    }
}
