/**
 * Metadata Manager Logic
 * Handles HUD Modal and Auto-Noos.
 */

let _currentWorldId = null;

function initMetadataManager(savedProps, worldId) {
    if (savedProps && savedProps.length > 0) {
        const emptyMsg = document.getElementById('empty-msg');
        if(emptyMsg) emptyMsg.classList.add('hidden');
        savedProps.forEach(p => renderRow(p.key, p.value));
    }
    _currentWorldId = worldId;
}

function openMetadataModal(targetType = 'WORLD', targetId = null) {
    const m = document.getElementById('metadataModal');
    m.classList.remove('hidden');
    m.classList.add('flex');
    
    // Set target info
    document.getElementById('metadata-target-type').value = targetType;
    if (targetId) {
        document.getElementById('metadata-target-id').value = targetId;
    }
}

async function submitMetadataProposal() {
    const btn = document.getElementById('btn-save-metadata');
    const type = document.getElementById('metadata-target-type').value;
    const id = document.getElementById('metadata-target-id').value;
    const changeLog = document.getElementById('metadata-change-log').value;
    
    // Collect metadata
    const keys = document.getElementsByName('prop_keys[]');
    const vals = document.getElementsByName('prop_values[]');
    let metadata = {};
    for (let i = 0; i < keys.length; i++) {
        if (keys[i].value.trim()) {
            metadata[keys[i].value.trim()] = vals[i].value.trim();
        }
    }
    
    if (Object.keys(metadata).length === 0) {
        await CaosModal.alert("Error", "No has definido ninguna variable de metadatos.");
        return;
    }
    
    btn.disabled = true;
    btn.innerText = "Enviando...";
    
    try {
        const response = await fetch(`/api/metadata/propose/${type}/${id}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                metadata: metadata,
                change_log: changeLog || "Actualización de metadatos independiente"
            })
        });
        
        const data = await response.json();
        if (data.success) {
            await CaosModal.alert("Propuesta Enviada", "✅ Tu propuesta de metadatos ha sido enviada para revisión.");
            closeMetadataModal();
            location.reload();
        } else {
            await CaosModal.alert("Error", data.error || "Ocurrió un error al enviar la propuesta.");
        }
    } catch (e) {
        console.error(e);
        await CaosModal.alert("Error de Conexión", "No se pudo contactar con el servidor.");
    } finally {
        btn.disabled = false;
        btn.innerText = "GUARDAR PROPUESTA";
    }
}

function closeMetadataModal() {
    const m = document.getElementById('metadataModal');
    m.classList.add('hidden');
    m.classList.remove('flex');
}

// VISUAL HELPER: Humanizer
function formatLabel(key) {
    if (!key) return '';
    let text = key.replace(/_/g, ' ');
    return text.toLowerCase().replace(/\b\w/g, char => char.toUpperCase());
}

function renderRow(key, value, isEditableKey = false) {
    // FILTER: Ignore massive text (hallucinations or descriptions) to keep UI clean
    if (value && typeof value === 'string' && value.length > 200) {
        console.warn(`Auto-Noos: Skipped long value for key '${key}' (${value.length} chars).`);
        return;
    }

    // Handle Objects/Arrays (e.g. timeline lists)
    let displayValue = value;
    if (typeof value === 'object' && value !== null) {
        displayValue = JSON.stringify(value);
    } else if (value === null || value === undefined) {
        displayValue = "";
    }

    const emptyMsg = document.getElementById('empty-msg');
    if(emptyMsg) emptyMsg.classList.add('hidden');
    
    const container = document.getElementById('metadata-rows-container');
    const row = document.createElement('div');
    row.className = "flex items-center gap-2 group bg-black/40 p-2 rounded border border-gray-800 hover:border-purple-500 transition-colors animate-in fade-in slide-in-from-bottom-2 duration-200";
    
    // Condition handling for Key Field
    let keyFieldHtml = '';
    if (isEditableKey) {
        keyFieldHtml = `
            <input type="text" name="prop_keys[]" value="${key}" 
                   class="w-full bg-black/50 border border-gray-700 text-purple-400 text-xs font-bold font-mono tracking-wider p-1 rounded focus:border-purple-500 focus:outline-none placeholder-purple-900/50" 
                   placeholder="NOMBRE_VARIABLE">
        `;
    } else {
        keyFieldHtml = `
            <span class="w-full bg-transparent text-purple-400 text-xs font-bold font-mono tracking-wider truncate cursor-help" title="${key}">
                ${formatLabel(key)}
            </span>
            <input type="hidden" name="prop_keys[]" value="${key}">
        `;
    }

    row.innerHTML = `
        <div class="w-1/3 flex items-center">
            ${keyFieldHtml}
        </div>
        <div class="w-2/3 border-l border-gray-700 pl-3 flex justify-between items-center bg-black/20 rounded-r">
            <input type="text" name="prop_values[]" value="${displayValue.replace(/"/g, '&quot;')}" class="w-full bg-transparent text-gray-200 text-sm focus:outline-none placeholder-gray-600 px-2" placeholder="Valor asignado...">
            <button type="button" onclick="this.closest('.group').remove(); checkEmpty();" class="text-gray-600 hover:text-red-500 transition px-2 opacity-0 group-hover:opacity-100 font-bold" title="Eliminar Fila">×</button>
        </div>
    `;
    container.appendChild(row);
}

function checkEmpty() {
    const container = document.getElementById('metadata-rows-container');
    const emptyMsg = document.getElementById('empty-msg');
    // Check if there are any flex rows (actual data rows)
    const hasRows = container.querySelectorAll('.flex').length > 0;
    
    if (!hasRows) {
        emptyMsg.classList.remove('hidden');
    }
}

async function addMetadataRow() {
    // Direct edit mode: Create empty row with editable key
    renderRow("", "", true);
}

async function runAutoNoos() {
    await requestAIAnalysis();
}

async function requestAIAnalysis() {
    const loader = document.getElementById('aiLoading');
    const container = document.getElementById('metadata-rows-container');
    const emptyMsg = document.getElementById('empty-msg');
    
    loader.classList.remove('hidden');
    
    try {
        const response = await fetch('/api/ai/analyze-metadata/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({ world_id: _currentWorldId })
        });

        const data = await response.json();
        
        if (data.success && data.metadata) {
            
            // SYSTEM LOG TRACE (User Feedback)
            if(data.metadata.analysis_trace && data.metadata.analysis_trace.length > 0) {
                const traceMsg = data.metadata.analysis_trace.join('\n');
                CaosModal.alert("Análisis Completado", `Sistema Auto-Noos:\n${traceMsg}`);
            }

            container.innerHTML = ''; 
            container.appendChild(emptyMsg);
            emptyMsg.classList.add('hidden');
            
            // V2 ADAPTER: Handle Nucleo & Extended
            if (data.metadata.datos_nucleo) {
                Object.entries(data.metadata.datos_nucleo).forEach(([k, v]) => renderRow(k, v));
            }
            if (data.metadata.datos_extendidos) {
                Object.entries(data.metadata.datos_extendidos).forEach(([k, v]) => renderRow(k, v));
            }
            
            // Legacy Fallback
            if (data.metadata.properties) {
                data.metadata.properties.forEach(item => {
                    renderRow(item.key, item.value);
                });
            }
        } else {
            console.log("Auto-Noos: No variables found or partial data.");
            const errorMsg = data.error || "No se pudieron extraer datos relevantes.";
            CaosModal.alert("Aviso AI", errorMsg);
        }

    } catch (e) {
        console.error(e);
        await CaosModal.alert("Error de Conexión", "Error conectando con el Núcleo NOOS.");
    } finally {
        loader.classList.add('hidden');
    }
}

// Ensure global accessibility
window.initMetadataManager = initMetadataManager;
window.openMetadataModal = openMetadataModal;
window.closeMetadataModal = closeMetadataModal;
window.submitMetadataProposal = submitMetadataProposal;
window.addMetadataRow = addMetadataRow;
window.runAutoNoos = runAutoNoos;
window.checkEmpty = checkEmpty;
