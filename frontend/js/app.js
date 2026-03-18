/**
 * Vehicle Forensic Matching System - Internal Dashboard
 * JavaScript Application - Enhanced with Charts, Dark Mode, and Real-time Updates
 */

// Configuration
const API_BASE_URL = "http://localhost:8899";
const METRICS_ENDPOINT = `${API_BASE_URL}/metrics`;
const HEALTH_ENDPOINT = `${API_BASE_URL}/health`;

// State
let currentResults = null;
let autoRefreshInterval = null;
let charts = {}; // Store chart instances
let performanceData = {
  responseTime: [],
  searchRequests: [],
  successRate: { success: 0, failure: 0 },
  matchQuality: [],
};

// Lightbox navigation state
let currentLightboxResults = [];
let currentLightboxIndex = 0;

// Search settings (configurable thresholds)
let searchSettings = {
  enableOrb: true,
  minSimilarity: 0.55,
  minOrbMatches: 8,
  topK: 10,
};

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  console.log(
    "Vehicle Forensic Matching System - Dashboard Initialized (Enhanced Version)"
  );

  // Initialize theme
  initializeTheme();

  // Initialize charts
  initializeCharts();

  // Setup event listeners
  setupEventListeners();

  // Initial health check
  checkSystemHealth();

  // Load system configuration
  loadSystemConfig();

  // Load initial metrics
  loadMetrics();

  // Auto-refresh every 30 seconds
  startAutoRefresh();

  // Update last update time
  updateLastUpdateTime();

  // Setup WebSocket for real-time updates (optional)
  setupWebSocket();
});

/**
 * Initialize Theme
 */
function initializeTheme() {
  const savedTheme = localStorage.getItem("theme") || "light";
  document.body.className = savedTheme + "-theme";
  updateThemeIcon(savedTheme);
}

/**
 * Toggle Theme (Light/Dark Mode)
 */
function toggleTheme() {
  const currentTheme = document.body.classList.contains("dark-theme")
    ? "dark"
    : "light";
  const newTheme = currentTheme === "dark" ? "light" : "dark";

  document.body.className = newTheme + "-theme";
  localStorage.setItem("theme", newTheme);
  updateThemeIcon(newTheme);

  // Update charts with new theme colors
  updateChartsTheme(newTheme);
}

/**
 * Update Theme Icon
 */
function updateThemeIcon(theme) {
  const icon = document.getElementById("themeIcon");
  if (icon) {
    icon.className = theme === "dark" ? "fas fa-sun" : "fas fa-moon";
  }
}

/**
 * Initialize Charts
 */
function initializeCharts() {
  const isDark = document.body.classList.contains("dark-theme");
  const colors = getChartColors(isDark);

  // Response Time Chart (Line)
  const responseTimeCtx = document.getElementById("responseTimeChart");
  if (responseTimeCtx) {
    charts.responseTime = new Chart(responseTimeCtx, {
      type: "line",
      data: {
        labels: [],
        datasets: [
          {
            label: "Response Time (ms)",
            data: [],
            borderColor: colors.primary,
            backgroundColor: colors.primaryAlpha,
            tension: 0.4,
            fill: true,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { mode: "index", intersect: false },
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: colors.grid },
          },
          x: {
            grid: { display: false },
          },
        },
      },
    });
  }

  // Search Requests Chart (Bar)
  const searchRequestsCtx = document.getElementById("searchRequestsChart");
  if (searchRequestsCtx) {
    charts.searchRequests = new Chart(searchRequestsCtx, {
      type: "bar",
      data: {
        labels: [],
        datasets: [
          {
            label: "Requests",
            data: [],
            backgroundColor: colors.success,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: colors.grid },
          },
        },
      },
    });
  }

  // Success Rate Chart (Pie)
  const successRateCtx = document.getElementById("successRateChart");
  if (successRateCtx) {
    charts.successRate = new Chart(successRateCtx, {
      type: "doughnut",
      data: {
        labels: ["Success", "Failure"],
        datasets: [
          {
            data: [0, 0],
            backgroundColor: [colors.success, colors.danger],
            borderWidth: 0,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom" },
        },
      },
    });
  }

  // Match Quality Chart (Histogram)
  const matchQualityCtx = document.getElementById("matchQualityChart");
  if (matchQualityCtx) {
    charts.matchQuality = new Chart(matchQualityCtx, {
      type: "bar",
      data: {
        labels: ["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"],
        datasets: [
          {
            label: "Matches",
            data: [0, 0, 0, 0, 0],
            backgroundColor: colors.primary,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: colors.grid },
          },
        },
      },
    });
  }

  // Load initial chart data
  updateChartsData();
}

/**
 * Get Chart Colors based on theme
 */
function getChartColors(isDark) {
  return {
    primary: isDark ? "#60a5fa" : "#2563eb",
    primaryAlpha: isDark ? "rgba(96, 165, 250, 0.1)" : "rgba(37, 99, 235, 0.1)",
    success: isDark ? "#34d399" : "#059669",
    danger: isDark ? "#f87171" : "#dc2626",
    warning: isDark ? "#fbbf24" : "#d97706",
    grid: isDark ? "rgba(255, 255, 255, 0.1)" : "rgba(0, 0, 0, 0.1)",
  };
}

/**
 * Update Charts Theme
 */
function updateChartsTheme(theme) {
  const isDark = theme === "dark";
  const colors = getChartColors(isDark);

  Object.values(charts).forEach((chart) => {
    if (chart && chart.options && chart.options.scales) {
      if (chart.options.scales.y) {
        chart.options.scales.y.grid.color = colors.grid;
      }
      chart.update();
    }
  });
}

/**
 * Update Charts Data
 */
async function updateChartsData() {
  try {
    // Fetch metrics from API
    const response = await fetch(`${API_BASE_URL}/metrics`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    console.log('Chart data update - metrics:', data.search_metrics_last_60min);

    // Update Response Time Chart (use real metrics)
    if (charts.responseTime && data.search_metrics_last_60min) {
      const avgResponseTime = Math.round(
        data.search_metrics_last_60min.avg_latency_ms || 0
      );
      const labels = charts.responseTime.data.labels || ["Last Hour"];

      // Keep last 24 data points, add new one
      if (charts.responseTime.data.datasets[0].data.length >= 24) {
        charts.responseTime.data.datasets[0].data.shift();
      }
      charts.responseTime.data.datasets[0].data.push(avgResponseTime);

      // Update labels if needed
      if (
        !charts.responseTime.data.labels ||
        charts.responseTime.data.labels.length === 0
      ) {
        charts.responseTime.data.labels = ["Now"];
      }

      charts.responseTime.update();
    }

    // Update Search Requests Chart (use real total requests)
    if (charts.searchRequests && data.search_metrics_last_60min) {
      const totalRequests = data.search_metrics_last_60min.total_requests || 0;

      // Keep last 24 data points
      if (charts.searchRequests.data.datasets[0].data.length >= 24) {
        charts.searchRequests.data.datasets[0].data.shift();
      }
      charts.searchRequests.data.datasets[0].data.push(totalRequests);

      if (
        !charts.searchRequests.data.labels ||
        charts.searchRequests.data.labels.length === 0
      ) {
        charts.searchRequests.data.labels = ["Now"];
      }

      charts.searchRequests.update();
    }

    // Update Success Rate Chart (use real success/failure counts)
    if (charts.successRate && data.search_metrics_last_60min) {
      const total = data.search_metrics_last_60min.total_requests || 0;
      const successful = data.search_metrics_last_60min.successful_requests || 0;
      const failed = data.search_metrics_last_60min.failed_requests || 0;
      const success = successful || Math.floor(total * 0.95); // Fallback to 95% if no data
      const failure = failed || (total - success);

      charts.successRate.data.datasets[0].data = [success, failure];
      charts.successRate.update();
    }

    // Update Match Quality Chart (use real avg matches data)
    if (charts.matchQuality && data.search_metrics_last_60min) {
      const avgMatches =
        data.search_metrics_last_60min.avg_matches_per_request || 0;

      // Distribute matches across quality buckets (simplified visualization)
      const qualityBuckets = [0, 0, 0, 0, 0]; // 0-20%, 20-40%, 40-60%, 60-80%, 80-100%
      const bucketIndex = Math.min(4, Math.floor((avgMatches / 10) * 5)); // Assuming max 10 matches
      qualityBuckets[bucketIndex] = avgMatches;

      charts.matchQuality.data.datasets[0].data = qualityBuckets;
      charts.matchQuality.update();
    }
  } catch (error) {
    console.error("Error updating charts:", error);
  }
}

/**
 * Export Charts as Images
 */
function exportCharts() {
  const chartsToExport = [
    "responseTimeChart",
    "searchRequestsChart",
    "successRateChart",
    "matchQualityChart",
  ];

  chartsToExport.forEach((chartId) => {
    const canvas = document.getElementById(chartId);
    if (canvas) {
      const url = canvas.toDataURL("image/png");
      const link = document.createElement("a");
      link.download = `${chartId}_${new Date().getTime()}.png`;
      link.href = url;
      link.click();
    }
  });

  showAlert("Charts exported successfully!", "success");
}

/**
 * Setup WebSocket for Real-time Updates
 */
function setupWebSocket() {
  // WebSocket is optional - only if backend supports it
  // This is a placeholder for future implementation
  console.log("WebSocket support: Optional feature for real-time updates");
}

/**
 * Setup Event Listeners
 * Initializes all event handlers for the dashboard
 */
function setupEventListeners() {
  // Dark Mode Toggle
  const themeToggle = document.getElementById("themeToggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", toggleTheme);
  }

  // Chart Time Range
  const chartTimeRange = document.getElementById("chartTimeRange");
  if (chartTimeRange) {
    chartTimeRange.addEventListener("change", () => {
      updateChartsData();
    });
  }

  // Export Charts
  const exportChartsBtn = document.getElementById("exportChartsBtn");
  if (exportChartsBtn) {
    exportChartsBtn.addEventListener("click", exportCharts);
  }

  // Auto Refresh Toggle
  const autoRefreshToggle = document.getElementById("autoRefreshToggle");
  if (autoRefreshToggle) {
    autoRefreshToggle.addEventListener("change", (e) => {
      if (e.target.checked) {
        startAutoRefresh();
      } else {
        stopAutoRefresh();
      }
    });
  }

  // Search form submission
  const searchForm = document.getElementById("searchForm");
  searchForm.addEventListener("submit", handleSearch);

  // Enter key on input (use keydown for better compatibility)
  const exitInput = document.getElementById("exitTxId");
  if (exitInput) {
    exitInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        handleSearch(e);
      }
    });
  }

  // Admin Controls
  setupAdminControls();
}

/**
 * Setup Admin Control Event Listeners
 */
function setupAdminControls() {
  // Cache Management
  const viewCacheStatsBtn = document.getElementById("viewCacheStatsBtn");
  if (viewCacheStatsBtn) {
    viewCacheStatsBtn.addEventListener("click", loadCacheStats);
  }

  const clearCacheBtn = document.getElementById("clearCacheBtn");
  if (clearCacheBtn) {
    clearCacheBtn.addEventListener("click", clearCache);
  }

  // Circuit Breaker Management
  const viewCircuitBreakerBtn = document.getElementById(
    "viewCircuitBreakerBtn"
  );
  if (viewCircuitBreakerBtn) {
    viewCircuitBreakerBtn.addEventListener("click", loadCircuitBreakerStatus);
  }

  const resetCircuitBreakerBtn = document.getElementById(
    "resetCircuitBreakerBtn"
  );
  if (resetCircuitBreakerBtn) {
    resetCircuitBreakerBtn.addEventListener("click", resetCircuitBreaker);
  }

  // Prometheus Metrics
  const openPrometheusBtn = document.getElementById("openPrometheusBtn");
  if (openPrometheusBtn) {
    openPrometheusBtn.addEventListener("click", () => {
      window.open(`${API_BASE_URL}/metrics`, "_blank");
    });
  }

  // Refresh Metrics manually
  const refreshMetricsBtn = document.getElementById("refreshMetricsBtn");
  if (refreshMetricsBtn) {
    refreshMetricsBtn.addEventListener("click", () => {
      loadMetrics();
      showAlert("Metrics refreshed", "success");
    });
  }

  // Refresh Vector Database Stats
  const refreshVectorBtn = document.getElementById("refreshVectorBtn");
  if (refreshVectorBtn) {
    refreshVectorBtn.addEventListener("click", () => {
      checkSystemHealth(); // This will refresh vector stats too
      showAlert("Vector database stats refreshed", "success");
    });
  }

  // Metric Time Range Selector
  const metricTimeRange = document.getElementById("metricTimeRange");
  if (metricTimeRange) {
    metricTimeRange.addEventListener("change", (e) => {
      // For now, just refresh metrics when range changes
      // In a full implementation, this would filter metrics by time range
      loadMetrics();
      showAlert(
        `Time range changed to ${
          e.target.options[e.target.selectedIndex].text
        }`,
        "info"
      );
    });
  }

  // System Settings
  const autoRefreshToggle = document.getElementById("autoRefreshToggle");
  if (autoRefreshToggle) {
    autoRefreshToggle.addEventListener("change", (e) => {
      if (e.target.checked) {
        startAutoRefresh();
        showAlert("Auto-refresh enabled", "success");
      } else {
        stopAutoRefresh();
        showAlert("Auto-refresh disabled", "info");
      }
    });
  }

  const showDebugInfo = document.getElementById("showDebugInfo");
  if (showDebugInfo) {
    showDebugInfo.addEventListener("change", (e) => {
      if (e.target.checked) {
        enableDebugMode();
      } else {
        disableDebugMode();
      }
    });
  }

  const notificationsToggle = document.getElementById("notificationsToggle");
  if (notificationsToggle) {
    notificationsToggle.addEventListener("change", (e) => {
      window.NOTIFICATIONS_ENABLED = e.target.checked;
      showAlert(
        e.target.checked ? "Notifications enabled" : "Notifications disabled",
        "info"
      );
    });
  }

  // Quick Actions
  const clearAllCachesBtn = document.getElementById("clearAllCaches");
  if (clearAllCachesBtn) {
    clearAllCachesBtn.addEventListener("click", clearSystemCache);
  }

  const viewCacheStatsQuick = document.getElementById("viewCacheStats");
  if (viewCacheStatsQuick) {
    viewCacheStatsQuick.addEventListener("click", viewCacheStatistics);
  }

  const resetCircuitBreakerQuick = document.getElementById(
    "resetCircuitBreaker"
  );
  if (resetCircuitBreakerQuick) {
    resetCircuitBreakerQuick.addEventListener("click", resetCircuitBreaker);
  }

  const viewCircuitBreakerStatusQuick = document.getElementById(
    "viewCircuitBreakerStatus"
  );
  if (viewCircuitBreakerStatusQuick) {
    viewCircuitBreakerStatusQuick.addEventListener(
      "click",
      viewCircuitBreakerStatus
    );
  }

  // Database Management
  const viewDbStatsBtn = document.getElementById("viewDbStatsBtn");
  if (viewDbStatsBtn) {
    viewDbStatsBtn.addEventListener("click", loadDatabaseStats);
  }

  const checkDbHealthBtn = document.getElementById("checkDbHealthBtn");
  if (checkDbHealthBtn) {
    checkDbHealthBtn.addEventListener("click", checkDatabaseHealth);
  }

  const optimizeDbBtn = document.getElementById("optimizeDbBtn");
  if (optimizeDbBtn) {
    optimizeDbBtn.addEventListener("click", optimizeDatabase);
  }

  // Service Monitoring
  const checkServicesBtn = document.getElementById("checkServicesBtn");
  if (checkServicesBtn) {
    checkServicesBtn.addEventListener("click", checkExternalServices);
  }

  const restartServicesBtn = document.getElementById("restartServicesBtn");
  if (restartServicesBtn) {
    restartServicesBtn.addEventListener("click", restartAllServices);
  }

  // Security & Audit
  const viewSecurityLogsBtn = document.getElementById("viewSecurityLogsBtn");
  if (viewSecurityLogsBtn) {
    viewSecurityLogsBtn.addEventListener("click", loadSecurityLogs);
  }

  const runSecurityScanBtn = document.getElementById("runSecurityScanBtn");
  if (runSecurityScanBtn) {
    runSecurityScanBtn.addEventListener("click", runSecurityScan);
  }

  // Enhanced Quick Actions
  const backupSystem = document.getElementById("backupSystem");
  if (backupSystem) {
    backupSystem.addEventListener("click", performSystemBackup);
  }

  const performanceTest = document.getElementById("performanceTest");
  if (performanceTest) {
    performanceTest.addEventListener("click", runPerformanceTest);
  }

  const restartApp = document.getElementById("restartApp");
  if (restartApp) {
    restartApp.addEventListener("click", restartApplication);
  }

  const emergencyStop = document.getElementById("emergencyStop");
  if (emergencyStop) {
    emergencyStop.addEventListener("click", emergencyStopApplication);
  }

  // Cache Management (Admin Panel)
  const clearCacheBtn2 = document.getElementById("clearCacheBtn");
  if (clearCacheBtn2) {
    clearCacheBtn2.addEventListener("click", clearSystemCache);
  }

  const viewCacheStatsBtn2 = document.getElementById("viewCacheStatsBtn");
  if (viewCacheStatsBtn2) {
    viewCacheStatsBtn2.addEventListener("click", viewCacheStatistics);
  }

  // Circuit Breaker (Admin Panel)
  const viewCircuitBreakerStatusBtn2 = document.getElementById(
    "viewCircuitBreakerStatusBtn"
  );
  if (viewCircuitBreakerStatusBtn2) {
    viewCircuitBreakerStatusBtn2.addEventListener(
      "click",
      viewCircuitBreakerStatus
    );
  }

  const resetCircuitBreakerBtn2 = document.getElementById(
    "resetCircuitBreakerBtn"
  );
  if (resetCircuitBreakerBtn2) {
    resetCircuitBreakerBtn2.addEventListener("click", resetCircuitBreaker);
  }

  // Initialize notifications state
  window.NOTIFICATIONS_ENABLED = true;

  // Update status indicators
  updateStatusIndicators();
}

