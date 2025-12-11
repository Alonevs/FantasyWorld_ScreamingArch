/**
 * Metadata Manager Logic
 * Handles HUD Modal and Auto-Noos.
 */

let _currentWorldId = null;

function initMetadata(savedProps, worldId) {
    if (savedProps && savedProps.length > 0) {
        document.getElementById('empty-state').classList.add('hidden');
        savedProps.forEach(p => renderRow(p.key, p.value));
    }
    _currentWorldId = worldId;
}

function openMetadataModal() {
    const m = document.getElementById('metadataModal');
    m.classList.remove('hidden');
    m.classList.add('flex');
}

function closeMetadataModal() {
    const m = document.getElementById('metadataModal');
    m.classList.add('hidden');
    m.classList.remove('flex');
}

// VISUAL HELPER: Humanizer
function formatLabel(key) {
    if (!key) return '';
    // 1. Quitar guiones bajos
    let text = key.replace(/_/g, ' ');
    // 2. Title Case (lowercase base first deals with ALLCAPS)
    return text.toLowerCase().replace(/\b\w/g, char => char.toUpperCase());
}

function renderRow(key, value) {
    // FILTER: Ignore massive text (hallucinations or descriptions) to keep UI clean
    if (value && value.length > 50) {
        console.warn(`Auto-Noos: Skipped long value for key '${key}' (${value.length} chars).`);
        return;
    }

    document.getElementById('empty-state').classList.add('hidden');
    
    const container = document.getElementById('dynamic-rows');
    const row = document.createElement('div');
    row.className = "flex items-center gap-2 group bg-black/40 p-2 rounded border border-gray-800 hover:border-purple-500 transition-colors animate-in fade-in slide-in-from-bottom-2 duration-200";
    
    // Removed 'uppercase' class to respect formatLabel
    row.innerHTML = `
        <div class="w-1/3 flex items-center">
            <span class="w-full bg-transparent text-purple-400 text-xs font-bold font-mono tracking-wider truncate" title="${key}">
                ${formatLabel(key)}
            </span>
            <input type="hidden" name="prop_keys[]" value="${key}">
        </div>
        <div class="w-2/3 border-l border-gray-700 pl-3 flex justify-between items-center">
            <input type="text" name="prop_values[]" value="${value}" class="w-full bg-transparent text-gray-200 text-sm focus:outline-none placeholder-gray-600" placeholder="Valor asignado...">
            <button type="button" onclick="this.closest('.flex').remove(); checkEmpty();" class="text-gray-600 hover:text-red-500 transition px-2 opacity-0 group-hover:opacity-100">×</button>
        </div>
    `;
    container.appendChild(row);
}

// ... checkEmpty() stays same ...

async function requestAIAnalysis() {
    const loader = document.getElementById('aiLoading');
    const container = document.getElementById('dynamic-rows');
    const emptyMsg = document.getElementById('empty-state');
    
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
        }

    } catch (e) {
        console.error(e);
        alert("Error conectando con el Núcleo NOOS.");
    } finally {
        loader.classList.add('hidden');
    }
}
