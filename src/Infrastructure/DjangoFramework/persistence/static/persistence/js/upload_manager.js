/**
 * ECLAI v4.8 - Gestor de Subidas y Seguridad
 * Maneja la previsualización, lectura EXIF y filtro NSFW.
 */

let selectedFile = null;
let nsfwModel = null;

// Carga asíncrona del modelo de seguridad
document.addEventListener('DOMContentLoaded', () => {
    try {
        if (typeof nsfwjs !== 'undefined') {
            nsfwjs.load().then(model => {
                nsfwModel = model;
                console.log("🛡️ [ECLAI Security] Modelo NSFW cargado.");
            }).catch(err => console.warn("⚠️ [ECLAI Security] Fallo al cargar NSFWJS:", err));
        }
    } catch (e) {
        console.warn("⚠️ Librerías de seguridad no detectadas.");
    }
});

// Abre el modal al seleccionar archivo
function openUploadModal(input) {
    if (input.files && input.files[0]) {
        selectedFile = input.files[0];
        
        // Elementos DOM
        const modal = document.getElementById('uploadModal');
        const imgPreview = document.getElementById('preview-img');
        const statusDiv = document.getElementById('scan-status');
        const btnConfirm = document.getElementById('btn-confirm-upload');
        const fileInfo = document.getElementById('file-info');

        if (!modal) return; // Seguridad

        // Reset UI
        modal.style.display = 'flex';
        imgPreview.style.display = 'none';
        btnConfirm.style.display = 'none';
        statusDiv.innerHTML = '⏳ INICIANDO PROTOCOLO...';
        statusDiv.style.color = '#aaa';

        // Leer archivo
        const reader = new FileReader();
        reader.onload = function(e) {
            imgPreview.src = e.target.result;
            imgPreview.style.display = 'block';
            
            let size = (selectedFile.size / 1024).toFixed(2) + " KB";
            fileInfo.innerText = selectedFile.name + " (" + size + ")";
            
            // Iniciar escaneo
            performSecurityScan(imgPreview, statusDiv, btnConfirm);
        };
        reader.readAsDataURL(selectedFile);
    }
}

// Lógica de Escaneo (Copyright + NSFW)
async function performSecurityScan(imgElement, statusDiv, btnConfirm) {
    statusDiv.innerHTML = '🔍 ESCANEANDO METADATOS...';
    statusDiv.style.color = '#f1c40f';

    // Timeout de seguridad (si la IA se cuelga, deja pasar a los 3s)
    let checkFinished = false;
    const safetyTimer = setTimeout(() => {
        if (!checkFinished) {
            console.warn("⚠️ Timeout de seguridad.");
            allowUpload(statusDiv, btnConfirm, "⚠️ VERIFICACIÓN MANUAL REQUERIDA");
        }
    }, 3000);

    try {
        // 1. Check EXIF (Copyright)
        if (typeof EXIF !== 'undefined') {
            await new Promise(resolve => {
                EXIF.getData(selectedFile, function() {
                    const all = JSON.stringify(EXIF.getAllTags(this)).toLowerCase();
                    if (all.includes('copyright') || all.includes('getty') || all.includes('rights reserved')) {
                        throw "⛔ COPYRIGHT DETECTADO";
                    }
                    resolve();
                });
            });
        }

        // 2. Check NSFW (IA)
        if (nsfwModel) {
            statusDiv.innerHTML = '🤖 ANALIZANDO CONTENIDO...';
            const predictions = await nsfwModel.classify(imgElement);
            const porn = predictions.find(p => p.className === 'Porn');
            const hentai = predictions.find(p => p.className === 'Hentai');
            
            if ((porn && porn.probability > 0.6) || (hentai && hentai.probability > 0.6)) {
                throw "⛔ CONTENIDO INAPROPIADO (NSFW)";
            }
        }

        checkFinished = true;
        clearTimeout(safetyTimer);
        allowUpload(statusDiv, btnConfirm, "✅ ARCHIVO SEGURO");

    } catch (reason) {
        checkFinished = true;
        clearTimeout(safetyTimer);
        blockUpload(statusDiv, reason);
    }
}

function allowUpload(statusDiv, btn, msg) {
    statusDiv.innerHTML = msg;
    statusDiv.style.color = msg.includes('⚠️') ? '#f1c40f' : '#2ecc71';
    btn.style.display = 'inline-block';
}

function blockUpload(statusDiv, msg) {
    statusDiv.innerHTML = msg;
    statusDiv.style.color = '#e74c3c';
    console.error("Upload bloqueado:", msg);
}

function closeUploadModal() {
    document.getElementById('uploadModal').style.display = 'none';
    document.getElementById('file-upload').value = "";
}

function confirmUpload() {
    const form = document.getElementById('form-manual-upload');
    if (form) form.submit();
}

// Función de Galería (Metadatos visuales)
function loadGalleryMetadata(imgElement) {
    if (imgElement.naturalWidth) {
        const wrapper = imgElement.parentElement;
        const res = wrapper.querySelector('.res');
        if (res) res.innerText = imgElement.naturalWidth + 'x' + imgElement.naturalHeight + 'px';
        
        try {
            EXIF.getData(imgElement, function() {
                const artist = EXIF.getTag(this, "Artist");
                const copy = EXIF.getTag(this, "Copyright");
                const fmt = wrapper.querySelector('.fmt');
                if (fmt && (artist || copy)) {
                    fmt.innerText = "© DATA";
                    fmt.style.color = "#f1c40f";
                }
            });
        } catch(e){}
    }
}