/**
 * Handle Search Form Submission
 */
/**
 * Handle search form submission
 * @param {Event} e - The form submit event
 */
async function handleSearch(e) {
  e.preventDefault();

  const exitTxId = document.getElementById("exitTxId").value.trim();
  const topK = parseInt(document.getElementById("topK").value) || 10;
  const includeDetails = document.getElementById("includeDetails").checked;

  if (!exitTxId) {
    const inputEl = document.getElementById("exitTxId");
    if (inputEl) {
      inputEl.setAttribute("aria-invalid", "true");
      inputEl.focus();
    }
    showAlert("Please enter an EXIT transaction ID", "error");
    return;
  } else {
    const inputEl = document.getElementById("exitTxId");
    if (inputEl) inputEl.removeAttribute("aria-invalid");
  }

  // Show loading state
  setSearchLoading(true);
  hideResults();

  try {
    console.log(
      `Searching for ${exitTxId}, k=${topK}, details=${includeDetails}, settings:`,
      searchSettings
    );

    // Build request with frontend settings
    const requestBody = {
      exit_transaction_id: exitTxId,
      k: topK,
      // Send settings from frontend
      enable_orb: searchSettings.enableOrb,
      min_similarity: searchSettings.minSimilarity,
      min_orb_matches: searchSettings.minOrbMatches,
    };

    // Make API call
    const url = `${API_BASE_URL}/search?include_details=${includeDetails}`;
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    const result = await response.json();
    currentResults = result;

    // Store match details globally for lightbox navigation
    window.currentSearchResults = result.matches_details || [];

    console.log("Search results:", result);

    // Display results
    displayResults(result, includeDetails);

    // Show success message
    showAlert(
      `Found ${result.matches_found} match${
        result.matches_found !== 1 ? "es" : ""
      } in ${result.processing_time_seconds}s`,
      "success"
    );

    // Refresh metrics to show updated stats
    loadMetrics();
  } catch (error) {
    console.error("Search failed:", error);
    showAlert(`Search failed: ${error.message}`, "error");
  } finally {
    setSearchLoading(false);
  }
}

/**
 * Display Search Results
 */
function displayResults(result, includeDetails) {
  const resultsCard = document.getElementById("resultsCard");
  const resultsBadge = document.getElementById("resultsBadge");
  const resultSummary = document.getElementById("resultSummary");
  const resultsList = document.getElementById("resultsList");

  // Update badge
  resultsBadge.textContent = `${result.matches_found} match${
    result.matches_found !== 1 ? "es" : ""
  }`;

  // Build exit image preview
  const exitImagePreview = result.exit_image_path
    ? `<div class="summary-item exit-image-item" style="grid-column: span 2;">
                <div class="summary-label">EXIT Vehicle Image</div>
                <div class="exit-image-container">
                    <img src="${API_BASE_URL}/image/${result.exit_transaction_id}" 
                         alt="Exit Vehicle ${result.exit_transaction_id}"
                         class="exit-vehicle-image"
                         onclick="openLightbox('${result.exit_transaction_id}', '${result.exit_timestamp}')"
                         onerror="this.parentElement.innerHTML='<div style=\\'padding:20px;text-align:center;color:#999;\\'>Exit Image Not Available</div>';">
                </div>
            </div>`
    : "";

    // PRO: Confidence badge
    const confidenceLevel = result.confidence || 'unknown';
    const confidenceBadge = getConfidenceBadge(confidenceLevel);
    const humanReviewNote = result.needs_human_review 
        ? '<div class="human-review-alert">⚠️ <strong>Human Review Recommended</strong> - Low confidence match</div>'
        : '';
    
    // Build summary
    const summaryHTML = `
        ${humanReviewNote}
        <div class="result-summary-grid">
            ${exitImagePreview}
            <div class="summary-item">
                <div class="summary-label">EXIT Transaction</div>
                <div class="summary-value" style="font-size: 16px;">${result.exit_transaction_id}</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">Exit Time</div>
                <div class="summary-value" style="font-size: 14px;">${formatDateTime(result.exit_timestamp)}</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">Matches Found</div>
                <div class="summary-value">${result.matches_found}</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">Match Confidence</div>
                <div class="summary-value">${confidenceBadge}</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">Processing Time</div>
                <div class="summary-value">${result.processing_time_seconds}<span class="metric-unit">sec</span></div>
            </div>
        </div>
    `;
  resultSummary.innerHTML = summaryHTML;

  // Build results list
  if (result.matches_found === 0) {
    resultsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <p>No matching ENTRY vehicles found within the 10-hour time window.</p>
            </div>
        `;
  } else {
    let resultsHTML = "";

    if (includeDetails && result.matches_details) {
      // Detailed view with image previews
      const matches = result.matches_details;
      matches.forEach((match, index) => {
        const imagePreview = match.image_path
          ? `<div class="image-preview" onclick="openLightbox('${match.entry_transaction_id}', '${match.entry_timestamp}', currentSearchResults, ${index})" title="Click to enlarge">
                        <img src="${API_BASE_URL}/image/${match.entry_transaction_id}" 
                             alt="Vehicle ${match.entry_transaction_id}"
                             onerror="this.parentElement.innerHTML='<div style=\\'display:flex;align-items:center;justify-content:center;height:100%;color:#999;font-size:0.8rem;\\'>No Image</div>';">
                       </div>`
          : `<div class="image-preview" style="display:flex;align-items:center;justify-content:center;background:#f5f5f5;color:#999;">
                        <span style="font-size:0.75rem;">No Image</span>
                       </div>`;

        // PRO: VRN similarity badge
        const vrnSimilarity = match.vrn_similarity || 0;
        const vrnBadge =
          vrnSimilarity > 0.8
            ? `<span class="vrn-badge vrn-high" title="License Plate Match">🚘 VRN ${(
                vrnSimilarity * 100
              ).toFixed(0)}%</span>`
            : vrnSimilarity > 0.5
            ? `<span class="vrn-badge vrn-medium" title="Partial License Plate Match">🚘 VRN ${(
                vrnSimilarity * 100
              ).toFixed(0)}%</span>`
            : "";

        // PRO: Calibrated score display
        const calibratedScore = match.calibrated_score || match.combined_score;
        const calibratedPercent = (calibratedScore * 100).toFixed(1);

        // PRO: ORB inlier ratio for RANSAC verification
        const orbInlierRatio = match.orb_inlier_ratio || 0;

        resultsHTML += `
                    <div class="result-item">
                        ${imagePreview}
                        <div class="result-content">
                            <div class="result-header">
                                <div class="result-id">🚗 ${
                                  match.entry_transaction_id
                                }</div>
                                <div class="result-badges">
                                    ${vrnBadge}
                                    <div class="result-rank">#${
                                      match.rank
                                    }</div>
                                </div>
                            </div>
                            <div class="result-details">
                                <div class="detail-item">
                                    <div class="detail-label">Entry Time</div>
                                    <div class="detail-value">${formatDateTime(
                                      match.entry_timestamp
                                    )}</div>
                                </div>
                                <div class="detail-item highlight">
                                    <div class="detail-label">Match Probability</div>
                                    <div class="detail-value score-${getScoreClass(
                                      calibratedScore
                                    )}">${calibratedPercent}%</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Embedding Score</div>
                                    <div class="detail-value">${(
                                      match.embedding_similarity * 100
                                    ).toFixed(1)}%</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">ORB Matches</div>
                                    <div class="detail-value">${
                                      match.orb_matches || 0
                                    } pts</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">ORB Quality</div>
                                    <div class="detail-value">${(
                                      (match.orb_quality || 0) * 100
                                    ).toFixed(1)}%</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Geometric Fit</div>
                                    <div class="detail-value">${(
                                      orbInlierRatio * 100
                                    ).toFixed(0)}%</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Time Proximity</div>
                                    <div class="detail-value">${(
                                      match.time_proximity * 100
                                    ).toFixed(1)}%</div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
      });
    } else {
      // Simple compact list view
      result.matched_entry_transaction_ids.forEach((txId, index) => {
        resultsHTML += `
                    <div class="result-item" style="padding: 0.75rem 1rem;">
                        <div class="result-content">
                            <div class="result-header" style="padding-bottom: 0; border-bottom: none;">
                                <div class="result-id">🚗 ${txId}</div>
                                <div class="result-rank">#${index + 1}</div>
                            </div>
                        </div>
                    </div>
                `;
      });
    }

    resultsList.innerHTML = resultsHTML;

    // Make result items keyboard accessible and add click/keyboard copy behavior
    const resultItems = resultsList.querySelectorAll(".result-item");
    resultItems.forEach((item) => {
      item.setAttribute("tabindex", "0");
      item.setAttribute("role", "article");
      // keyboard activation (Enter or Space copies entry id)
      item.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter" || ev.key === " ") {
          ev.preventDefault();
          const idEl = item.querySelector(".result-id");
          if (idEl) {
            const id = idEl.textContent.replace("📌", "").trim();
            navigator.clipboard.writeText(id);
            showAlert(`Copied ${id}`, "success");
          }
        }
      });
      // click behavior
      item.addEventListener("click", () => {
        const idEl = item.querySelector(".result-id");
        if (idEl) {
          const id = idEl.textContent.replace("📌", "").trim();
          navigator.clipboard.writeText(id);
          showAlert(`Copied ${id}`, "success");
        }
      });
    });
    // move focus to first result for keyboard users
    if (resultItems.length > 0) resultItems[0].focus();
  }

  // Show results card
  resultsCard.style.display = "block";

  // Smooth scroll to results
  setTimeout(() => {
    resultsCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, 100);
}

/**
 * Check System Health
 */
async function checkSystemHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    const health = await response.json();

    updateSystemStatus(health);
    displayHealthInfo(health);
  } catch (error) {
    console.error("Health check failed:", error);
    updateSystemStatus({ status: "error", database_ok: false });
    document.getElementById("healthContent").innerHTML = `
            <div class="alert alert-error">
                ❌ Cannot connect to API server at ${API_BASE_URL}
            </div>
        `;
  }
}

/**
 * Update System Status Indicator
 */
function updateSystemStatus(health) {
  const indicator = document.getElementById("statusIndicator");
  const statusText = document.getElementById("statusText");

  if (health.status === "healthy") {
    indicator.className = "status-indicator healthy";
    statusText.textContent = "System Healthy";
  } else {
    indicator.className = "status-indicator unhealthy";
    statusText.textContent =
      health.status === "error" ? "Connection Error" : "System Unhealthy";
  }
}

/**
 * Display Health Information
 */
function displayHealthInfo(health) {
  const healthContent = document.getElementById("healthContent");

  const dbStatus = health.database_ok ? "✅ Connected" : "❌ Disconnected";
  const dbClass = health.database_ok ? "success" : "danger";

  healthContent.innerHTML = `
        <div class="metric-grid">
            <div class="metric-item ${
              health.status === "healthy" ? "success" : "danger"
            }">
                <div class="metric-label">System Status</div>
                <div class="metric-value">${
                  health.status === "healthy" ? "✅" : "⚠️"
                } ${health.status}</div>
            </div>
            <div class="metric-item ${dbClass}">
                <div class="metric-label">Database</div>
                <div class="metric-value">${dbStatus}</div>
            </div>
        </div>
        <ul class="info-list" style="margin-top: 16px;">
            <li class="info-item">
                <span class="info-label">System Version</span>
                <span class="info-value">${health.version}</span>
            </li>
            <li class="info-item">
                <span class="info-label">Embedding Version</span>
                <span class="info-value">${health.embedding_version}</span>
            </li>
        </ul>
    `;

  // Display vector DB stats if available
  if (health.vector_db_stats) {
    displayVectorDbStats(health.vector_db_stats);
  }
}

/**
 * Display Vector Database Statistics
 */
function displayVectorDbStats(stats) {
  // Update individual stat elements
  document.getElementById("totalVectors").textContent = (
    stats.total_vectors || 0
  ).toLocaleString();
  document.getElementById("vectorDimensions").textContent =
    stats.dimension || 5632;
  document.getElementById("indexSize").textContent = stats.index_size_mb
    ? `${stats.index_size_mb} MB`
    : "0 MB";
  document.getElementById("avgQueryTime").textContent = stats.avg_query_time_ms
    ? `${stats.avg_query_time_ms}ms`
    : "0ms";
  document.getElementById("totalQueries").textContent = (
    stats.total_queries || 0
  ).toLocaleString();
  document.getElementById("cacheHitRate").textContent = stats.cache_hit_rate
    ? `${Math.round(stats.cache_hit_rate * 100)}%`
    : "0%";

  // Hide loading content and show stats
  document.getElementById("vectorDbContent").style.display = "none";
}

/**
 * Load and Display System Configuration
 */
async function loadSystemConfig() {
  try {
    const response = await fetch(`${API_BASE_URL}/config`);
    const config = await response.json();

    // Update search settings with config values
    if (config.matching) {
      // Update internal searchSettings
      searchSettings.topK = config.matching.default_top_k || 10;
      
      // Update UI if elements exist
      const topKInput = document.getElementById("topK");
      if (topKInput && !topKInput.value) {
        topKInput.value = config.matching.default_top_k;
      }
    }

    // Display optimization status in console
    console.log("System Configuration Loaded:", config);
    
    // Display loaded partitions if available
    if (config.faiss && config.faiss.loaded_partitions) {
      console.log("Loaded Partitions:", config.faiss.loaded_partitions);
      
      // Show optimization info to user
      if (config.faiss.lazy_load) {
        console.log("✅ Lazy loading enabled - partitions loaded on demand");
        console.log(`📊 Max partitions: ${config.faiss.max_loaded_partitions}`);
        console.log(`⏱️ Partition TTL: ${config.faiss.partition_ttl_hours} hours`);
      }
    }

    // Display ingestion config
    if (config.ingestion) {
      console.log("Ingestion Settings:");
      console.log(`  - Batch size: ${config.ingestion.batch_size}`);
      console.log(`  - Worker threads: ${config.ingestion.worker_threads}`);
      console.log(`  - Poll interval: ${config.ingestion.poll_interval}s`);
    }

    return config;
  } catch (error) {
    console.error("Failed to load system config:", error);
    return null;
  }
}

/**
 * Load Performance Metrics
 */
async function loadMetrics() {
  try {
    const response = await fetch(METRICS_ENDPOINT);
    if (!response.ok) {
      console.error(`Metrics endpoint returned ${response.status}`);
      throw new Error(`HTTP ${response.status}`);
    }

    const metrics = await response.json();
    console.log('Loaded metrics successfully:', {
      search: metrics.search_metrics_last_60min,
      system: metrics.system,
      vector_db: metrics.vector_db
    });
    displayMetrics(metrics);
    updateVectorDBStats(metrics);
    updateChartsData(); // Also update charts when metrics load
  } catch (error) {
    console.error("Failed to load metrics:", error);
    console.error("API endpoint:", METRICS_ENDPOINT);
    // Set default values on error
    setDefaultMetrics();
  }
}

/**
 * Set Default Metrics on Error
 */
function setDefaultMetrics() {
  document.getElementById("cpuUsage").textContent = "0%";
  document.getElementById("memoryUsage").textContent = "0%";
  document.getElementById("diskUsage").textContent = "0%";
  document.getElementById("totalVectors").textContent = "0";
  document.getElementById("avgResponseTime").textContent = "0ms";
  document.getElementById("requestsPerMin").textContent = "0";
}

