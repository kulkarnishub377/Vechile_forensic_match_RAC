/**
 * 🚗 Vehicle Re-Identification System - Frontend
 * Clean, no-database image matching interface
 */

// ═══════════════════════════════════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════════════════════════════════

const STATE = {
    sessionId: null,
    uploadedFiles: [],
    searchFile: null,
    imageCount: 0,
    apiBase: '/api'
};

// ═══════════════════════════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    // Generate session ID
    STATE.sessionId = generateUUID();
    document.getElementById('sessionId').textContent = STATE.sessionId.substring(0, 8) + '...';

    // Setup event listeners
    setupFileUploadEvents();
    setupSearchEvents();
    setupThresholdControl();

    updateStatus('Session initialized', 'success');
}

// ═══════════════════════════════════════════════════════════════════════
// FILE UPLOAD EVENTS
// ═══════════════════════════════════════════════════════════════════════

function setupFileUploadEvents() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');

    uploadZone.addEventListener('click', () => fileInput.click());
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        STATE.uploadedFiles = Array.from(e.dataTransfer.files);
        updateStatus(`${STATE.uploadedFiles.length} files selected for upload`);
    });

    fileInput.addEventListener('change', (e) => {
        STATE.uploadedFiles = Array.from(e.target.files);
        updateStatus(`${STATE.uploadedFiles.length} files selected`);
    });
}

// ═══════════════════════════════════════════════════════════════════════
// SEARCH EVENTS
// ═══════════════════════════════════════════════════════════════════════

function setupSearchEvents() {
    const searchZone = document.getElementById('searchZone');
    const searchInput = document.getElementById('searchInput');

    searchZone.addEventListener('click', () => searchInput.click());
    searchZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        searchZone.classList.add('dragover');
    });
    searchZone.addEventListener('dragleave', () => {
        searchZone.classList.remove('dragover');
    });
    searchZone.addEventListener('drop', (e) => {
        e.preventDefault();
        searchZone.classList.remove('dragover');
        STATE.searchFile = e.dataTransfer.files[0];
        updateStatus(`Search image: ${STATE.searchFile.name}`);
    });

    searchInput.addEventListener('change', (e) => {
        STATE.searchFile = e.target.files[0];
        updateStatus(`Search image: ${STATE.searchFile.name}`);
    });
}

// ═══════════════════════════════════════════════════════════════════════
// THRESHOLD CONTROL
// ═══════════════════════════════════════════════════════════════════════

function setupThresholdControl() {
    const slider = document.getElementById('threshold');
    slider.addEventListener('input', (e) => {
        const value = parseInt(e.target.value) / 100;
        document.getElementById('thresholdValue').textContent = value.toFixed(2);
    });
}

// ═══════════════════════════════════════════════════════════════════════
// FILE SELECTION
// ═══════════════════════════════════════════════════════════════════════

function chooseFiles() {
    document.getElementById('fileInput').click();
}

function chooseSearchFile() {
    document.getElementById('searchInput').click();
}

// ═══════════════════════════════════════════════════════════════════════
// UPLOAD FILES
// ═══════════════════════════════════════════════════════════════════════

