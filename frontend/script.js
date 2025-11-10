let currentFile = null;

// Manejar drag and drop
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const processBtn = document.getElementById('processBtn');
const resultsSection = document.getElementById('resultsSection');
const loadingSection = document.getElementById('loadingSection');

// Eventos para drag and drop
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    uploadArea.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
    uploadArea.addEventListener(eventName, () => uploadArea.classList.add('dragover'), false);
});

['dragleave', 'drop'].forEach(eventName => {
    uploadArea.addEventListener(eventName, () => uploadArea.classList.remove('dragover'), false);
});

uploadArea.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

fileInput.addEventListener('change', function() {
    handleFiles(this.files);
});

function handleFiles(files) {
    if (files.length > 0) {
        const file = files[0];
        if (file.name.endsWith('.arff')) {
            currentFile = file;
            fileName.textContent = file.name;
            fileInfo.style.display = 'block';
            processBtn.disabled = false;
        } else {
            alert('Por favor, seleccione un archivo ARFF válido.');
        }
    }
}

async function processDataset() {
    if (!currentFile) {
        alert('Por favor, seleccione un archivo primero.');
        return;
    }

    // Mostrar loading
    loadingSection.style.display = 'block';
    resultsSection.style.display = 'none';
    processBtn.disabled = true;

    const formData = new FormData();
    formData.append('file', currentFile);

    try {
        console.log('Enviando solicitud al servidor...');
        const response = await fetch('https://divisiondataset-webservice.onrender.com/api/process/', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Error en el procesamiento del dataset');
        }

        console.log('Respuesta recibida:', data);
        displayResults(data);

    } catch (error) {
        console.error('Error:', error);
        alert('Error al procesar el dataset: ' + error.message);
    } finally {
        loadingSection.style.display = 'none';
        processBtn.disabled = false;
    }
}

function displayResults(results) {
    try {
        // Mostrar información del dataset
        displayDatasetInfo(results.dataset_info);
        
        // Mostrar tamaños de los conjuntos
        displaySplitSizes(results.split_sizes);
        
        // Mostrar distribución de protocol types
        displayProtocolDistribution(results.protocol_type_distribution);
        
        // Mostrar histogramas
        displayHistograms(results.histograms);
        
        // Mostrar sección de resultados
        resultsSection.style.display = 'block';
        
        // Scroll a los resultados
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('Error mostrando resultados:', error);
        alert('Error mostrando los resultados: ' + error.message);
    }
}

// Las demás funciones display... se mantienen igual
function displayDatasetInfo(info) {
    const container = document.getElementById('datasetInfo');
    
    container.innerHTML = `
        <div class="info-item">
            <strong>Total de instancias:</strong> ${info.total_instances.toLocaleString()}
        </div>
        <div class="info-item">
            <strong>Total de características (columnas):</strong> ${info.features_count.toLocaleString()}
        </div>
        <div class="info-item">
            <strong>Columna usada para estratificar:</strong> ${info.stratify_column_used}
        </div>
    `;
}


function displaySplitSizes(sizes) {
    const container = document.getElementById('splitSizes');
    const total = sizes.train + sizes.validation + sizes.test;
    container.innerHTML = `
        <div class="info-item">
            <strong>Training Set:</strong> ${sizes.train.toLocaleString()} instancias (${((sizes.train/total)*100).toFixed(1)}%)
        </div>
        <div class="info-item">
            <strong>Validation Set:</strong> ${sizes.validation.toLocaleString()} instancias (${((sizes.validation/total)*100).toFixed(1)}%)
        </div>
        <div class="info-item">
            <strong>Test Set:</strong> ${sizes.test.toLocaleString()} instancias (${((sizes.test/total)*100).toFixed(1)}%)
        </div>
        <div class="info-item">
            <strong>Total:</strong> ${total.toLocaleString()} instancias
        </div>
    `;
}

function displayProtocolDistribution(distribution) {
    const container = document.getElementById('protocolDistribution');

    if (!distribution || Object.keys(distribution).length === 0) {
        container.innerHTML = "<p>No se pudo generar la distribución de protocolos.</p>";
        return;
    }

    let html = '';
    const sets = ['original', 'train', 'validation', 'test'];

    sets.forEach(setName => {
        if (distribution[setName]) {
            html += `<h4 style="margin-top: 20px;">${getSetDisplayName(setName)}</h4>`;
            html += createDistributionTable(distribution[setName]);
        }
    });

    container.innerHTML = html;
}

function createDistributionTable(setData) {
    if (!setData || typeof setData !== 'object') {
        console.warn("Distribución vacía o inválida:", setData);
        return "<p>Sin datos disponibles.</p>";
    }

    const protocols = Object.keys(setData);
    const rows = protocols.map(protocol => `
        <tr>
            <td>${protocol}</td>
            <td>${setData[protocol].toLocaleString()}</td>
        </tr>
    `).join('');

    return `
        <table class="distribution-table">
            <thead>
                <tr>
                    <th>Protocolo</th>
                    <th>Frecuencia</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    `;
}


function displayHistograms(histograms) {
    const container = document.getElementById('histograms');
    container.innerHTML = '';
    
    for (const [setName, base64Image] of Object.entries(histograms)) {
        const div = document.createElement('div');
        div.className = 'histogram-item';
        div.innerHTML = `
            <h4>${getSetDisplayName(setName)}</h4>
            <img src="data:image/png;base64,${base64Image}" alt="Histograma de ${setName}">
        `;
        container.appendChild(div);
    }
}

function getSetDisplayName(setName) {
    const names = {
        'original': 'Dataset Original',
        'train': 'Training Set',
        'validation': 'Validation Set',
        'test': 'Test Set'
    };
    return names[setName] || setName;
}