/**
 * Update Vector DB Statistics
 */
function updateVectorDBStats(metrics) {
  if (metrics.vector_db) {
    const totalVectors = metrics.vector_db.total_vectors || 0;
    document.getElementById("totalVectors").textContent =
      totalVectors.toLocaleString();
    document.getElementById("vectorDimensions").textContent = "5632";

    // Update partitions if available
    if (
      metrics.vector_db.partitions &&
      metrics.vector_db.partitions.length > 0
    ) {
      const latestPartition =
        metrics.vector_db.partitions[metrics.vector_db.partitions.length - 1];
      console.log(
        `Latest partition: ${latestPartition.date} with ${latestPartition.vector_count} vectors`
      );
    }
  }
}

/**
 * Display Performance Metrics
 */
function displayMetrics(metrics) {
  // Log the actual metrics structure for debugging
  console.log('Received metrics:', metrics);
  
  const searchMetrics = metrics.search_metrics_last_60min || {};
  const allTimeStats = metrics.all_time_stats || {};
  const systemMetrics = metrics.system || {};

  // CPU Metrics
  const cpuUsage = Math.round(systemMetrics.cpu_percent || 0);
  document.getElementById("cpuUsage").textContent = `${cpuUsage}%`;
  document.getElementById("cpuBar").style.width = `${cpuUsage}%`;

  // CPU load - handle both array and single value
  const cpuLoad = systemMetrics.cpu_load_avg ? 
    (Array.isArray(systemMetrics.cpu_load_avg) ? systemMetrics.cpu_load_avg[0] : systemMetrics.cpu_load_avg) : 0;
  document.getElementById("cpuLoad").textContent = cpuLoad.toFixed(2);
  
  // CPU temp - may not be available on all systems
  document.getElementById("cpuTemp").textContent = `${
    systemMetrics.cpu_temp || "--"
  }°C`;

  // Memory Metrics
  const memoryPercent = Math.round(systemMetrics.memory_percent || 0);
  const memoryUsed = Math.round(systemMetrics.memory_mb || 0);
  const memoryTotal = Math.round((memoryUsed / (memoryPercent || 1)) * 100) || 0;

  document.getElementById("memoryUsage").textContent = `${memoryPercent}%`;
  document.getElementById("memoryBar").style.width = `${memoryPercent}%`;
  document.getElementById(
    "memoryDetails"
  ).textContent = `${memoryUsed}MB / ${memoryTotal}MB`;
  document.getElementById("swapUsage").textContent = `${
    Math.round(systemMetrics.swap_percent || 0)
  }%`;

  // Disk Metrics - use disk object from API
  const diskMetrics = metrics.disk || {};
  const diskPercent = Math.round(diskMetrics.percent || 0);
  const diskUsed = Math.round(diskMetrics.used_gb || 0);
  const diskTotal = Math.round(diskMetrics.total_gb || 0);

  document.getElementById("diskUsage").textContent = `${diskPercent}%`;
  document.getElementById("diskBar").style.width = `${diskPercent}%`;
  document.getElementById(
    "diskDetails"
  ).textContent = `${diskUsed}GB / ${diskTotal}GB`;
  document.getElementById("diskIO").textContent = `${
    systemMetrics.disk_io_ops || 0
  } ops/s`;

  // Network Metrics - may not be available
  document.getElementById("networkDown").textContent = `${(
    systemMetrics.network_download_mbps || 0
  ).toFixed(2)} MB/s`;
  document.getElementById("networkUp").textContent = `${(
    systemMetrics.network_upload_mbps || 0
  ).toFixed(2)} MB/s`;
  document.getElementById("networkConn").textContent =
    systemMetrics.network_connections || 0;

  // Application Metrics
  document.getElementById("activeConnections").textContent =
    systemMetrics.active_connections || systemMetrics.threads || 0;
  document.getElementById("avgResponseTime").textContent = `${
    Math.round(searchMetrics.avg_latency_ms || 0)
  }ms`;
  document.getElementById("requestsPerMin").textContent =
    Math.round(searchMetrics.requests_per_minute || 0);

  // Update metric colors based on thresholds
  updateMetricColors();
}

/**
 * Update Metric Colors Based on Thresholds
 */
function updateMetricColors() {
  // CPU Usage
  const cpuUsage = parseFloat(document.getElementById("cpuUsage").textContent);
  const cpuBar = document.getElementById("cpuBar");
  if (cpuUsage > 90) {
    cpuBar.style.background = "linear-gradient(90deg, #dc2626, #b91c1c)";
  } else if (cpuUsage > 70) {
    cpuBar.style.background = "linear-gradient(90deg, #f59e0b, #d97706)";
  } else {
    cpuBar.style.background = "linear-gradient(90deg, #10b981, #059669)";
  }

  // Memory Usage
  const memoryUsage = parseFloat(
    document.getElementById("memoryUsage").textContent
  );
  const memoryBar = document.getElementById("memoryBar");
  if (memoryUsage > 90) {
    memoryBar.style.background = "linear-gradient(90deg, #dc2626, #b91c1c)";
  } else if (memoryUsage > 70) {
    memoryBar.style.background = "linear-gradient(90deg, #f59e0b, #d97706)";
  } else {
    memoryBar.style.background = "linear-gradient(90deg, #3b82f6, #2563eb)";
  }

  // Disk Usage
  const diskUsage = parseFloat(
    document.getElementById("diskUsage").textContent
  );
  const diskBar = document.getElementById("diskBar");
  if (diskUsage > 90) {
    diskBar.style.background = "linear-gradient(90deg, #dc2626, #b91c1c)";
  } else if (diskUsage > 70) {
    diskBar.style.background = "linear-gradient(90deg, #f59e0b, #d97706)";
  } else {
    diskBar.style.background = "linear-gradient(90deg, #f59e0b, #d97706)";
  }
}

/**
 * Refresh Functions
 */
async function performRefresh(actionFn, btnId, loaderId) {
  const btn = document.getElementById(btnId);
  const loader = document.getElementById(loaderId);
  try {
    if (btn) {
      btn.disabled = true;
      btn.setAttribute("aria-busy", "true");
    }
    if (loader) loader.style.display = "inline-block";
    await actionFn();
  } catch (err) {
    console.error("Refresh action failed:", err);
    showAlert("Refresh failed", "error");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.removeAttribute("aria-busy");
    }
    if (loader) loader.style.display = "none";
  }
}

async function refreshHealth() {
  await performRefresh(
    checkSystemHealth,
    "refreshHealthBtn",
    "refreshHealthLoader"
  );
  showAlert("Health data refreshed", "success");
}

async function refreshMetrics() {
  await performRefresh(
    loadMetrics,
    "refreshMetricsBtn",
    "refreshMetricsLoader"
  );
  showAlert("Metrics refreshed", "success");
}

// attach refresh button listeners (ensure no inline onclick is required)
document.addEventListener("DOMContentLoaded", () => {
  const hbtn = document.getElementById("refreshHealthBtn");
  if (hbtn) hbtn.addEventListener("click", refreshHealth);
  const mbtn = document.getElementById("refreshMetricsBtn");
  if (mbtn) mbtn.addEventListener("click", refreshMetrics);
});

/**
 * Auto-refresh
 */
function startAutoRefresh() {
  // Refresh every 30 seconds
  autoRefreshInterval = setInterval(() => {
    checkSystemHealth();
    loadMetrics();
    updateLastUpdateTime();
  }, 30000);
}

function stopAutoRefresh() {
  if (autoRefreshInterval) {
    clearInterval(autoRefreshInterval);
    autoRefreshInterval = null;
  }
}

/**
 * Update Last Update Time
 */
function updateLastUpdateTime() {
  const now = new Date();
  document.getElementById("lastUpdate").textContent = now.toLocaleTimeString();
}

/**
 * Utility Functions
 */
function setSearchLoading(loading) {
  const btn = document.getElementById("searchBtn");
  const btnText = document.getElementById("searchBtnText");
  const btnLoader = document.getElementById("searchBtnLoader");
  const form = document.getElementById("searchForm");

  if (!btn) return;
  if (loading) {
    btn.disabled = true;
    btn.setAttribute("aria-busy", "true");
    if (form) form.setAttribute("aria-busy", "true");
    if (btnText) btnText.style.display = "none";
    if (btnLoader) btnLoader.style.display = "block";
  } else {
    btn.disabled = false;
    btn.removeAttribute("aria-busy");
    if (form) form.removeAttribute("aria-busy");
    if (btnText) btnText.style.display = "block";
    if (btnLoader) btnLoader.style.display = "none";
  }
}

function hideResults() {
  document.getElementById("resultsCard").style.display = "none";
}

function showAlert(message, type = "success") {
  // Create accessible alert element (polite)
  const alert = document.createElement("div");
  alert.className = `alert alert-${type}`;
  alert.setAttribute("role", "status");
  alert.setAttribute("aria-live", "polite");
  alert.setAttribute("aria-atomic", "true");

  // Add icon based on type
  const iconMap = {
    success: "✓",
    error: "✕",
    warning: "⚠",
    info: "ℹ",
  };

  // Create alert structure
  alert.innerHTML = `
        <span class="alert-icon">${iconMap[type] || "ℹ"}</span>
        <span class="alert-content">${message}</span>
        <button class="alert-close" onclick="this.parentElement.remove()" aria-label="Close notification">×</button>
    `;

  // Position the alert
  const existingAlerts = document.querySelectorAll(".alert");
  const offset = existingAlerts.length * 60;
  alert.style.position = "fixed";
  alert.style.top = `${20 + offset}px`;
  alert.style.right = "20px";
  alert.style.zIndex = "9999";
  alert.style.animation = "toastSlideIn 0.3s ease-out";

  document.body.appendChild(alert);

  // Remove after 5 seconds
  setTimeout(() => {
    alert.style.animation = "toastSlideOut 0.3s ease-out";
    setTimeout(() => {
      if (alert.parentElement) {
        alert.remove();
      }
    }, 300);
  }, 5000);
}

function formatDateTime(dateString) {
  const date = new Date(dateString);
  return date.toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

/**
 * PRO: Get score class for color coding
 * @param {number} score - Score value (0-1)
 * @returns {string} Class name for styling
 */
function getScoreClass(score) {
    if (score >= 0.85) return 'high';
    if (score >= 0.65) return 'medium';
    if (score >= 0.45) return 'low';
    return 'very-low';
}

/**
 * PRO: Get confidence badge HTML
 * @param {string} level - Confidence level from API
 * @returns {string} HTML for confidence badge
 */
function getConfidenceBadge(level) {
    const badges = {
        'high': '<span class="confidence-badge confidence-high">✅ HIGH</span>',
        'medium': '<span class="confidence-badge confidence-medium">🔶 MEDIUM</span>',
        'low': '<span class="confidence-badge confidence-low">⚠️ LOW</span>',
        'no_match': '<span class="confidence-badge confidence-none">❌ NO MATCH</span>',
        'unknown': '<span class="confidence-badge confidence-unknown">❓ UNKNOWN</span>'
    };
    return badges[level.toLowerCase()] || badges['unknown'];
}

// Add slide-in animation
const style = document.createElement("style");
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Expose global functions for HTML onclick handlers
window.refreshHealth = refreshHealth;
window.refreshMetrics = refreshMetrics;

// --- API Docs Modal: Complete rewrite for consistency ---

/**
 * Clone API documentation for modal display
 * @returns {HTMLElement|null} Cloned API docs container
 */
function cloneApiDocsForModal() {
  // Get content from template
  const template = document.getElementById("apiDocsTemplate");
  if (!template || !template.content) {
    console.error("API docs template not found");
    return null;
  }

  // Clone template content
  const clonedContent = template.content.cloneNode(true);
  const container = clonedContent.querySelector(".api-docs");

  if (!container) {
    console.error("API docs container not found in template");
    return null;
  }

  // Fix duplicate IDs by adding modal suffix
  container.querySelectorAll("[id]").forEach((el) => {
    el.id = el.id + "-modal";
  });

  // Update aria-controls attributes
  container.querySelectorAll("[aria-controls]").forEach((el) => {
    const controls = el.getAttribute("aria-controls");
    el.setAttribute("aria-controls", controls + "-modal");
  });
  // Reset all toggle buttons to collapsed state
  container.querySelectorAll(".api-toggle").forEach((button) => {
    button.setAttribute("aria-expanded", "false");
    button.classList.remove("open");
    button.setAttribute("aria-label", "Expand details");

    // Reset emoji to collapsed state
    const emojiEl = button.querySelector("span.toggle-emoji");
    if (emojiEl) {
      emojiEl.innerHTML = ""; // Clear any existing content
      emojiEl.textContent = ""; // No emoji
    }
  });

  // Ensure all details sections are collapsed
  container.querySelectorAll(".api-details").forEach((details) => {
    details.classList.remove("open");
    details.style.maxHeight = "0";
  });

  return container;
}

/**
 * Attach event handlers to API documentation elements
 * @param {HTMLElement} root - Root element containing API docs
 */
function attachApiDocsHandlers(root) {
  if (!root) return;
  // Handle toggle buttons
  root.querySelectorAll(".api-toggle").forEach((button) => {
    // Remove any existing event listeners to prevent duplicates
    const newButton = button.cloneNode(true);
    button.parentNode.replaceChild(newButton, button);

    newButton.addEventListener("click", function () {
      const controlsId = this.getAttribute("aria-controls");
      const details = root.querySelector(`#${controlsId}`);
      const isExpanded = this.getAttribute("aria-expanded") === "true";
      const emojiEl = this.querySelector("span.toggle-emoji");

      if (!details) return;

      if (isExpanded) {
        // Collapse
        this.setAttribute("aria-expanded", "false");
        this.classList.remove("open");
        details.classList.remove("open");
        details.style.transition = "max-height 0.3s ease";
        details.style.maxHeight = "0";

        if (emojiEl) {
          emojiEl.innerHTML = ""; // Clear any existing content first
          emojiEl.textContent = ""; // No emoji for collapsed
        }
      } else {
        // Expand
        this.setAttribute("aria-expanded", "true");
        this.classList.add("open");
        details.classList.add("open");
        details.style.transition = "max-height 0.3s ease";
        details.style.maxHeight = details.scrollHeight + "px";

        if (emojiEl) {
          emojiEl.innerHTML = ""; // Clear any existing content first
          emojiEl.textContent = ""; // No emoji for expanded
        }
      }
    });
  });

  // Handle copy buttons
  root.querySelectorAll(".api-copy").forEach((button) => {
    button.addEventListener("click", function () {
      const endpoint = this.closest(".api-endpoint");
      if (!endpoint) return;

      const method =
        endpoint.querySelector(".api-method")?.textContent?.trim() || "";
      const path =
        endpoint.querySelector(".api-path")?.textContent?.trim() || "";
      const details = endpoint.querySelector(".api-details");

      let textToCopy = `${method} ${path}`;
      if (details) {
        textToCopy += "\n\n" + details.textContent.trim();
      }

      navigator.clipboard
        .writeText(textToCopy)
        .then(() => {
          showAlert("API endpoint copied to clipboard", "success");
        })
        .catch(() => {
          showAlert("Failed to copy to clipboard", "error");
        });
    });
  });
}

/**
 * Open API documentation modal
 */
function openApiModal() {
  const modal = document.getElementById("apiModal");
  const modalBody = document.getElementById("apiModalBody");
  const openButton = document.getElementById("openApiModalBtn");

  if (!modal || !modalBody || !openButton) {
    console.error("API modal elements not found");
    return;
  }

  try {
    // Clone and prepare content
    const clonedDocs = cloneApiDocsForModal();
    if (!clonedDocs) {
      throw new Error("Failed to clone API documentation");
    }

    // Clear and populate modal body
    modalBody.innerHTML = "";
    modalBody.appendChild(clonedDocs);

    // Attach event handlers to cloned content
    attachApiDocsHandlers(clonedDocs);

    // Setup modal expand/collapse buttons
    setupModalBulkActions(clonedDocs);

    // Show modal
    modal.removeAttribute("hidden");
    modal.setAttribute("aria-hidden", "false");

    // Add modal-open class for animations
    const modalContent = modal.querySelector(".api-modal-content");
    if (modalContent) {
      modalContent.classList.add("open");
    }

    // Update button state
    openButton.setAttribute("aria-expanded", "true");

    // Prevent body scroll
    document.body.style.overflow = "hidden";

    // Hide main content from screen readers
    const mainContent = document.querySelector(".container");
    if (mainContent) {
      mainContent.setAttribute("aria-hidden", "true");
    }

    // Setup accessibility features
    setupModalAccessibility(modal);

    // Focus management
    focusFirstFocusableElement(modal);

    console.log("API modal opened successfully");
  } catch (error) {
    console.error("Failed to open API modal:", error);
    modalBody.innerHTML =
      '<div class="alert alert-warning">API documentation currently unavailable.</div>';
    modal.removeAttribute("hidden");
    modal.setAttribute("aria-hidden", "false");
  }
}

/**
 * Close API documentation modal
 */
function closeApiModal() {
  const modal = document.getElementById("apiModal");
  const openButton = document.getElementById("openApiModalBtn");

  if (!modal) return;

  // Hide modal with animation
  const modalContent = modal.querySelector(".api-modal-content");
  if (modalContent) {
    modalContent.classList.remove("open");
  }

  // Use timeout to allow animation to complete
  setTimeout(() => {
    modal.setAttribute("hidden", "");
    modal.setAttribute("aria-hidden", "true");

    // Restore body scroll
    document.body.style.overflow = "";

    // Restore main content accessibility
    const mainContent = document.querySelector(".container");
    if (mainContent) {
      mainContent.removeAttribute("aria-hidden");
    }

    // Update button state
    if (openButton) {
      openButton.setAttribute("aria-expanded", "false");
      openButton.focus();
    }

    // Clear modal content to free memory
    const modalBody = document.getElementById("apiModalBody");
    if (modalBody) {
      modalBody.innerHTML = "";
    }

    console.log("API modal closed");
  }, 150); // Match CSS transition duration
}

/**
 * Setup bulk expand/collapse actions for modal
 * @param {HTMLElement} docsContainer - Container with API docs
 */
function setupModalBulkActions(docsContainer) {
  const expandAllBtn = document.getElementById("apiModalExpandAll");
  const collapseAllBtn = document.getElementById("apiModalCollapseAll");

  // Remove existing event listeners to prevent duplicates
  if (expandAllBtn) {
    const newExpandBtn = expandAllBtn.cloneNode(true);
    expandAllBtn.parentNode.replaceChild(newExpandBtn, expandAllBtn);

    newExpandBtn.addEventListener("click", () => {
      docsContainer.querySelectorAll(".api-toggle").forEach((button) => {
        if (button.getAttribute("aria-expanded") !== "true") {
          button.click();
        }
      });
    });
  }

  if (collapseAllBtn) {
    const newCollapseBtn = collapseAllBtn.cloneNode(true);
    collapseAllBtn.parentNode.replaceChild(newCollapseBtn, collapseAllBtn);

    newCollapseBtn.addEventListener("click", () => {
      docsContainer.querySelectorAll(".api-toggle").forEach((button) => {
        if (button.getAttribute("aria-expanded") === "true") {
          button.click();
        }
      });
    });
  }
}

/**
 * Setup accessibility features for modal
 * @param {HTMLElement} modal - Modal element
 */
function setupModalAccessibility(modal) {
  // Focus trap
  setupFocusTrap(modal);

  // Close on overlay click
  const overlay = document.getElementById("apiModalOverlay");
  if (overlay) {
    const newOverlay = overlay.cloneNode(true);
    overlay.parentNode.replaceChild(newOverlay, overlay);
    newOverlay.addEventListener("click", closeApiModal);
  }

  // Close on close button click
  const closeBtn = document.getElementById("closeApiModalBtn");
  if (closeBtn) {
    const newCloseBtn = closeBtn.cloneNode(true);
    closeBtn.parentNode.replaceChild(newCloseBtn, closeBtn);
    newCloseBtn.addEventListener("click", closeApiModal);
  }
}

/**
 * Setup focus trap for modal
 * @param {HTMLElement} modal - Modal element
 */
function setupFocusTrap(modal) {
  const focusableElements = modal.querySelectorAll(
    'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
  );

  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  function handleKeyDown(e) {
    if (e.key === "Escape") {
      closeApiModal();
      return;
    }

    if (e.key === "Tab") {
      if (e.shiftKey) {
        // Shift + Tab
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        // Tab
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    }
  }

  modal.addEventListener("keydown", handleKeyDown);

  // Cleanup when modal closes
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.attributeName === "hidden" && modal.hasAttribute("hidden")) {
        modal.removeEventListener("keydown", handleKeyDown);
        observer.disconnect();
      }
    });
  });
  observer.observe(modal, { attributes: true });
}