async function uploadFiles() {
    if (STATE.uploadedFiles.length === 0) {
        updateStatus('No files selected', 'error');
        return;
    }

    updateStatus(`Uploading ${STATE.uploadedFiles.length} images...`, 'loading');

    try {
        for (let i = 0; i < STATE.uploadedFiles.length; i++) {
            const file = STATE.uploadedFiles[i];
            const formData = new FormData();
            formData.append('file', file);
            formData.append('session_id', STATE.sessionId);

            const response = await fetch(`${STATE.apiBase}/upload?session_id=${STATE.sessionId}`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Upload failed for ${file.name}`);
            }

            const data = await response.json();
            console.log(`✓ Uploaded: ${file.name}`, data);
        }

        updateStatus(`✓ ${STATE.uploadedFiles.length} images uploaded successfully`, 'success');
        STATE.uploadedFiles = [];
        document.getElementById('fileInput').value = '';
        refreshGallery();
    } catch (error) {
        updateStatus(`Error: ${error.message}`, 'error');
    }
}

// ═══════════════════════════════════════════════════════════════════════
// REFRESH GALLERY
// ═══════════════════════════════════════════════════════════════════════

async function refreshGallery() {
    try {
        const response = await fetch(`${STATE.apiBase}/results/${STATE.sessionId}`);
        if (!response.ok) throw new Error('Failed to fetch results');

        const data = await response.json();
        const gallery = document.getElementById('gallery');
        const imageCount = document.getElementById('imageCount');

        STATE.imageCount = data.total_images;
        imageCount.textContent = STATE.imageCount;

        if (data.total_images === 0) {
            gallery.innerHTML = '<p class="empty-state">No images uploaded yet</p>';
            return;
        }

        gallery.innerHTML = data.images.map((img) => `
            <div class="gallery-item">
                <div style="width: 100%; height: 100%; background: #e5e7eb; display: flex; align-items: center; justify-content: center; font-size: 2rem;">
                    🖼️
                </div>
                <div class="gallery-item-status">
                    ${img.embedding_ready ? '✓ Ready' : '⏳ Processing'}
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Gallery error:', error);
    }
}

// ═══════════════════════════════════════════════════════════════════════
// SEARCH VEHICLE
// ═══════════════════════════════════════════════════════════════════════

async function searchVehicle() {
    if (!STATE.searchFile) {
        updateStatus('No search image selected', 'error');
        return;
    }

    if (STATE.imageCount === 0) {
        updateStatus('No images in session to search against', 'error');
        return;
    }

    updateStatus('Searching... <span class="spinner"></span>', 'loading');

    try {
        const formData = new FormData();
        formData.append('file', STATE.searchFile);
        formData.append('session_id', STATE.sessionId);

        const threshold = parseInt(document.getElementById('threshold').value) / 100;

        const response = await fetch(
            `${STATE.apiBase}/search?session_id=${STATE.sessionId}&threshold=${threshold}`,
            {
                method: 'POST',
                body: formData
            }
        );

        if (!response.ok) throw new Error('Search failed');

        const data = await response.json();
        console.log('Search results:', data);

        displayResults(data);

        if (data.total_matches > 0) {
            updateStatus(
                `✓ Found ${data.total_matches} matches in ${data.search_time_ms.toFixed(0)}ms`,
                'success'
            );
        } else {
            updateStatus('No matches found', 'error');
        }
    } catch (error) {
        updateStatus(`Error: ${error.message}`, 'error');
    }
}

// ═══════════════════════════════════════════════════════════════════════
// DISPLAY RESULTS
// ═══════════════════════════════════════════════════════════════════════

function displayResults(data) {
    const resultsSection = document.getElementById('resultsSection');
    const resultsList = document.getElementById('results');

    if (data.total_matches === 0) {
        resultsList.innerHTML = '<p>No matches found above threshold</p>';
        resultsSection.style.display = 'block';
        return;
    }

    const medals = ['🥇', '🥈', '🥉'];
    resultsList.innerHTML = data.matches.map((match, idx) => `
        <div class="result-item ${match.match_type}">
            <div class="result-image" style="background: #e5e7eb; display: flex; align-items: center; justify-content: center; font-size: 2rem;">
                🖼️
            </div>
            <div class="result-info">
                <div class="result-filename">
                    ${medals[idx] || '•'} ${match.filename}
                </div>
                <div class="result-score">${(match.match_score * 100).toFixed(1)}%</div>
                <div class="result-type">${match.match_type.toUpperCase()} MATCH</div>
            </div>
        </div>
    `).join('');

    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// ═══════════════════════════════════════════════════════════════════════
// CLEAR SESSION
// ═══════════════════════════════════════════════════════════════════════

async function clearSession() {
    if (!confirm('Clear all images from this session?')) return;

    try {
        await fetch(`${STATE.apiBase}/clear/${STATE.sessionId}`, { method: 'POST' });

        STATE.uploadedFiles = [];
        STATE.searchFile = null;
        STATE.imageCount = 0;
        document.getElementById('fileInput').value = '';
        document.getElementById('searchInput').value = '';
        document.getElementById('gallery').innerHTML = '<p class="empty-state">No images uploaded yet</p>';
        document.getElementById('imageCount').textContent = '0';
        document.getElementById('resultsSection').style.display = 'none';
        updateStatus('Session cleared', 'success');
    } catch (error) {
        updateStatus(`Error: ${error.message}`, 'error');
    }
}

// ═══════════════════════════════════════════════════════════════════════
// STATUS MESSAGES
// ═══════════════════════════════════════════════════════════════════════

function updateStatus(message, type = 'info') {
    const status = document.getElementById('status');
    status.innerHTML = message;
    status.className = `status show ${type}`;

    if (type !== 'loading' && type !== 'info') {
        setTimeout(() => {
            status.classList.remove('show');
        }, 5000);
    }
}

// ═══════════════════════════════════════════════════════════════════════
// UTILITIES
// ═══════════════════════════════════════════════════════════════════════

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}
