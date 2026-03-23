/**
 * 🚗 Vehicle Re-Identification System - Frontend
 * Complete implementation with batch upload, target search, and results display
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

    updateStatus('✓ Session initialized. Ready to upload images!', 'success');
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
        displaySelectedFiles();
    });

    fileInput.addEventListener('change', (e) => {
        STATE.uploadedFiles = Array.from(e.target.files);
        displaySelectedFiles();
    });
}

function displaySelectedFiles() {
    const fileList = document.getElementById('fileList');
    if (STATE.uploadedFiles.length === 0) {
        fileList.innerHTML = '';
        return;
    }

    fileList.innerHTML = `
        <div class="selected-files">
            <strong>${STATE.uploadedFiles.length} files selected:</strong>
            <ul>
                ${STATE.uploadedFiles.slice(0, 5).map(f => `<li>${f.name} (${(f.size / 1024).toFixed(1)} KB)</li>`).join('')}
                ${STATE.uploadedFiles.length > 5 ? `<li>... and ${STATE.uploadedFiles.length - 5} more</li>` : ''}
            </ul>
        </div>
    `;
    updateStatus(`${STATE.uploadedFiles.length} files selected. Click "Upload to Database" to proceed.`);
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
        displaySearchPreview();
    });

    searchInput.addEventListener('change', (e) => {
        STATE.searchFile = e.target.files[0];
        displaySearchPreview();
    });
}

function displaySearchPreview() {
    const preview = document.getElementById('searchPreview');
    if (!STATE.searchFile) {
        preview.innerHTML = '';
        return;
    }

    preview.innerHTML = `
        <div class="search-file-info">
            <strong>Target Image:</strong> ${STATE.searchFile.name} (${(STATE.searchFile.size / 1024).toFixed(1)} KB)
        </div>
    `;
    updateStatus(`Target image selected: ${STATE.searchFile.name}`);
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
// FILE SELECTION HELPERS
// ═══════════════════════════════════════════════════════════════════════

function chooseFiles() {
    document.getElementById('fileInput').click();
}

function chooseSearchFile() {
    document.getElementById('searchInput').click();
}

// ═══════════════════════════════════════════════════════════════════════
// BATCH UPLOAD FILES
// ═══════════════════════════════════════════════════════════════════════

async function uploadBatchFiles() {
    if (STATE.uploadedFiles.length === 0) {
        updateStatus('❌ No files selected. Please select images first.', 'error');
        return;
    }

    const progressBar = document.getElementById('uploadProgress');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const uploadBtn = document.getElementById('uploadBtn');

    uploadBtn.disabled = true;
    progressBar.style.display = 'block';

    updateStatus(`⬆️ Uploading ${STATE.uploadedFiles.length} images to database...`, 'loading');

    try {
        let successful = 0;
        let failed = 0;

        for (let i = 0; i < STATE.uploadedFiles.length; i++) {
            const file = STATE.uploadedFiles[i];
            const progress = ((i + 1) / STATE.uploadedFiles.length) * 100;

            progressFill.style.width = `${progress}%`;
            progressText.textContent = `${Math.round(progress)}% (${i + 1}/${STATE.uploadedFiles.length})`;

            try {
                const formData = new FormData();
                formData.append('file', file);

                const response = await fetch(`${STATE.apiBase}/upload?session_id=${STATE.sessionId}`, {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    failed++;
                    console.error(`Upload failed: ${file.name}`);
                } else {
                    successful++;
                    console.log(`✓ Uploaded: ${file.name}`);
                }
            } catch (error) {
                failed++;
                console.error(`Error uploading ${file.name}:`, error);
            }
        }

        progressFill.style.width = '100%';
        progressText.textContent = '100%';

        setTimeout(() => {
            progressBar.style.display = 'none';
            uploadBtn.disabled = false;
        }, 1000);

        if (failed === 0) {
            updateStatus(`✓ Successfully uploaded ${successful} images to database!`, 'success');
        } else {
            updateStatus(`⚠️ Uploaded ${successful} images. ${failed} failed.`, 'error');
        }

        STATE.uploadedFiles = [];
        document.getElementById('fileInput').value = '';
        document.getElementById('fileList').innerHTML = '';

        await refreshGallery();

    } catch (error) {
        updateStatus(`❌ Upload error: ${error.message}`, 'error');
        uploadBtn.disabled = false;
        progressBar.style.display = 'none';
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
            gallery.innerHTML = '<p class="empty-state">No images uploaded yet. Upload images above to build your database.</p>';
            return;
        }

        gallery.innerHTML = data.images.map((img, idx) => `
            <div class="gallery-item">
                <div class="gallery-number">#${idx + 1}</div>
                <div style="width: 100%; height: 100%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; font-size: 2rem; color: white;">
                    🚗
                </div>
                <div class="gallery-item-status">
                    ${img.embedding_ready ? '✓ Ready' : '⏳ Processing'}
                </div>
                <div class="gallery-item-name">${img.filename.substring(0, 15)}${img.filename.length > 15 ? '...' : ''}</div>
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
        updateStatus('❌ No target image selected. Please select an image to search.', 'error');
        return;
    }

    if (STATE.imageCount === 0) {
        updateStatus('❌ No images in database. Upload images first before searching.', 'error');
        return;
    }

    const searchBtn = document.getElementById('searchBtn');
    searchBtn.disabled = true;
    updateStatus('🔍 Searching database... <span class="spinner"></span>', 'loading');

    try {
        const formData = new FormData();
        formData.append('file', STATE.searchFile);

        const threshold = parseInt(document.getElementById('threshold').value) / 100;

        const response = await fetch(
            `${STATE.apiBase}/search?session_id=${STATE.sessionId}&threshold=${threshold}`,
            {
                method: 'POST',
                body: formData
            }
        );

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Search failed');
        }

        const data = await response.json();
        console.log('Search results:', data);

        displayResults(data);

        if (data.total_matches > 0) {
            updateStatus(
                `✓ Found ${data.total_matches} matching vehicles in ${data.search_time_ms.toFixed(0)}ms!`,
                'success'
            );
        } else {
            updateStatus(`⚠️ No matches found above ${threshold * 100}% threshold. Try lowering the threshold.`, 'error');
        }
    } catch (error) {
        updateStatus(`❌ Search error: ${error.message}`, 'error');
    } finally {
        searchBtn.disabled = false;
    }
}

// ═══════════════════════════════════════════════════════════════════════
// DISPLAY RESULTS
// ═══════════════════════════════════════════════════════════════════════

function displayResults(data) {
    const resultsSection = document.getElementById('resultsSection');
    const resultsList = document.getElementById('results');
    const resultsCount = document.getElementById('resultsCount');
    const searchTime = document.getElementById('searchTime');

    if (data.total_matches === 0) {
        resultsList.innerHTML = '<p class="empty-state">No matches found above the threshold</p>';
        resultsSection.style.display = 'block';
        return;
    }

    resultsCount.textContent = `${data.total_matches} matches found`;
    searchTime.textContent = `Search time: ${data.search_time_ms.toFixed(0)}ms`;

    const medals = ['🥇', '🥈', '🥉'];
    resultsList.innerHTML = data.matches.map((match, idx) => `
        <div class="result-item ${match.match_type}">
            <div class="result-rank">${medals[idx] || `#${idx + 1}`}</div>
            <div class="result-image" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; font-size: 2.5rem; color: white;">
                🚗
            </div>
            <div class="result-info">
                <div class="result-filename">
                    ${match.filename}
                </div>
                <div class="result-score">${(match.match_score * 100).toFixed(1)}%</div>
                <div class="result-type">
                    ${match.match_type === 'confident' ? '🟢 CONFIDENT' : match.match_type === 'probable' ? '🟡 PROBABLE' : '🟠 WEAK'}
                </div>
                <div class="result-meta">
                    <small>Uploaded: ${new Date(match.upload_time).toLocaleString()}</small>
                </div>
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
    if (!confirm('⚠️ This will clear all uploaded images from the database. Continue?')) return;

    try {
        await fetch(`${STATE.apiBase}/clear/${STATE.sessionId}`, { method: 'POST' });

        STATE.uploadedFiles = [];
        STATE.searchFile = null;
        STATE.imageCount = 0;

        document.getElementById('fileInput').value = '';
        document.getElementById('searchInput').value = '';
        document.getElementById('fileList').innerHTML = '';
        document.getElementById('searchPreview').innerHTML = '';
        document.getElementById('gallery').innerHTML = '<p class="empty-state">No images uploaded yet. Upload images above to build your database.</p>';
        document.getElementById('imageCount').textContent = '0';
        document.getElementById('resultsSection').style.display = 'none';

        updateStatus('✓ Session cleared. All images removed from database.', 'success');
    } catch (error) {
        updateStatus(`❌ Error clearing session: ${error.message}`, 'error');
    }
}

// ═══════════════════════════════════════════════════════════════════════
// STATUS MESSAGES
// ═══════════════════════════════════════════════════════════════════════

function updateStatus(message, type = 'info') {
    const status = document.getElementById('status');
    status.innerHTML = message;
    status.className = `status show ${type}`;

    if (type !== 'loading') {
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