/**
 * Focus first focusable element in modal
 * @param {HTMLElement} modal - Modal element
 */
function focusFirstFocusableElement(modal) {
  const closeBtn = modal.querySelector("#closeApiModalBtn");
  if (closeBtn) {
    closeBtn.focus();
    return;
  }

  const firstFocusable = modal.querySelector(
    'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
  );
  if (firstFocusable) {
    firstFocusable.focus();
  }
}

// Setup API modal event listeners
document.addEventListener("DOMContentLoaded", () => {
  const openBtn = document.getElementById("openApiModalBtn");
  const closeBtn = document.getElementById("closeApiModalBtn");

  if (openBtn) {
    openBtn.addEventListener("click", () => {
      console.log("Opening API modal");
      openApiModal();
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener("click", closeApiModal);
  }

  // Setup lightbox close handlers
  const lightboxClose = document.querySelector(".lightbox-close");
  const lightboxOverlay = document.querySelector(".lightbox-overlay");

  if (lightboxClose) {
    lightboxClose.addEventListener("click", closeLightbox);
  }

  if (lightboxOverlay) {
    lightboxOverlay.addEventListener("click", closeLightbox);
  }

  // Close lightbox on ESC key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeLightbox();
    }
  });
});

// ===========================
// ADMIN FUNCTIONS
// ===========================

/**
 * Load Cache Statistics
 */
