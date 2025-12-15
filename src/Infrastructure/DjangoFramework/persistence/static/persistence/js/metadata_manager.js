/**
 * METADATA MANAGER V2 (Clean Rewrite)
 * Handles the dynamic list of metadata properties for the editing modal.
 */

let META_PROPS = []; // Source of Truth
let CURRENT_JID = ""; // Global JID

// 1. Initialization
function initMetadataManager(initialData, jid) {
    // Ensure we have an array
    META_PROPS = Array.isArray(initialData) ? initialData : [];
    CURRENT_JID = jid;
    console.log("✅ Metadata Manager Initialized for", jid, "with", META_PROPS.length, "items.");
    renderMetadataRows();
}

// 2. Open/Close Modal Helper
function openMetadataModal() {
    const modal = document.getElementById('metadataModal');
    if(modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}

function closeMetadataModal() {
    const modal = document.getElementById('metadataModal');
    if(modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

// 3. Render Logic (State -> DOM)
function renderMetadataRows() {
    const container = document.getElementById('metadata-rows-container');
    const emptyMsg = document.getElementById('empty-msg');
    
    if (!container) return;
    
    // Clear current DOM
    container.innerHTML = '';
    
    // Toggle Empty State
    if (META_PROPS.length === 0) {
        if(emptyMsg) emptyMsg.classList.remove('hidden');
        return;
    } else {
        if(emptyMsg) emptyMsg.classList.add('hidden');
    }

    // Generate Rows
    META_PROPS.forEach((prop, index) => {
        const row = document.createElement('div');
        row.className = "flex gap-2 items-center bg-black/20 p-2 rounded border border-gray-800 hover:border-purple-500/30 transition group";
        
        row.innerHTML = `
            <!-- KEY INPUT -->
            <div class="w-1/3 relative">
                <input type="text" 
                       name="prop_keys[]" 
                       value="${escapeHtml(prop.key)}" 
                       oninput="syncProp(${index}, 'key', this.value)"
                       class="w-full bg-black/40 text-purple-400 font-mono text-xs border border-gray-700 rounded focus:border-purple-500 outline-none px-2 py-1"
                       placeholder="Nombre" required>
            </div>
            
            <span class="text-gray-600">:</span>
            
            <!-- VALUE INPUT -->
            <div class="flex-1 relative">
                <input type="text" 
                       name="prop_values[]" 
                       value="${escapeHtml(prop.value)}" 
                       oninput="syncProp(${index}, 'value', this.value)"
                       class="w-full bg-black/40 text-gray-200 text-sm border border-gray-700 rounded focus:border-green-500 outline-none px-2 py-1"
                       placeholder="Valor" required>
            </div>

            <!-- DELETE BUTTON -->
            <button type="button" onclick="deleteMetadataRow(${index})" 
                    class="ml-2 w-7 h-7 flex items-center justify-center bg-red-900/10 text-red-600 border border-transparent hover:border-red-500 hover:bg-red-900/30 rounded transition group-hover:opacity-100"
                    title="Eliminar fila">
                &times;
            </button>
        `;
        container.appendChild(row);
    });
}

// 4. State Management (DOM -> State)
function syncProp(index, field, value) {
    if (META_PROPS[index]) {
        META_PROPS[index][field] = value;
    }
}

function addMetadataRow() {
    META_PROPS.push({ key: "", value: "" });
    renderMetadataRows();
    // Focus last element
    setTimeout(() => {
        const inputs = document.querySelectorAll('input[name="prop_keys[]"]');
        if(inputs.length) inputs[inputs.length - 1].focus();
    }, 50);
}

function deleteMetadataRow(index) {
    META_PROPS.splice(index, 1);
    renderMetadataRows();
}

// 5. Utility
function escapeHtml(text) {
    if (!text) return "";
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// 6. AUTO-NOOS LOGIC
async function runAutoNoos(jid) {
    const targetJid = jid || CURRENT_JID;
    const btn = document.querySelector('button[onclick^="runAutoNoos"]');
    const txt = document.getElementById('noos-text');
    const icon = document.getElementById('noos-icon');
    
    // Loading State
    const originalText = txt ? txt.innerText : "AUTO-NOOS";
    if(txt) txt.innerText = "ESCANEYENDO...";
    if(icon) icon.innerHTML = "⏳";
    if(btn) btn.disabled = true;

    try {
        console.log("🧠 Run AutoNode for:", targetJid);
        const res = await fetch(`/api/auto_noos/${targetJid}/`);
        
        if (!res.ok) throw new Error(`Server Error ${res.status}`);
        
        const data = await res.json();
        
        if (data.status === 'success') {
            const newDefaults = data.properties || [];
            let added = 0;
            
            newDefaults.forEach(item => {
                // Only add if key doesn't exist (to preserve current edits)
                // OR simply overwrite? Let's OVERWRITE empty values, maintain filled?
                // Logic: If key exists, update value. If not, add.
                
                const existing = META_PROPS.find(p => p.key === item.key);
                if (existing) {
                    existing.value = item.value;
                } else {
                    META_PROPS.push({ key: item.key, value: item.value });
                    added++;
                }
            });
            
            renderMetadataRows();
            alert(`✅ Auto-Noos Completado.\nSe actualizaron/añadieron variables.`);
        } else {
            alert(`⚠️ Error IA: ${data.message}`);
        }

    } catch (e) {
        console.error(e);
        alert("❌ Error de comunicación con el servidor.");
    } finally {
        // Reset UI
        txt.innerText = originalText;
        icon.innerHTML = "🧠";
        btn.disabled = false;
    }
}
