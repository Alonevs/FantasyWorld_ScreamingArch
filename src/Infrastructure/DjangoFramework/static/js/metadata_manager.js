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

function renderRow(key, value) {
    document.getElementById('empty-state').classList.add('hidden');
    
    const container = document.getElementById('dynamic-rows');
    const row = document.createElement('div');
    row.className = "flex items-center gap-2 group bg-black/40 p-2 rounded border border-gray-800 hover:border-purple-500 transition-colors animate-in fade-in slide-in-from-bottom-2 duration-200";
    row.innerHTML = `
        <div class="w-1/3">
            <input type="text" name="prop_keys[]" value="${key}" class="w-full bg-transparent text-purple-400 text-xs uppercase font-bold focus:outline-none placeholder-gray-700 font-mono tracking-wider" placeholder="CLAVE">
        </div>
        <div class="w-2/3 border-l border-gray-700 pl-3 flex justify-between items-center">
            <input type="text" name="prop_values[]" value="${value}" class="w-full bg-transparent text-gray-200 text-sm focus:outline-none placeholder-gray-600" placeholder="Valor asignado...">
            <button type="button" onclick="this.closest('.flex').remove(); checkEmpty();" class="text-gray-600 hover:text-red-500 transition px-2 opacity-0 group-hover:opacity-100">×</button>
        </div>
    `;
    container.appendChild(row);
}

function checkEmpty() {
    if (document.getElementById('dynamic-rows').children.length <= 1) { 
         const visibleRows = document.querySelectorAll('#dynamic-rows > div:not(#empty-state)').length;
         if (visibleRows === 0) document.getElementById('empty-state').classList.remove('hidden');
    }
}

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
        
        if (data.success && data.metadata && data.metadata.properties) {
            container.innerHTML = ''; 
            container.appendChild(emptyMsg);
            emptyMsg.classList.add('hidden');
            
            data.metadata.properties.forEach(item => {
                renderRow(item.key, item.value);
            });
        } else {
            alert("⚠️ " + (data.error || "La IA no encontró variables claras."));
        }

    } catch (e) {
        console.error(e);
        alert("Error conectando con el Núcleo NOOS.");
    } finally {
        loader.classList.add('hidden');
    }
}