async function loadCacheStats() {
  const content = document.getElementById("cacheStatsContent");
  const btn = document.getElementById("viewCacheStatsBtn");

  if (!content) return;

  // Toggle visibility
  if (content.style.display === "block") {
    content.style.display = "none";
    return;
  }

  content.innerHTML = '<div class="loading">Loading cache stats...</div>';
  content.style.display = "block";

  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/cache/stats`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const stats = await response.json();

    let html = '<div class="stats-grid">';

    if (stats.enabled === false) {
      html +=
        '<div class="stat-item"><div class="stat-label">Status</div><div class="stat-value warning">Disabled</div></div>';
      html +=
        '<p class="admin-hint">Redis cache is not enabled. Set REDIS_ENABLED=true in .env to use caching.</p>';
    } else {
      html += `<div class="stat-item"><div class="stat-label">Status</div><div class="stat-value success">Enabled</div></div>`;
      html += `<div class="stat-item"><div class="stat-label">Cache Hits</div><div class="stat-value">${
        stats.hits || 0
      }</div></div>`;
      html += `<div class="stat-item"><div class="stat-label">Cache Misses</div><div class="stat-value">${
        stats.misses || 0
      }</div></div>`;

      const totalRequests = (stats.hits || 0) + (stats.misses || 0);
      const hitRate =
        totalRequests > 0 ? ((stats.hits / totalRequests) * 100).toFixed(1) : 0;
      html += `<div class="stat-item"><div class="stat-label">Hit Rate</div><div class="stat-value">${hitRate}%</div></div>`;

      if (stats.memory_usage) {
        html += `<div class="stat-item"><div class="stat-label">Memory Usage</div><div class="stat-value">${formatBytes(
          stats.memory_usage
        )}</div></div>`;
      }

      if (stats.keys_count !== undefined) {
        html += `<div class="stat-item"><div class="stat-label">Cached Keys</div><div class="stat-value">${stats.keys_count}</div></div>`;
      }
    }

    html += "</div>";
    content.innerHTML = html;
  } catch (error) {
    console.error("Error loading cache stats:", error);
    content.innerHTML = `<div class="alert alert-danger">Failed to load cache stats: ${error.message}</div>`;
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Clear Cache
 */
async function clearCache() {
  if (
    !confirm(
      "Are you sure you want to clear all cached data? This will temporarily slow down searches until the cache rebuilds."
    )
  ) {
    return;
  }

  const btn = document.getElementById("clearCacheBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/cache/clear`, {
      method: "POST",
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const result = await response.json();

    if (result.status === "success") {
      showAlert("Cache cleared successfully", "success");
      // Refresh cache stats
      loadCacheStats();
    } else if (result.status === "disabled") {
      showAlert("Cache is not enabled", "warning");
    } else {
      showAlert(result.message || "Unknown response", "info");
    }
  } catch (error) {
    console.error("Error clearing cache:", error);
    showAlert(`Failed to clear cache: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Load Circuit Breaker Status
 */
async function loadCircuitBreakerStatus() {
  const content = document.getElementById("circuitBreakerContent");
  const btn = document.getElementById("viewCircuitBreakerBtn");

  if (!content) return;

  // Toggle visibility
  if (content.style.display === "block") {
    content.style.display = "none";
    return;
  }

  content.innerHTML =
    '<div class="loading">Loading circuit breaker status...</div>';
  content.style.display = "block";

  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/circuit-breaker/status`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    let html = '<div class="circuit-breakers">';

    if (
      data.circuit_breakers &&
      Object.keys(data.circuit_breakers).length > 0
    ) {
      for (const [name, breaker] of Object.entries(data.circuit_breakers)) {
        const stateClass =
          breaker.state === "CLOSED"
            ? "success"
            : breaker.state === "OPEN"
            ? "danger"
            : "warning";

        html += `<div class="circuit-breaker-item">`;
        html += `<div class="cb-header"><strong>${name}</strong> <span class="badge badge-${stateClass}">${breaker.state}</span></div>`;
        html += `<div class="stats-grid">`;
        html += `<div class="stat-item"><div class="stat-label">Failures</div><div class="stat-value">${
          breaker.failure_count || 0
        }</div></div>`;
        html += `<div class="stat-item"><div class="stat-label">Success Count</div><div class="stat-value">${
          breaker.success_count || 0
        }</div></div>`;

        if (breaker.last_failure_time) {
          html += `<div class="stat-item"><div class="stat-label">Last Failure</div><div class="stat-value">${new Date(
            breaker.last_failure_time
          ).toLocaleString()}</div></div>`;
        }

        html += `</div></div>`;
      }
    } else {
      html += '<p class="admin-hint">No circuit breakers configured</p>';
    }

    html += "</div>";
    content.innerHTML = html;
  } catch (error) {
    console.error("Error loading circuit breaker status:", error);
    content.innerHTML = `<div class="alert alert-danger">Failed to load circuit breaker status: ${error.message}</div>`;
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Reset Circuit Breaker
 */
async function resetCircuitBreaker() {
  const serviceName = prompt('Enter service name to reset (e.g., "database"):');

  if (!serviceName || !serviceName.trim()) {
    return;
  }

  const btn = document.getElementById("resetCircuitBreakerBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(
      `${API_BASE_URL}/circuit-breaker/reset/${serviceName.trim()}`,
      {
        method: "POST",
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    const result = await response.json();

    if (result.status === "success") {
      showAlert(`Circuit breaker reset for ${serviceName}`, "success");
      // Refresh circuit breaker status
      loadCircuitBreakerStatus();
    } else {
      showAlert(result.message || "Unknown response", "info");
    }
  } catch (error) {
    console.error("Error resetting circuit breaker:", error);
    showAlert(`Failed to reset circuit breaker: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Enable Debug Mode
 */
function enableDebugMode() {
  console.log("Debug mode enabled");
  document.body.classList.add("debug-mode");
  showAlert("Debug mode enabled - check console for detailed logs", "info");

  // Add debug info to all API calls
  window.DEBUG_MODE = true;
}

/**
 * Disable Debug Mode
 */
function disableDebugMode() {
  console.log("Debug mode disabled");
  document.body.classList.remove("debug-mode");
  showAlert("Debug mode disabled", "info");

  window.DEBUG_MODE = false;
}

/**
 * Stop Auto Refresh
 */
function stopAutoRefresh() {
  if (autoRefreshInterval) {
    clearInterval(autoRefreshInterval);
    autoRefreshInterval = null;
    console.log("Auto-refresh stopped");
  }
}

/**
 * Format Bytes
 */
function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB"];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
}

/**
 * Update Status Indicators
 */
async function updateStatusIndicators() {
  // Update cache status
  try {
    const cacheStats = await fetch(`${API_BASE_URL}/cache/stats`).then((r) =>
      r.json()
    );
    const cacheStatus = document.getElementById("cacheStatus");
    if (cacheStatus) {
      if (cacheStats.enabled === false) {
        cacheStatus.style.color = "var(--text-muted)";
        cacheStatus.title = "Cache Disabled";
      } else {
        cacheStatus.style.color = "var(--success-color)";
        cacheStatus.classList.add("active");
        cacheStatus.title = "Cache Active";
      }
    }
  } catch (error) {
    console.error("Failed to update cache status:", error);
  }

  // Update circuit breaker status
  try {
    const cbData = await fetch(`${API_BASE_URL}/circuit-breaker/status`).then(
      (r) => r.json()
    );
    const circuitStatus = document.getElementById("circuitStatus");
    if (circuitStatus && cbData.circuit_breakers) {
      const breakers = Object.values(cbData.circuit_breakers);
      const hasOpenBreaker = breakers.some((b) => b.state === "OPEN");
      const hasHalfOpenBreaker = breakers.some((b) => b.state === "HALF_OPEN");

      if (hasOpenBreaker) {
        circuitStatus.style.color = "var(--danger-color)";
        circuitStatus.classList.add("active");
        circuitStatus.title = "Circuit Breaker OPEN";
      } else if (hasHalfOpenBreaker) {
        circuitStatus.style.color = "var(--warning-color)";
        circuitStatus.classList.add("active");
        circuitStatus.title = "Circuit Breaker HALF-OPEN";
      } else {
        circuitStatus.style.color = "var(--success-color)";
        circuitStatus.classList.add("active");
        circuitStatus.title = "All Circuit Breakers CLOSED";
      }
    }
  } catch (error) {
    console.error("Failed to update circuit breaker status:", error);
  }
}

/**
 * Perform Full System Check (Quick Action)
 */
async function performSystemCheck() {
  const btn = document.getElementById("fullSystemCheck");
  if (btn) btn.disabled = true;

  showAlert("Running full system check...", "info");

  try {
    // Check health
    const health = await fetch(`${API_BASE_URL}/health`).then((r) => r.json());

    // Check cache
    const cache = await fetch(`${API_BASE_URL}/cache/stats`).then((r) =>
      r.json()
    );

    // Check circuit breakers
    const breakers = await fetch(`${API_BASE_URL}/circuit-breaker/status`).then(
      (r) => r.json()
    );

    let issues = [];

    if (health.status !== "healthy") {
      issues.push("System health check failed");
    }

    if (cache.enabled === false) {
      issues.push("Cache is disabled");
    }

    if (breakers.circuit_breakers) {
      Object.entries(breakers.circuit_breakers).forEach(([name, breaker]) => {
        if (breaker.state !== "CLOSED") {
          issues.push(`Circuit breaker "${name}" is ${breaker.state}`);
        }
      });
    }

    if (issues.length === 0) {
      showAlert("✅ All systems operational!", "success");
    } else {
      showAlert(
        `⚠️ Found ${issues.length} issue(s): ${issues.join(", ")}`,
        "warning"
      );
    }

    // Update status indicators
    updateStatusIndicators();
  } catch (error) {
    console.error("System check failed:", error);
    showAlert(`❌ System check failed: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Clear All Caches (Quick Action)
 */
async function clearAllCachesAction() {
  if (
    !confirm(
      "Clear ALL caches? This will:\n- Clear Redis cache\n- Clear browser cache\n- Temporarily slow down searches\n\nContinue?"
    )
  ) {
    return;
  }

  const btn = document.getElementById("clearAllCaches");
  if (btn) btn.disabled = true;

  try {
    // Clear server cache
    const response = await fetch(`${API_BASE_URL}/cache/clear`, {
      method: "POST",
    });
    const result = await response.json();

    if (result.status === "success") {
      // Clear browser cache
      if ("caches" in window) {
        const cacheNames = await caches.keys();
        await Promise.all(cacheNames.map((name) => caches.delete(name)));
      }

      showAlert("✅ All caches cleared successfully!", "success");

      // Reload cache stats
      loadCacheStats();
    } else {
      showAlert(result.message || "Failed to clear cache", "warning");
    }
  } catch (error) {
    console.error("Failed to clear caches:", error);
    showAlert(`❌ Failed to clear caches: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Database Management Functions
 */
async function loadDatabaseStats() {
  const btn = document.getElementById("viewDbStatsBtn");
  const content = document.getElementById("databaseContent");

  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/database/stats`);
    const result = await response.json();

    if (response.ok && result.success) {
      content.innerHTML = `
                <h4>📊 Database Statistics</h4>
                <pre>${JSON.stringify(result.data, null, 2)}</pre>
            `;
      content.style.display = "block";
      showAlert("Database stats loaded successfully", "success");
    } else {
      content.innerHTML = `<p class="error">❌ ${
        result.message || "Failed to load database stats"
      }</p>`;
      content.style.display = "block";
      showAlert(result.message || "Failed to load database stats", "error");
    }
  } catch (error) {
    console.error("Failed to load database stats:", error);
    content.innerHTML = `<p class="error">❌ Failed to load database stats: ${error.message}</p>`;
    content.style.display = "block";
    showAlert(`Failed to load database stats: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function checkDatabaseHealth() {
  const btn = document.getElementById("checkDbHealthBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/database/health`);
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ Database health check passed!", "success");
      updateStatusIndicator("databaseStatus", "healthy");
    } else {
      showAlert(result.message || "Database health check failed", "error");
      updateStatusIndicator("databaseStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Database health check failed:", error);
    showAlert(`Database health check failed: ${error.message}`, "error");
    updateStatusIndicator("databaseStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function optimizeDatabase() {
  const btn = document.getElementById("optimizeDbBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/database/optimize`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ Database optimization completed!", "success");
    } else {
      showAlert(result.message || "Database optimization failed", "error");
    }
  } catch (error) {
    console.error("Database optimization failed:", error);
    showAlert(`Database optimization failed: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Service Monitoring Functions
 */
async function checkExternalServices() {
  const btn = document.getElementById("checkServicesBtn");
  const content = document.getElementById("servicesContent");

  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/services/check`);
    const result = await response.json();

    if (response.ok && result.success) {
      content.innerHTML = `
                <h4>🔧 External Services Status</h4>
                <pre>${JSON.stringify(result.data, null, 2)}</pre>
            `;
      content.style.display = "block";
      showAlert("External services checked successfully", "success");
      updateStatusIndicator("servicesStatus", "healthy");
    } else {
      content.innerHTML = `<p class="error">❌ ${
        result.message || "Failed to check external services"
      }</p>`;
      content.style.display = "block";
      showAlert(result.message || "Failed to check external services", "error");
      updateStatusIndicator("servicesStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to check external services:", error);
    content.innerHTML = `<p class="error">❌ Failed to check external services: ${error.message}</p>`;
    content.style.display = "block";
    showAlert(`Failed to check external services: ${error.message}`, "error");
    updateStatusIndicator("servicesStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function restartAllServices() {
  const btn = document.getElementById("restartServicesBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/services/restart`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ All external services restarted successfully!", "success");
      updateStatusIndicator("servicesStatus", "healthy");
    } else {
      showAlert(result.message || "Failed to restart services", "error");
      updateStatusIndicator("servicesStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to restart services:", error);
    showAlert(`Failed to restart services: ${error.message}`, "error");
    updateStatusIndicator("servicesStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Security & Audit Functions
 */
async function loadSecurityLogs() {
  const btn = document.getElementById("viewSecurityLogsBtn");
  const content = document.getElementById("securityContent");

  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/security/logs`);
    const result = await response.json();

    if (response.ok && result.success) {
      content.innerHTML = `
                <h4>🔒 Security Audit Logs</h4>
                <pre>${JSON.stringify(result.data, null, 2)}</pre>
            `;
      content.style.display = "block";
      showAlert("Security logs loaded successfully", "success");
    } else {
      content.innerHTML = `<p class="error">❌ ${
        result.message || "Failed to load security logs"
      }</p>`;
      content.style.display = "block";
      showAlert(result.message || "Failed to load security logs", "error");
    }
  } catch (error) {
    console.error("Failed to load security logs:", error);
    content.innerHTML = `<p class="error">❌ Failed to load security logs: ${error.message}</p>`;
    content.style.display = "block";
    showAlert(`Failed to load security logs: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function runSecurityScan() {
  const btn = document.getElementById("runSecurityScanBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/security/scan`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ Security scan completed successfully!", "success");
      updateStatusIndicator("securityStatus", "healthy");
    } else {
      showAlert(result.message || "Security scan failed", "error");
      updateStatusIndicator("securityStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Security scan failed:", error);
    showAlert(`Security scan failed: ${error.message}`, "error");
    updateStatusIndicator("securityStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Enhanced Quick Actions Functions
 */
async function performSystemBackup() {
  const btn = document.getElementById("backupSystem");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/backup`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ System backup completed successfully!", "success");
    } else {
      showAlert(result.message || "System backup failed", "error");
    }
  } catch (error) {
    console.error("System backup failed:", error);
    showAlert(`System backup failed: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function runPerformanceTest() {
  const btn = document.getElementById("performanceTest");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/performance/test`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ Performance test completed successfully!", "success");
    } else {
      showAlert(result.message || "Performance test failed", "error");
    }
  } catch (error) {
    console.error("Performance test failed:", error);
    showAlert(`Performance test failed: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function restartApplication() {
  const btn = document.getElementById("restartApp");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/restart`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ Application restart initiated successfully!", "success");
      // Auto-refresh will show the restart status
    } else {
      showAlert(result.message || "Application restart failed", "error");
    }
  } catch (error) {
    console.error("Application restart failed:", error);
    showAlert(`Application restart failed: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function emergencyStopApplication() {
  const btn = document.getElementById("emergencyStop");
  if (btn) btn.disabled = true;

  // Show confirmation dialog
  if (
    !confirm(
      "⚠️ EMERGENCY STOP: This will immediately stop all services. Are you sure?"
    )
  ) {
    if (btn) btn.disabled = false;
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/admin/emergency-stop`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("🛑 Emergency stop executed successfully!", "warning");
    } else {
      showAlert(result.message || "Emergency stop failed", "error");
    }
  } catch (error) {
    console.error("Emergency stop failed:", error);
    showAlert(`Emergency stop failed: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Update Status Indicator Helper
 */
function updateStatusIndicator(elementId, status) {
  const indicator = document.getElementById(elementId);
  if (indicator) {
    indicator.className = `section-status ${status}`;
  }
}

/**
 * System Logs Functions
 */
async function viewSystemLogs() {
  const btn = document.getElementById("viewSystemLogsBtn");
  const content = document.getElementById("logsContent");

  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/logs?limit=100`);
    const result = await response.json();

    if (response.ok && result.success) {
      const logsHtml = result.data.logs
        .map(
          (log) =>
            `<div class="log-entry log-${log.level.toLowerCase()}">
                    <span class="log-timestamp">${new Date(
                      log.timestamp
                    ).toLocaleString()}</span>
                    <span class="log-level">[${log.level}]</span>
                    <span class="log-message">${log.message}</span>
                </div>`
        )
        .join("");

      content.innerHTML = `
                <h4>📋 System Logs (Last 100 entries)</h4>
                <div class="logs-container">${logsHtml}</div>
            `;
      content.style.display = "block";
      showAlert("System logs loaded successfully", "success");
      updateStatusIndicator("logsStatus", "healthy");
    } else {
      content.innerHTML = `<p class="error">❌ ${
        result.message || "Failed to load system logs"
      }</p>`;
      content.style.display = "block";
      showAlert(result.message || "Failed to load system logs", "error");
      updateStatusIndicator("logsStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to load system logs:", error);
    content.innerHTML = `<p class="error">❌ Failed to load system logs: ${error.message}</p>`;
    content.style.display = "block";
    showAlert(`Failed to load system logs: ${error.message}`, "error");
    updateStatusIndicator("logsStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function downloadSystemLogs() {
  const btn = document.getElementById("downloadLogsBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/logs/download`);

    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `system-logs-${new Date().toISOString().split("T")[0]}.log`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      showAlert("✅ System logs downloaded successfully!", "success");
    } else {
      showAlert("Failed to download system logs", "error");
    }
  } catch (error) {
    console.error("Failed to download logs:", error);
    showAlert(`Failed to download logs: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function clearOldLogs() {
  const btn = document.getElementById("clearLogsBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/logs/clear`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ Old logs cleared successfully!", "success");
      updateStatusIndicator("logsStatus", "healthy");
    } else {
      showAlert(result.message || "Failed to clear old logs", "error");
      updateStatusIndicator("logsStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to clear old logs:", error);
    showAlert(`Failed to clear old logs: ${error.message}`, "error");
    updateStatusIndicator("logsStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Configuration Management Functions
 */
async function viewSystemConfig() {
  const btn = document.getElementById("viewConfigBtn");
  const content = document.getElementById("configContent");

  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/config`);
    const result = await response.json();

    if (response.ok && result.success) {
      const configHtml = Object.entries(result.data)
        .map(
          ([key, value]) =>
            `<div class="config-item">
                    <span class="config-key">${key}:</span>
                    <span class="config-value">${JSON.stringify(value)}</span>
                </div>`
        )
        .join("");

      content.innerHTML = `
                <h4>⚙️ System Configuration</h4>
                <div class="config-list">${configHtml}</div>
            `;
      content.style.display = "block";
      showAlert("System configuration loaded successfully", "success");
      updateStatusIndicator("configStatus", "healthy");
    } else {
      content.innerHTML = `<p class="error">❌ ${
        result.message || "Failed to load system configuration"
      }</p>`;
      content.style.display = "block";
      showAlert(
        result.message || "Failed to load system configuration",
        "error"
      );
      updateStatusIndicator("configStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to load system config:", error);
    content.innerHTML = `<p class="error">❌ Failed to load system configuration: ${error.message}</p>`;
    content.style.display = "block";
    showAlert(`Failed to load system configuration: ${error.message}`, "error");
    updateStatusIndicator("configStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function editSystemConfig() {
  const content = document.getElementById("configContent");

  content.innerHTML = `
        <h4>✏️ Edit System Configuration</h4>
        <div class="config-editor">
            <textarea id="configEditor" rows="20" placeholder="Enter configuration as JSON..."></textarea>
            <div class="editor-actions">
                <button id="saveConfigBtn" class="btn btn-primary btn-small">💾 Save Configuration</button>
                <button id="cancelConfigBtn" class="btn btn-outline btn-small">❌ Cancel</button>
            </div>
        </div>
    `;
  content.style.display = "block";

  // Load current config into editor
  try {
    const response = await fetch(`${API_BASE_URL}/admin/config`);
    const result = await response.json();
    if (response.ok && result.success) {
      document.getElementById("configEditor").value = JSON.stringify(
        result.data,
        null,
        2
      );
    }
  } catch (error) {
    console.error("Failed to load config for editing:", error);
  }

  // Setup save/cancel handlers
  document
    .getElementById("saveConfigBtn")
    .addEventListener("click", saveSystemConfig);
  document
    .getElementById("cancelConfigBtn")
    .addEventListener("click", () => viewSystemConfig());
}

async function saveSystemConfig() {
  const editor = document.getElementById("configEditor");
  const btn = document.getElementById("saveConfigBtn");

  if (!editor || !editor.value.trim()) {
    showAlert("Configuration cannot be empty", "error");
    return;
  }

  if (btn) btn.disabled = true;

  try {
    const configData = JSON.parse(editor.value);
    const response = await fetch(`${API_BASE_URL}/admin/config`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(configData),
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ Configuration saved successfully!", "success");
      updateStatusIndicator("configStatus", "healthy");
      viewSystemConfig(); // Reload view
    } else {
      showAlert(result.message || "Failed to save configuration", "error");
      updateStatusIndicator("configStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to save config:", error);
    showAlert(`Failed to save configuration: ${error.message}`, "error");
    updateStatusIndicator("configStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function reloadSystemConfig() {
  const btn = document.getElementById("reloadConfigBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/config/reload`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ Configuration reloaded successfully!", "success");
      updateStatusIndicator("configStatus", "healthy");
    } else {
      showAlert(result.message || "Failed to reload configuration", "error");
      updateStatusIndicator("configStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to reload config:", error);
    showAlert(`Failed to reload configuration: ${error.message}`, "error");
    updateStatusIndicator("configStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Alert Management Functions
 */
async function viewSystemAlerts() {
  const btn = document.getElementById("viewAlertsBtn");
  const content = document.getElementById("alertsContent");

  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/alerts`);
    const result = await response.json();

    if (response.ok && result.success) {
      const alertsHtml = result.data.alerts
        .map(
          (alert) =>
            `<div class="alert-item alert-${alert.severity.toLowerCase()}">
                    <span class="alert-time">${new Date(
                      alert.timestamp
                    ).toLocaleString()}</span>
                    <span class="alert-severity">[${alert.severity}]</span>
                    <span class="alert-message">${alert.message}</span>
                    <span class="alert-status">${alert.status}</span>
                </div>`
        )
        .join("");

      content.innerHTML = `
                <h4>🚨 System Alerts</h4>
                <div class="alerts-container">${
                  alertsHtml || "<p>No active alerts</p>"
                }</div>
            `;
      content.style.display = "block";
      showAlert("System alerts loaded successfully", "success");
      updateStatusIndicator("alertsStatus", "healthy");
    } else {
      content.innerHTML = `<p class="error">❌ ${
        result.message || "Failed to load system alerts"
      }</p>`;
      content.style.display = "block";
      showAlert(result.message || "Failed to load system alerts", "error");
      updateStatusIndicator("alertsStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to load system alerts:", error);
    content.innerHTML = `<p class="error">❌ Failed to load system alerts: ${error.message}</p>`;
    content.style.display = "block";
    showAlert(`Failed to load system alerts: ${error.message}`, "error");
    updateStatusIndicator("alertsStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function configureSystemAlerts() {
  const content = document.getElementById("alertsContent");

  content.innerHTML = `
        <h4>⚙️ Configure Alert Settings</h4>
        <div class="alerts-config">
            <div class="config-section">
                <h5>Email Notifications</h5>
                <label><input type="checkbox" id="emailAlerts" checked> Enable email alerts</label>
                <input type="email" id="alertEmail" placeholder="alerts@example.com" class="form-control">
            </div>
            <div class="config-section">
                <h5>Alert Thresholds</h5>
                <label>CPU Usage (%): <input type="number" id="cpuThreshold" value="80" min="1" max="100"></label>
                <label>Memory Usage (%): <input type="number" id="memoryThreshold" value="85" min="1" max="100"></label>
                <label>Disk Usage (%): <input type="number" id="diskThreshold" value="90" min="1" max="100"></label>
            </div>
            <div class="editor-actions">
                <button id="saveAlertConfigBtn" class="btn btn-primary btn-small">💾 Save Settings</button>
                <button id="cancelAlertConfigBtn" class="btn btn-outline btn-small">❌ Cancel</button>
            </div>
        </div>
    `;
  content.style.display = "block";

  document
    .getElementById("saveAlertConfigBtn")
    .addEventListener("click", saveAlertConfiguration);
  document
    .getElementById("cancelAlertConfigBtn")
    .addEventListener("click", () => viewSystemAlerts());
}

async function saveAlertConfiguration() {
  const btn = document.getElementById("saveAlertConfigBtn");
  if (btn) btn.disabled = true;

  const config = {
    emailAlerts: document.getElementById("emailAlerts").checked,
    alertEmail: document.getElementById("alertEmail").value,
    thresholds: {
      cpu: parseInt(document.getElementById("cpuThreshold").value),
      memory: parseInt(document.getElementById("memoryThreshold").value),
      disk: parseInt(document.getElementById("diskThreshold").value),
    },
  };

  try {
    const response = await fetch(`${API_BASE_URL}/admin/alerts/config`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ Alert configuration saved successfully!", "success");
      updateStatusIndicator("alertsStatus", "healthy");
      viewSystemAlerts(); // Reload view
    } else {
      showAlert(
        result.message || "Failed to save alert configuration",
        "error"
      );
      updateStatusIndicator("alertsStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to save alert config:", error);
    showAlert(`Failed to save alert configuration: ${error.message}`, "error");
    updateStatusIndicator("alertsStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function testSystemAlerts() {
  const btn = document.getElementById("testAlertsBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/alerts/test`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ Test alert sent successfully!", "success");
    } else {
      showAlert(result.message || "Failed to send test alert", "error");
    }
  } catch (error) {
    console.error("Failed to send test alert:", error);
    showAlert(`Failed to send test alert: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * API Controls Functions
 */
async function viewApiStatistics() {
  const btn = document.getElementById("viewApiStatsBtn");
  const content = document.getElementById("apiContent");

  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/api/stats`);
    const result = await response.json();

    if (response.ok && result.success) {
      content.innerHTML = `
                <h4>📊 API Statistics</h4>
                <div class="api-stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">${
                          result.data.totalRequests || 0
                        }</div>
                        <div class="stat-label">Total Requests</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${
                          result.data.avgResponseTime || 0
                        }ms</div>
                        <div class="stat-label">Avg Response Time</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${
                          result.data.errorRate || 0
                        }%</div>
                        <div class="stat-label">Error Rate</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${
                          result.data.activeConnections || 0
                        }</div>
                        <div class="stat-label">Active Connections</div>
                    </div>
                </div>
            `;
      content.style.display = "block";
      showAlert("API statistics loaded successfully", "success");
      updateStatusIndicator("apiStatus", "healthy");
    } else {
      content.innerHTML = `<p class="error">❌ ${
        result.message || "Failed to load API statistics"
      }</p>`;
      content.style.display = "block";
      showAlert(result.message || "Failed to load API statistics", "error");
      updateStatusIndicator("apiStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to load API stats:", error);
    content.innerHTML = `<p class="error">❌ Failed to load API statistics: ${error.message}</p>`;
    content.style.display = "block";
    showAlert(`Failed to load API statistics: ${error.message}`, "error");
    updateStatusIndicator("apiStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function manageRateLimits() {
  const content = document.getElementById("apiContent");

  content.innerHTML = `
        <h4>⏱️ Rate Limiting Configuration</h4>
        <div class="rate-limit-config">
            <div class="config-section">
                <h5>Global Limits</h5>
                <label>Requests per minute: <input type="number" id="globalRpm" value="1000" min="1"></label>
                <label>Requests per hour: <input type="number" id="globalRph" value="10000" min="1"></label>
            </div>
            <div class="config-section">
                <h5>Per-IP Limits</h5>
                <label>Requests per minute: <input type="number" id="ipRpm" value="60" min="1"></label>
                <label>Requests per hour: <input type="number" id="ipRph" value="1000" min="1"></label>
            </div>
            <div class="editor-actions">
                <button id="saveRateLimitsBtn" class="btn btn-primary btn-small">💾 Save Limits</button>
                <button id="cancelRateLimitsBtn" class="btn btn-outline btn-small">❌ Cancel</button>
            </div>
        </div>
    `;
  content.style.display = "block";

  document
    .getElementById("saveRateLimitsBtn")
    .addEventListener("click", saveRateLimits);
  document
    .getElementById("cancelRateLimitsBtn")
    .addEventListener("click", () => viewApiStatistics());
}

async function saveRateLimits() {
  const btn = document.getElementById("saveRateLimitsBtn");
  if (btn) btn.disabled = true;

  const limits = {
    global: {
      rpm: parseInt(document.getElementById("globalRpm").value),
      rph: parseInt(document.getElementById("globalRph").value),
    },
    perIp: {
      rpm: parseInt(document.getElementById("ipRpm").value),
      rph: parseInt(document.getElementById("ipRph").value),
    },
  };

  try {
    const response = await fetch(`${API_BASE_URL}/admin/api/rate-limits`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(limits),
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ Rate limits updated successfully!", "success");
      updateStatusIndicator("apiStatus", "healthy");
      viewApiStatistics(); // Reload view
    } else {
      showAlert(result.message || "Failed to update rate limits", "error");
      updateStatusIndicator("apiStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to save rate limits:", error);
    showAlert(`Failed to update rate limits: ${error.message}`, "error");
    updateStatusIndicator("apiStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function viewApiKeys() {
  const btn = document.getElementById("viewApiKeysBtn");
  const content = document.getElementById("apiContent");

  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/api/keys`);
    const result = await response.json();

    if (response.ok && result.success) {
      const keysHtml = result.data.keys
        .map(
          (key) =>
            `<div class="api-key-item">
                    <span class="key-name">${key.name}</span>
                    <span class="key-value">${key.maskedKey}</span>
                    <span class="key-status ${
                      key.active ? "active" : "inactive"
                    }">${key.active ? "Active" : "Inactive"}</span>
                    <button class="btn btn-small" onclick="toggleApiKey('${
                      key.id
                    }')">${key.active ? "Deactivate" : "Activate"}</button>
                </div>`
        )
        .join("");

      content.innerHTML = `
                <h4>🔑 API Keys Management</h4>
                <div class="api-keys-list">${keysHtml}</div>
                <button id="generateApiKeyBtn" class="btn btn-primary btn-small" style="margin-top: 1rem;">➕ Generate New Key</button>
            `;
      content.style.display = "block";

      document
        .getElementById("generateApiKeyBtn")
        .addEventListener("click", generateApiKey);

      showAlert("API keys loaded successfully", "success");
      updateStatusIndicator("apiStatus", "healthy");
    } else {
      content.innerHTML = `<p class="error">❌ ${
        result.message || "Failed to load API keys"
      }</p>`;
      content.style.display = "block";
      showAlert(result.message || "Failed to load API keys", "error");
      updateStatusIndicator("apiStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to load API keys:", error);
    content.innerHTML = `<p class="error">❌ Failed to load API keys: ${error.message}</p>`;
    content.style.display = "block";
    showAlert(`Failed to load API keys: ${error.message}`, "error");
    updateStatusIndicator("apiStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function generateApiKey() {
  try {
    const keyName = prompt("Enter a name for the new API key:");
    if (!keyName) return;

    const response = await fetch(`${API_BASE_URL}/admin/api/keys`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: keyName }),
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert(`✅ API key generated: ${result.data.key}`, "success");
      viewApiKeys(); // Reload list
    } else {
      showAlert(result.message || "Failed to generate API key", "error");
    }
  } catch (error) {
    console.error("Failed to generate API key:", error);
    showAlert(`Failed to generate API key: ${error.message}`, "error");
  }
}

async function toggleApiKey(keyId) {
  try {
    const response = await fetch(
      `${API_BASE_URL}/admin/api/keys/${keyId}/toggle`,
      { method: "POST" }
    );
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ API key status updated!", "success");
      viewApiKeys(); // Reload list
    } else {
      showAlert(result.message || "Failed to update API key", "error");
    }
  } catch (error) {
    console.error("Failed to toggle API key:", error);
    showAlert(`Failed to update API key: ${error.message}`, "error");
  }
}

/**
 * Performance Tuning Functions
 */
async function runPerformanceAnalysis() {
  const btn = document.getElementById("runPerformanceAnalysisBtn");
  const content = document.getElementById("performanceContent");

  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/performance/analyze`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      content.innerHTML = `
                <h4>📈 Performance Analysis Results</h4>
                <div class="performance-results">
                    <div class="result-item">
                        <span class="result-label">Bottlenecks Found:</span>
                        <span class="result-value">${
                          result.data.bottlenecks || 0
                        }</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">Memory Efficiency:</span>
                        <span class="result-value">${
                          result.data.memoryEfficiency || 0
                        }%</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">CPU Utilization:</span>
                        <span class="result-value">${
                          result.data.cpuUtilization || 0
                        }%</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">Recommendations:</span>
                        <span class="result-value">${
                          result.data.recommendations || "None"
                        }</span>
                    </div>
                </div>
            `;
      content.style.display = "block";
      showAlert("Performance analysis completed successfully", "success");
      updateStatusIndicator("performanceStatus", "healthy");
    } else {
      content.innerHTML = `<p class="error">❌ ${
        result.message || "Failed to run performance analysis"
      }</p>`;
      content.style.display = "block";
      showAlert(
        result.message || "Failed to run performance analysis",
        "error"
      );
      updateStatusIndicator("performanceStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to run performance analysis:", error);
    content.innerHTML = `<p class="error">❌ Failed to run performance analysis: ${error.message}</p>`;
    content.style.display = "block";
    showAlert(`Failed to run performance analysis: ${error.message}`, "error");
    updateStatusIndicator("performanceStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function optimizeSystemPerformance() {
  const btn = document.getElementById("optimizePerformanceBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/performance/optimize`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ System performance optimized successfully!", "success");
      updateStatusIndicator("performanceStatus", "healthy");
    } else {
      showAlert(result.message || "Failed to optimize performance", "error");
      updateStatusIndicator("performanceStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to optimize performance:", error);
    showAlert(`Failed to optimize performance: ${error.message}`, "error");
    updateStatusIndicator("performanceStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function performMemoryCleanup() {
  const btn = document.getElementById("memoryCleanupBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(
      `${API_BASE_URL}/admin/performance/memory-cleanup`,
      { method: "POST" }
    );
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert(
        `✅ Memory cleanup completed! Freed ${result.data.freedMemory || 0} MB`,
        "success"
      );
      updateStatusIndicator("performanceStatus", "healthy");
    } else {
      showAlert(result.message || "Failed to perform memory cleanup", "error");
      updateStatusIndicator("performanceStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to perform memory cleanup:", error);
    showAlert(`Failed to perform memory cleanup: ${error.message}`, "error");
    updateStatusIndicator("performanceStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Backup Management Functions
 */
async function createSystemBackup() {
  const btn = document.getElementById("createBackupBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/backup/create`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert(
        `✅ Backup created successfully: ${result.data.backupId}`,
        "success"
      );
      updateStatusIndicator("backupStatus", "healthy");
      listSystemBackups(); // Refresh list
    } else {
      showAlert(result.message || "Failed to create backup", "error");
      updateStatusIndicator("backupStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to create backup:", error);
    showAlert(`Failed to create backup: ${error.message}`, "error");
    updateStatusIndicator("backupStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function listSystemBackups() {
  const btn = document.getElementById("listBackupsBtn");
  const content = document.getElementById("backupContent");

  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/backup/list`);
    const result = await response.json();

    if (response.ok && result.success) {
      const backupsHtml = result.data.backups
        .map(
          (backup) =>
            `<div class="backup-item">
                    <span class="backup-name">${backup.name}</span>
                    <span class="backup-size">${backup.size}</span>
                    <span class="backup-date">${new Date(
                      backup.createdAt
                    ).toLocaleString()}</span>
                    <button class="btn btn-small" onclick="restoreBackup('${
                      backup.id
                    }')">Restore</button>
                    <button class="btn btn-small btn-danger" onclick="deleteBackup('${
                      backup.id
                    }')">Delete</button>
                </div>`
        )
        .join("");

      content.innerHTML = `
                <h4>💾 System Backups</h4>
                <div class="backups-list">${
                  backupsHtml || "<p>No backups found</p>"
                }</div>
            `;
      content.style.display = "block";
      showAlert("Backups list loaded successfully", "success");
      updateStatusIndicator("backupStatus", "healthy");
    } else {
      content.innerHTML = `<p class="error">❌ ${
        result.message || "Failed to load backups list"
      }</p>`;
      content.style.display = "block";
      showAlert(result.message || "Failed to load backups list", "error");
      updateStatusIndicator("backupStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to load backups list:", error);
    content.innerHTML = `<p class="error">❌ Failed to load backups list: ${error.message}</p>`;
    content.style.display = "block";
    showAlert(`Failed to load backups list: ${error.message}`, "error");
    updateStatusIndicator("backupStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function restoreSystemBackup() {
  const backupId = prompt("Enter backup ID to restore:");
  if (!backupId) return;

  if (
    !confirm(
      `⚠️ This will restore the system to backup: ${backupId}. Continue?`
    )
  )
    return;

  try {
    const response = await fetch(
      `${API_BASE_URL}/admin/backup/restore/${backupId}`,
      { method: "POST" }
    );
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ System backup restored successfully!", "success");
      updateStatusIndicator("backupStatus", "healthy");
    } else {
      showAlert(result.message || "Failed to restore backup", "error");
      updateStatusIndicator("backupStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to restore backup:", error);
    showAlert(`Failed to restore backup: ${error.message}`, "error");
    updateStatusIndicator("backupStatus", "unhealthy");
  }
}

/**
 * Maintenance Mode Functions
 */
async function toggleMaintenanceMode() {
  const btn = document.getElementById("toggleMaintenanceBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/maintenance/toggle`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      const status = result.data.enabled ? "enabled" : "disabled";
      showAlert(
        `✅ Maintenance mode ${status}!`,
        result.data.enabled ? "warning" : "success"
      );
      updateStatusIndicator(
        "maintenanceStatus",
        result.data.enabled ? "degraded" : "healthy"
      );
    } else {
      showAlert(result.message || "Failed to toggle maintenance mode", "error");
      updateStatusIndicator("maintenanceStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to toggle maintenance mode:", error);
    showAlert(`Failed to toggle maintenance mode: ${error.message}`, "error");
    updateStatusIndicator("maintenanceStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function scheduleMaintenance() {
  const content = document.getElementById("maintenanceContent");

  content.innerHTML = `
        <h4>📅 Schedule Maintenance</h4>
        <div class="maintenance-scheduler">
            <div class="config-section">
                <label>Start Time: <input type="datetime-local" id="maintenanceStart"></label>
                <label>Duration (minutes): <input type="number" id="maintenanceDuration" value="60" min="1"></label>
                <label><input type="checkbox" id="maintenanceNotify"> Notify users before maintenance</label>
            </div>
            <div class="editor-actions">
                <button id="scheduleMaintenanceBtn" class="btn btn-primary btn-small">📅 Schedule</button>
                <button id="cancelMaintenanceBtn" class="btn btn-outline btn-small">❌ Cancel</button>
            </div>
        </div>
    `;
  content.style.display = "block";

  document
    .getElementById("scheduleMaintenanceBtn")
    .addEventListener("click", saveMaintenanceSchedule);
  document
    .getElementById("cancelMaintenanceBtn")
    .addEventListener("click", () => checkMaintenanceStatus());
}

async function saveMaintenanceSchedule() {
  const btn = document.getElementById("scheduleMaintenanceBtn");
  if (btn) btn.disabled = true;

  const schedule = {
    startTime: document.getElementById("maintenanceStart").value,
    duration: parseInt(document.getElementById("maintenanceDuration").value),
    notifyUsers: document.getElementById("maintenanceNotify").checked,
  };

  if (!schedule.startTime) {
    showAlert("Please select a start time", "error");
    if (btn) btn.disabled = false;
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/admin/maintenance/schedule`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(schedule),
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ Maintenance scheduled successfully!", "success");
      updateStatusIndicator("maintenanceStatus", "healthy");
      checkMaintenanceStatus(); // Reload view
    } else {
      showAlert(result.message || "Failed to schedule maintenance", "error");
      updateStatusIndicator("maintenanceStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to schedule maintenance:", error);
    showAlert(`Failed to schedule maintenance: ${error.message}`, "error");
    updateStatusIndicator("maintenanceStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function checkMaintenanceStatus() {
  const btn = document.getElementById("checkMaintenanceStatusBtn");
  const content = document.getElementById("maintenanceContent");

  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/maintenance/status`);
    const result = await response.json();

    if (response.ok && result.success) {
      content.innerHTML = `
                <h4>🔧 Maintenance Status</h4>
                <div class="maintenance-status">
                    <div class="status-item">
                        <span class="status-label">Current Mode:</span>
                        <span class="status-value ${
                          result.data.enabled
                            ? "maintenance-active"
                            : "maintenance-inactive"
                        }">
                            ${
                              result.data.enabled
                                ? "MAINTENANCE ACTIVE"
                                : "Normal Operation"
                            }
                        </span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">Next Scheduled:</span>
                        <span class="status-value">${
                          result.data.nextScheduled
                            ? new Date(
                                result.data.nextScheduled
                              ).toLocaleString()
                            : "None"
                        }</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">Active Sessions:</span>
                        <span class="status-value">${
                          result.data.activeSessions || 0
                        }</span>
                    </div>
                </div>
            `;
      content.style.display = "block";
      showAlert("Maintenance status loaded successfully", "success");
      updateStatusIndicator(
        "maintenanceStatus",
        result.data.enabled ? "degraded" : "healthy"
      );
    } else {
      content.innerHTML = `<p class="error">❌ ${
        result.message || "Failed to load maintenance status"
      }</p>`;
      content.style.display = "block";
      showAlert(result.message || "Failed to load maintenance status", "error");
      updateStatusIndicator("maintenanceStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to load maintenance status:", error);
    content.innerHTML = `<p class="error">❌ Failed to load maintenance status: ${error.message}</p>`;
    content.style.display = "block";
    showAlert(`Failed to load maintenance status: ${error.message}`, "error");
    updateStatusIndicator("maintenanceStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Missing Functions Implementation
 */
async function deleteBackup(backupId) {
  if (!confirm(`⚠️ Are you sure you want to delete backup: ${backupId}?`))
    return;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/backup/${backupId}`, {
      method: "DELETE",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ Backup deleted successfully!", "success");
      listSystemBackups(); // Refresh list
    } else {
      showAlert(result.message || "Failed to delete backup", "error");
    }
  } catch (error) {
    console.error("Failed to delete backup:", error);
    showAlert(`Failed to delete backup: ${error.message}`, "error");
  }
}

async function restoreBackup(backupId) {
  if (
    !confirm(
      `⚠️ This will restore the system to backup: ${backupId}. Continue?`
    )
  )
    return;

  try {
    const response = await fetch(
      `${API_BASE_URL}/admin/backup/restore/${backupId}`,
      { method: "POST" }
    );
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ System backup restored successfully!", "success");
      updateStatusIndicator("backupStatus", "healthy");
    } else {
      showAlert(result.message || "Failed to restore backup", "error");
      updateStatusIndicator("backupStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to restore backup:", error);
    showAlert(`Failed to restore backup: ${error.message}`, "error");
    updateStatusIndicator("backupStatus", "unhealthy");
  }
}

/**
 * Additional Admin Functions
 */
async function viewCacheStats() {
  const btn = document.getElementById("viewCacheStatsBtn");
  const content = document.getElementById("cacheStatsContent");

  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/cache/stats`);
    const result = await response.json();

    if (response.ok && result.success) {
      content.innerHTML = `
                <h4>💾 Cache Statistics</h4>
                <div class="cache-stats">
                    <div class="stat-item">
                        <span class="stat-label">Total Keys:</span>
                        <span class="stat-value">${
                          result.data.totalKeys || 0
                        }</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Memory Used:</span>
                        <span class="stat-value">${
                          result.data.memoryUsed || "0MB"
                        }</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Hit Rate:</span>
                        <span class="stat-value">${
                          result.data.hitRate || 0
                        }%</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Evictions:</span>
                        <span class="stat-value">${
                          result.data.evictions || 0
                        }</span>
                    </div>
                </div>
            `;
      content.style.display = "block";
      showAlert("Cache statistics loaded successfully", "success");
      updateStatusIndicator("cacheStatus", "healthy");
    } else {
      content.innerHTML = `<p class="error">❌ ${
        result.message || "Failed to load cache statistics"
      }</p>`;
      content.style.display = "block";
      showAlert(result.message || "Failed to load cache statistics", "error");
      updateStatusIndicator("cacheStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to load cache stats:", error);
    content.innerHTML = `<p class="error">❌ Failed to load cache statistics: ${error.message}</p>`;
    content.style.display = "block";
    showAlert(`Failed to load cache statistics: ${error.message}`, "error");
    updateStatusIndicator("cacheStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function clearCache() {
  const btn = document.getElementById("clearCacheBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/cache/clear`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ Cache cleared successfully!", "success");
      updateStatusIndicator("cacheStatus", "healthy");
    } else {
      showAlert(result.message || "Failed to clear cache", "error");
      updateStatusIndicator("cacheStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to clear cache:", error);
    showAlert(`Failed to clear cache: ${error.message}`, "error");
    updateStatusIndicator("cacheStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function viewCircuitBreaker() {
  const btn = document.getElementById("viewCircuitBreakerBtn");
  const content = document.getElementById("circuitBreakerContent");

  if (btn) btn.disabled = true;

  try {
    const response = await fetch(
      `${API_BASE_URL}/admin/circuit-breaker/status`
    );
    const result = await response.json();

    if (response.ok && result.success) {
      content.innerHTML = `
                <h4>🔌 Circuit Breaker Status</h4>
                <div class="circuit-status">
                    <div class="status-item">
                        <span class="status-label">State:</span>
                        <span class="status-value ${result.data.state.toLowerCase()}">${
        result.data.state
      }</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">Failure Count:</span>
                        <span class="status-value">${
                          result.data.failureCount || 0
                        }</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">Success Count:</span>
                        <span class="status-value">${
                          result.data.successCount || 0
                        }</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">Last Failure:</span>
                        <span class="status-value">${
                          result.data.lastFailure
                            ? new Date(result.data.lastFailure).toLocaleString()
                            : "None"
                        }</span>
                    </div>
                </div>
            `;
      content.style.display = "block";
      showAlert("Circuit breaker status loaded successfully", "success");
      updateStatusIndicator(
        "circuitStatus",
        result.data.state === "CLOSED" ? "healthy" : "degraded"
      );
    } else {
      content.innerHTML = `<p class="error">❌ ${
        result.message || "Failed to load circuit breaker status"
      }</p>`;
      content.style.display = "block";
      showAlert(
        result.message || "Failed to load circuit breaker status",
        "error"
      );
      updateStatusIndicator("circuitStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to load circuit breaker status:", error);
    content.innerHTML = `<p class="error">❌ Failed to load circuit breaker status: ${error.message}</p>`;
    content.style.display = "block";
    showAlert(
      `Failed to load circuit breaker status: ${error.message}`,
      "error"
    );
    updateStatusIndicator("circuitStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function resetCircuitBreaker() {
  const btn = document.getElementById("resetCircuitBreakerBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(
      `${API_BASE_URL}/admin/circuit-breaker/reset`,
      { method: "POST" }
    );
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ Circuit breaker reset successfully!", "success");
      updateStatusIndicator("circuitStatus", "healthy");
    } else {
      showAlert(result.message || "Failed to reset circuit breaker", "error");
      updateStatusIndicator("circuitStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to reset circuit breaker:", error);
    showAlert(`Failed to reset circuit breaker: ${error.message}`, "error");
    updateStatusIndicator("circuitStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function openPrometheus() {
  window.open(`${API_BASE_URL}/metrics`, "_blank");
}

async function refreshMetrics() {
  const btn = document.getElementById("refreshMetricsBtn");
  if (btn) btn.disabled = true;

  try {
    // Refresh all metrics
    await Promise.all([
      refreshHealth(),
      refreshVectorStats(),
      refreshSystemMetrics(),
    ]);
    showAlert("✅ Metrics refreshed successfully!", "success");
  } catch (error) {
    console.error("Failed to refresh metrics:", error);
    showAlert(`Failed to refresh metrics: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function viewDbStats() {
  const btn = document.getElementById("viewDbStatsBtn");
  const content = document.getElementById("databaseContent");

  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/database/stats`);
    const result = await response.json();

    if (response.ok && result.success) {
      content.innerHTML = `
                <h4>🗄️ Database Statistics</h4>
                <div class="db-stats">
                    <div class="stat-item">
                        <span class="stat-label">Active Connections:</span>
                        <span class="stat-value">${
                          result.data.activeConnections || 0
                        }</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Total Queries:</span>
                        <span class="stat-value">${
                          result.data.totalQueries || 0
                        }</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Slow Queries:</span>
                        <span class="stat-value">${
                          result.data.slowQueries || 0
                        }</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Cache Hit Rate:</span>
                        <span class="stat-value">${
                          result.data.cacheHitRate || 0
                        }%</span>
                    </div>
                </div>
            `;
      content.style.display = "block";
      showAlert("Database statistics loaded successfully", "success");
      updateStatusIndicator("databaseStatus", "healthy");
    } else {
      content.innerHTML = `<p class="error">❌ ${
        result.message || "Failed to load database statistics"
      }</p>`;
      content.style.display = "block";
      showAlert(
        result.message || "Failed to load database statistics",
        "error"
      );
      updateStatusIndicator("databaseStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to load database stats:", error);
    content.innerHTML = `<p class="error">❌ Failed to load database statistics: ${error.message}</p>`;
    content.style.display = "block";
    showAlert(`Failed to load database statistics: ${error.message}`, "error");
    updateStatusIndicator("databaseStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function checkDbHealth() {
  const btn = document.getElementById("checkDbHealthBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/database/health`);
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ Database health check passed!", "success");
      updateStatusIndicator("databaseStatus", "healthy");
    } else {
      showAlert(result.message || "Database health check failed", "error");
      updateStatusIndicator("databaseStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Database health check failed:", error);
    showAlert(`Database health check failed: ${error.message}`, "error");
    updateStatusIndicator("databaseStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function optimizeDb() {
  const btn = document.getElementById("optimizeDbBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/database/optimize`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ Database optimization completed!", "success");
      updateStatusIndicator("databaseStatus", "healthy");
    } else {
      showAlert(result.message || "Failed to optimize database", "error");
      updateStatusIndicator("databaseStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to optimize database:", error);
    showAlert(`Failed to optimize database: ${error.message}`, "error");
    updateStatusIndicator("databaseStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function checkServices() {
  const btn = document.getElementById("checkServicesBtn");
  const content = document.getElementById("servicesContent");

  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/services/status`);
    const result = await response.json();

    if (response.ok && result.success) {
      const servicesHtml = result.data.services
        .map(
          (service) =>
            `<div class="service-item ${service.status.toLowerCase()}">
                    <span class="service-name">${service.name}</span>
                    <span class="service-status">${service.status}</span>
                    <span class="service-response">${
                      service.responseTime || "N/A"
                    }ms</span>
                </div>`
        )
        .join("");

      content.innerHTML = `
                <h4>🔧 Service Status</h4>
                <div class="services-list">${servicesHtml}</div>
            `;
      content.style.display = "block";
      showAlert("Service status loaded successfully", "success");
      updateStatusIndicator("servicesStatus", "healthy");
    } else {
      content.innerHTML = `<p class="error">❌ ${
        result.message || "Failed to load service status"
      }</p>`;
      content.style.display = "block";
      showAlert(result.message || "Failed to load service status", "error");
      updateStatusIndicator("servicesStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to load service status:", error);
    content.innerHTML = `<p class="error">❌ Failed to load service status: ${error.message}</p>`;
    content.style.display = "block";
    showAlert(`Failed to load service status: ${error.message}`, "error");
    updateStatusIndicator("servicesStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function restartServices() {
  const btn = document.getElementById("restartServicesBtn");
  if (btn) btn.disabled = true;

  if (!confirm("⚠️ This will restart all services. Continue?")) {
    if (btn) btn.disabled = false;
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/admin/services/restart`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ Services restarted successfully!", "success");
      updateStatusIndicator("servicesStatus", "healthy");
    } else {
      showAlert(result.message || "Failed to restart services", "error");
      updateStatusIndicator("servicesStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to restart services:", error);
    showAlert(`Failed to restart services: ${error.message}`, "error");
    updateStatusIndicator("servicesStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function viewSecurityLogs() {
  const btn = document.getElementById("viewSecurityLogsBtn");
  const content = document.getElementById("securityContent");

  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/security/logs`);
    const result = await response.json();

    if (response.ok && result.success) {
      const logsHtml = result.data.logs
        .map(
          (log) =>
            `<div class="security-log ${log.severity.toLowerCase()}">
                    <span class="log-time">${new Date(
                      log.timestamp
                    ).toLocaleString()}</span>
                    <span class="log-severity">[${log.severity}]</span>
                    <span class="log-event">${log.event}</span>
                    <span class="log-source">${log.source}</span>
                </div>`
        )
        .join("");

      content.innerHTML = `
                <h4>🔒 Security Logs</h4>
                <div class="security-logs">${
                  logsHtml || "<p>No security events</p>"
                }</div>
            `;
      content.style.display = "block";
      showAlert("Security logs loaded successfully", "success");
      updateStatusIndicator("securityStatus", "healthy");
    } else {
      content.innerHTML = `<p class="error">❌ ${
        result.message || "Failed to load security logs"
      }</p>`;
      content.style.display = "block";
      showAlert(result.message || "Failed to load security logs", "error");
      updateStatusIndicator("securityStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Failed to load security logs:", error);
    content.innerHTML = `<p class="error">❌ Failed to load security logs: ${error.message}</p>`;
    content.style.display = "block";
    showAlert(`Failed to load security logs: ${error.message}`, "error");
    updateStatusIndicator("securityStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function runSecurityScan() {
  const btn = document.getElementById("runSecurityScanBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/security/scan`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert(
        `✅ Security scan completed! ${
          result.data.vulnerabilities || 0
        } vulnerabilities found`,
        "success"
      );
      updateStatusIndicator("securityStatus", "healthy");
    } else {
      showAlert(result.message || "Security scan failed", "error");
      updateStatusIndicator("securityStatus", "unhealthy");
    }
  } catch (error) {
    console.error("Security scan failed:", error);
    showAlert(`Security scan failed: ${error.message}`, "error");
    updateStatusIndicator("securityStatus", "unhealthy");
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Quick Actions Functions
 */
async function fullSystemCheck() {
  const btn = document.getElementById("fullSystemCheck");
  if (btn) btn.disabled = true;

  try {
    showAlert("🔍 Running full system check...", "info");

    // Run multiple checks in parallel
    const checks = await Promise.allSettled([
      fetch(`${API_BASE_URL}/health`).then((r) => r.json()),
      fetch(`${API_BASE_URL}/admin/database/health`).then((r) => r.json()),
      fetch(`${API_BASE_URL}/admin/services/status`).then((r) => r.json()),
      fetch(`${API_BASE_URL}/admin/cache/stats`).then((r) => r.json()),
    ]);

    const results = checks.map((check, index) => {
      const names = ["Health", "Database", "Services", "Cache"];
      return {
        name: names[index],
        status:
          check.status === "fulfilled" && check.value.success ? "✅" : "❌",
      };
    });

    const summary = results.map((r) => `${r.name}: ${r.status}`).join(", ");
    showAlert(`System check complete: ${summary}`, "success");
  } catch (error) {
    console.error("Full system check failed:", error);
    showAlert(`System check failed: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function clearAllCaches() {
  const btn = document.getElementById("clearAllCaches");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/cache/clear-all`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ All caches cleared successfully!", "success");
    } else {
      showAlert(result.message || "Failed to clear caches", "error");
    }
  } catch (error) {
    console.error("Failed to clear caches:", error);
    showAlert(`Failed to clear caches: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function exportLogs() {
  const btn = document.getElementById("exportLogs");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/logs/export`);

    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `system-export-${
        new Date().toISOString().split("T")[0]
      }.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      showAlert("✅ System logs exported successfully!", "success");
    } else {
      showAlert("Failed to export logs", "error");
    }
  } catch (error) {
    console.error("Failed to export logs:", error);
    showAlert(`Failed to export logs: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

function viewApiDocs() {
  const modal = document.getElementById("apiModal");
  const modalBody = document.getElementById("apiModalBody");

  modalBody.innerHTML = document.getElementById("apiDocsTemplate").innerHTML;
  modal.hidden = false;
  modal.setAttribute("aria-hidden", "false");

  // Focus management
  modal.focus();

  // Setup event listeners for API docs
  setupApiDocsListeners();
}

async function backupSystem() {
  const btn = document.getElementById("backupSystem");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/backup/create`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert(`✅ System backup created: ${result.data.backupId}`, "success");
    } else {
      showAlert(result.message || "Failed to create backup", "error");
    }
  } catch (error) {
    console.error("Failed to create backup:", error);
    showAlert(`Failed to create backup: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function performanceTest() {
  const btn = document.getElementById("performanceTest");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/performance/test`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert(
        `✅ Performance test completed! Score: ${result.data.score || "N/A"}`,
        "success"
      );
    } else {
      showAlert(result.message || "Performance test failed", "error");
    }
  } catch (error) {
    console.error("Performance test failed:", error);
    showAlert(`Performance test failed: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function restartApp() {
  const btn = document.getElementById("restartApp");
  if (btn) btn.disabled = true;

  if (!confirm("⚠️ This will restart the application. Continue?")) {
    if (btn) btn.disabled = false;
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/admin/app/restart`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ Application restart initiated!", "success");
      setTimeout(() => window.location.reload(), 3000);
    } else {
      showAlert(result.message || "Failed to restart application", "error");
    }
  } catch (error) {
    console.error("Failed to restart application:", error);
    showAlert(`Failed to restart application: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function emergencyStop() {
  const btn = document.getElementById("emergencyStop");
  if (btn) btn.disabled = true;

  if (
    !confirm(
      "🚨 EMERGENCY STOP: This will immediately stop all services. Continue?"
    )
  ) {
    if (btn) btn.disabled = false;
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/admin/app/emergency-stop`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("🚨 Emergency stop initiated!", "warning");
    } else {
      showAlert(result.message || "Failed to initiate emergency stop", "error");
    }
  } catch (error) {
    console.error("Emergency stop failed:", error);
    showAlert(`Emergency stop failed: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

// Cache Management Functions
async function clearSystemCache() {
  const btn = document.getElementById("clearCacheBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/cache/clear`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert(
        `✅ Cache cleared successfully! Freed ${
          result.data?.freed_memory || "N/A"
        } MB`,
        "success"
      );
      updateStatusIndicators();
    } else {
      showAlert(result.message || "Failed to clear cache", "error");
    }
  } catch (error) {
    console.error("Failed to clear cache:", error);
    showAlert(`Failed to clear cache: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function viewCacheStatistics() {
  const btn = document.getElementById("viewCacheStatsBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/cache/stats`);
    const result = await response.json();

    if (response.ok && result.success) {
      const stats = result.data;
      const statsHTML = `
                <div class="admin-modal-content">
                    <h3>📊 Cache Statistics</h3>
                    <div class="stats-grid">
                        <div class="stat-item">
                            <div class="stat-label">Total Entries</div>
                            <div class="stat-value">${
                              stats.total_entries || "N/A"
                            }</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Memory Usage</div>
                            <div class="stat-value">${
                              stats.memory_usage || "N/A"
                            } MB</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Hit Rate</div>
                            <div class="stat-value">${
                              stats.hit_rate || "N/A"
                            }%</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Miss Rate</div>
                            <div class="stat-value">${
                              stats.miss_rate || "N/A"
                            }%</div>
                        </div>
                    </div>
                </div>
            `;
      showModal("Cache Statistics", statsHTML);
    } else {
      showAlert(result.message || "Failed to load cache statistics", "error");
    }
  } catch (error) {
    console.error("Failed to load cache statistics:", error);
    showAlert(`Failed to load cache statistics: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function configureCacheSettings() {
  const btn = document.getElementById("configureCacheBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/admin/cache/config`);
    const result = await response.json();

    if (response.ok && result.success) {
      const config = result.data;
      const configHTML = `
                <div class="admin-modal-content">
                    <h3>⚙️ Cache Configuration</h3>
                    <form id="cacheConfigForm">
                        <div class="form-group">
                            <label for="maxSize">Max Size (MB)</label>
                            <input type="number" id="maxSize" value="${
                              config.max_size || 100
                            }" min="10" max="1000">
                        </div>
                        <div class="form-group">
                            <label for="ttl">TTL (seconds)</label>
                            <input type="number" id="ttl" value="${
                              config.ttl || 3600
                            }" min="60" max="86400">
                        </div>
                        <div class="form-group">
                            <label for="compression">Enable Compression</label>
                            <input type="checkbox" id="compression" ${
                              config.compression ? "checked" : ""
                            }>
                        </div>
                        <div class="form-actions">
                            <button type="submit" class="btn btn-primary">Save Configuration</button>
                        </div>
                    </form>
                </div>
            `;
      showModal("Cache Configuration", configHTML);

      // Handle form submission
      document
        .getElementById("cacheConfigForm")
        .addEventListener("submit", async (e) => {
          e.preventDefault();
          const formData = {
            max_size: parseInt(document.getElementById("maxSize").value),
            ttl: parseInt(document.getElementById("ttl").value),
            compression: document.getElementById("compression").checked,
          };

          try {
            const saveResponse = await fetch(
              `${API_BASE_URL}/admin/cache/config`,
              {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData),
              }
            );
            const saveResult = await saveResponse.json();

            if (saveResponse.ok && saveResult.success) {
              showAlert("✅ Cache configuration updated!", "success");
              closeModal();
            } else {
              showAlert(
                saveResult.message || "Failed to update configuration",
                "error"
              );
            }
          } catch (error) {
            showAlert(
              `Failed to update configuration: ${error.message}`,
              "error"
            );
          }
        });
    } else {
      showAlert(
        result.message || "Failed to load cache configuration",
        "error"
      );
    }
  } catch (error) {
    console.error("Failed to load cache configuration:", error);
    showAlert(`Failed to load cache configuration: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

// Circuit Breaker Functions
async function viewCircuitBreakerStatus() {
  const btn = document.getElementById("viewCircuitBreakerStatusBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(
      `${API_BASE_URL}/admin/circuit-breaker/status`
    );
    const result = await response.json();

    if (response.ok && result.success) {
      const status = result.data;
      const statusHTML = `
                <div class="admin-modal-content">
                    <h3>🔌 Circuit Breaker Status</h3>
                    <div class="status-grid">
                        <div class="status-item">
                            <div class="status-label">State</div>
                            <div class="status-value ${
                              status.state === "CLOSED"
                                ? "status-healthy"
                                : status.state === "OPEN"
                                ? "status-error"
                                : "status-warning"
                            }">${status.state || "UNKNOWN"}</div>
                        </div>
                        <div class="status-item">
                            <div class="status-label">Failure Count</div>
                            <div class="status-value">${
                              status.failure_count || 0
                            }</div>
                        </div>
                        <div class="status-item">
                            <div class="status-label">Success Count</div>
                            <div class="status-value">${
                              status.success_count || 0
                            }</div>
                        </div>
                        <div class="status-item">
                            <div class="status-label">Last Failure</div>
                            <div class="status-value">${
                              status.last_failure
                                ? new Date(status.last_failure).toLocaleString()
                                : "Never"
                            }</div>
                        </div>
                    </div>
                </div>
            `;
      showModal("Circuit Breaker Status", statusHTML);
    } else {
      showAlert(
        result.message || "Failed to load circuit breaker status",
        "error"
      );
    }
  } catch (error) {
    console.error("Failed to load circuit breaker status:", error);
    showAlert(
      `Failed to load circuit breaker status: ${error.message}`,
      "error"
    );
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function resetCircuitBreaker() {
  const btn = document.getElementById("resetCircuitBreakerBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(
      `${API_BASE_URL}/admin/circuit-breaker/reset`,
      { method: "POST" }
    );
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("✅ Circuit breaker reset successfully!", "success");
      updateStatusIndicators();
    } else {
      showAlert(result.message || "Failed to reset circuit breaker", "error");
    }
  } catch (error) {
    console.error("Failed to reset circuit breaker:", error);
    showAlert(`Failed to reset circuit breaker: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function configureCircuitBreaker() {
  const btn = document.getElementById("configureCircuitBreakerBtn");
  if (btn) btn.disabled = true;

  try {
    const response = await fetch(
      `${API_BASE_URL}/admin/circuit-breaker/config`
    );
    const result = await response.json();

    if (response.ok && result.success) {
      const config = result.data;
      const configHTML = `
                <div class="admin-modal-content">
                    <h3>⚙️ Circuit Breaker Configuration</h3>
                    <form id="circuitBreakerConfigForm">
                        <div class="form-group">
                            <label for="failureThreshold">Failure Threshold</label>
                            <input type="number" id="failureThreshold" value="${
                              config.failure_threshold || 5
                            }" min="1" max="50">
                        </div>
                        <div class="form-group">
                            <label for="timeout">Timeout (seconds)</label>
                            <input type="number" id="timeout" value="${
                              config.timeout || 30
                            }" min="5" max="300">
                        </div>
                        <div class="form-group">
                            <label for="resetTimeout">Reset Timeout (seconds)</label>
                            <input type="number" id="resetTimeout" value="${
                              config.reset_timeout || 60
                            }" min="10" max="600">
                        </div>
                        <div class="form-actions">
                            <button type="submit" class="btn btn-primary">Save Configuration</button>
                        </div>
                    </form>
                </div>
            `;
      showModal("Circuit Breaker Configuration", configHTML);

      // Handle form submission
      document
        .getElementById("circuitBreakerConfigForm")
        .addEventListener("submit", async (e) => {
          e.preventDefault();
          const formData = {
            failure_threshold: parseInt(
              document.getElementById("failureThreshold").value
            ),
            timeout: parseInt(document.getElementById("timeout").value),
            reset_timeout: parseInt(
              document.getElementById("resetTimeout").value
            ),
          };

          try {
            const saveResponse = await fetch(
              `${API_BASE_URL}/admin/circuit-breaker/config`,
              {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData),
              }
            );
            const saveResult = await saveResponse.json();

            if (saveResponse.ok && saveResult.success) {
              showAlert("✅ Circuit breaker configuration updated!", "success");
              closeModal();
            } else {
              showAlert(
                saveResult.message || "Failed to update configuration",
                "error"
              );
            }
          } catch (error) {
            showAlert(
              `Failed to update configuration: ${error.message}`,
              "error"
            );
          }
        });
    } else {
      showAlert(
        result.message || "Failed to load circuit breaker configuration",
        "error"
      );
    }
  } catch (error) {
    console.error("Failed to load circuit breaker configuration:", error);
    showAlert(
      `Failed to load circuit breaker configuration: ${error.message}`,
      "error"
    );
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function emergencyStop() {
  const btn = document.getElementById("emergencyStop");
  if (btn) btn.disabled = true;

  if (
    !confirm("🚨 EMERGENCY STOP - This will halt all operations. Are you sure?")
  ) {
    if (btn) btn.disabled = false;
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/admin/emergency/stop`, {
      method: "POST",
    });
    const result = await response.json();

    if (response.ok && result.success) {
      showAlert("🛑 Emergency stop activated!", "warning");
    } else {
      showAlert(result.message || "Failed to activate emergency stop", "error");
    }
  } catch (error) {
    console.error("Failed to activate emergency stop:", error);
    showAlert(`Failed to activate emergency stop: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Export System Logs (Quick Action)
 */
async function exportSystemLogs() {
  const btn = document.getElementById("exportLogs");
  if (btn) btn.disabled = true;

  try {
    showAlert("Generating system logs...", "info");

    // Collect system information
    const health = await fetch(`${API_BASE_URL}/health`).then((r) => r.json());
    const stats = await fetch(`${API_BASE_URL}/stats`).then((r) => r.json());
    const cacheStats = await fetch(`${API_BASE_URL}/cache/stats`).then((r) =>
      r.json()
    );
    const cbStatus = await fetch(`${API_BASE_URL}/circuit-breaker/status`).then(
      (r) => r.json()
    );

    const logData = {
      timestamp: new Date().toISOString(),
      system: {
        health: health,
        statistics: stats,
        cache: cacheStats,
        circuitBreakers: cbStatus,
      },
      browser: {
        userAgent: navigator.userAgent,
        language: navigator.language,
        platform: navigator.platform,
      },
      performance: {
        memory: performance.memory
          ? {
              usedJSHeapSize: performance.memory.usedJSHeapSize,
              totalJSHeapSize: performance.memory.totalJSHeapSize,
              jsHeapSizeLimit: performance.memory.jsHeapSizeLimit,
            }
          : null,
      },
    };

    // Create downloadable file
    const blob = new Blob([JSON.stringify(logData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `system-logs-${new Date()
      .toISOString()
      .slice(0, 19)
      .replace(/:/g, "-")}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showAlert("✅ System logs exported successfully!", "success");
  } catch (error) {
    console.error("Failed to export logs:", error);
    showAlert(`❌ Failed to export logs: ${error.message}`, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Open image lightbox modal with navigation support
 */
function openLightbox(
  transactionId,
  timestamp,
  resultsArray = null,
  index = -1
) {
  const lightbox = document.getElementById("imageLightbox");
  const lightboxImage = document.getElementById("lightboxImage");
  const lightboxTxId = document.getElementById("lightboxTxId");
  const lightboxTimestamp = document.getElementById("lightboxTimestamp");

  // Store results for navigation
  if (resultsArray && resultsArray.length > 0) {
    currentLightboxResults = resultsArray;
    currentLightboxIndex = index >= 0 ? index : 0;
  }

  if (lightbox && lightboxImage) {
    lightboxImage.src = `${API_BASE_URL}/image/${transactionId}`;
    if (lightboxTxId)
      lightboxTxId.textContent = `Transaction: ${transactionId}`;
    if (lightboxTimestamp)
      lightboxTimestamp.textContent = `Time: ${formatDateTime(timestamp)}`;

    // Update navigation button states
    updateLightboxNavigation();

    lightbox.style.display = "flex";
    document.body.style.overflow = "hidden"; // Prevent background scrolling
  }
}

/**
 * Navigate to previous image in lightbox
 */
function navigateLightboxPrev() {
  if (currentLightboxIndex > 0 && currentLightboxResults.length > 0) {
    currentLightboxIndex--;
    const match = currentLightboxResults[currentLightboxIndex];
    openLightbox(
      match.entry_transaction_id,
      match.entry_timestamp,
      currentLightboxResults,
      currentLightboxIndex
    );
  }
}

/**
 * Navigate to next image in lightbox
 */
function navigateLightboxNext() {
  if (
    currentLightboxIndex < currentLightboxResults.length - 1 &&
    currentLightboxResults.length > 0
  ) {
    currentLightboxIndex++;
    const match = currentLightboxResults[currentLightboxIndex];
    openLightbox(
      match.entry_transaction_id,
      match.entry_timestamp,
      currentLightboxResults,
      currentLightboxIndex
    );
  }
}

/**
 * Update lightbox navigation button states
 */
function updateLightboxNavigation() {
  const prevBtn = document.getElementById("lightboxPrevBtn");
  const nextBtn = document.getElementById("lightboxNextBtn");
  const counter = document.getElementById("lightboxCounter");

  if (currentLightboxResults.length > 0) {
    if (prevBtn) {
      prevBtn.disabled = currentLightboxIndex <= 0;
      prevBtn.style.display = "block";
    }
    if (nextBtn) {
      nextBtn.disabled =
        currentLightboxIndex >= currentLightboxResults.length - 1;
      nextBtn.style.display = "block";
    }
    if (counter) {
      counter.textContent = `${currentLightboxIndex + 1} / ${
        currentLightboxResults.length
      }`;
      counter.style.display = "block";
    }
  } else {
    if (prevBtn) prevBtn.style.display = "none";
    if (nextBtn) nextBtn.style.display = "none";
    if (counter) counter.style.display = "none";
  }
}

/**
 * Close image lightbox modal
 */
function closeLightbox() {
  const lightbox = document.getElementById("imageLightbox");
  if (lightbox) {
    lightbox.style.display = "none";
    document.body.style.overflow = ""; // Restore scrolling

    // Reset navigation state
    currentLightboxResults = [];
    currentLightboxIndex = -1;
  }
}

/**
 * Open settings panel
 */
function openSettings() {
  const panel = document.getElementById("settingsPanel");
  if (panel) {
    panel.style.display = "flex";
    document.body.style.overflow = "hidden";

    // Load current settings
    document.getElementById("settingEnableOrb").checked =
      searchSettings.enableOrb;
    document.getElementById("settingMinSimilarity").value =
      searchSettings.minSimilarity;
    document.getElementById("settingMinOrbMatches").value =
      searchSettings.minOrbMatches;
    document.getElementById("settingTopK").value = searchSettings.topK;

    // Update labels
    updateSliderLabel("settingMinSimilarity", searchSettings.minSimilarity);
    updateSliderLabel("settingMinOrbMatches", searchSettings.minOrbMatches);
    updateSliderLabel("settingTopK", searchSettings.topK);
  }
}

/**
 * Close settings panel
 */
function closeSettings() {
  const panel = document.getElementById("settingsPanel");
  if (panel) {
    panel.style.display = "none";
    document.body.style.overflow = "";
  }
}

/**
 * Update settings from panel
 */
function updateSettings() {
  searchSettings.enableOrb =
    document.getElementById("settingEnableOrb").checked;
  searchSettings.minSimilarity = parseFloat(
    document.getElementById("settingMinSimilarity").value
  );
  searchSettings.minOrbMatches = parseInt(
    document.getElementById("settingMinOrbMatches").value
  );
  searchSettings.topK = parseInt(document.getElementById("settingTopK").value);

  console.log("Settings updated:", searchSettings);
}

/**
 * Reset settings to defaults
 */
function resetSettings() {
  searchSettings = {
    enableOrb: true,
    minSimilarity: 0.55,
    minOrbMatches: 8,
    topK: 10,
  };

  document.getElementById("settingEnableOrb").checked = true;
  document.getElementById("settingMinSimilarity").value = 0.55;
  document.getElementById("settingMinOrbMatches").value = 8;
  document.getElementById("settingTopK").value = 10;
  document.getElementById("topK").value = 10;

  updateSliderLabel("settingMinSimilarity", 0.55);
  updateSliderLabel("settingMinOrbMatches", 8);
  updateSliderLabel("settingTopK", 10);

  showAlert("Settings reset to defaults", "success");
}

/**
 * Update slider value label
 */
function updateSliderLabel(sliderId, value) {
  const label = document.getElementById(`${sliderId}Value`);
  if (label) {
    label.textContent = value;
  }
}

// Setup API modal and keyboard shortcuts
document.addEventListener("DOMContentLoaded", () => {
  const openBtn = document.getElementById("openApiModalBtn");
  const closeBtn = document.getElementById("closeApiModalBtn");

  if (openBtn) {
    openBtn.addEventListener("click", () => {
      console.log("Opening API modal");
      openApiModal();
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener("click", closeApiModal);
  }

  // Keyboard shortcuts
  document.addEventListener("keydown", (e) => {
    const lightbox = document.getElementById("imageLightbox");
    const settingsPanel = document.getElementById("settingsPanel");

    // Lightbox navigation with arrow keys
    if (lightbox && lightbox.style.display === "flex") {
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        navigateLightboxPrev();
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        navigateLightboxNext();
      } else if (e.key === "Escape") {
        e.preventDefault();
        closeLightbox();
      }
    }

    // Settings panel shortcuts
    if (settingsPanel && settingsPanel.style.display === "flex") {
      if (e.key === "Escape") {
        e.preventDefault();
        closeSettings();
      }
    }

    // Global shortcuts
    if (!lightbox || lightbox.style.display !== "flex") {
      if (e.key === "," && e.ctrlKey) {
        e.preventDefault();
        openSettings();
      }
    }
  });
});
