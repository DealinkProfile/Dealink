// Dealink Analytics - Lightweight, Privacy-Friendly Event Tracking
// No personal data collected. Only aggregated usage events.

const DealinkAnalytics = (() => {
  // Config
  const ANALYTICS_ENABLED = true; // Set to false to disable all tracking
  const BATCH_SIZE = 10;
  const FLUSH_INTERVAL = 30000; // 30 seconds
  const STORAGE_KEY = 'dealink_analytics_queue';

  let eventQueue = [];
  let sessionId = null;

  // Generate anonymous session ID (no user identification)
  function getSessionId() {
    if (!sessionId) {
      sessionId = `s_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    return sessionId;
  }

  // Track an event (queued, batched)
  function track(eventName, properties = {}) {
    if (!ANALYTICS_ENABLED) return;

    const event = {
      event: eventName,
      timestamp: new Date().toISOString(),
      session: getSessionId(),
      version: chrome.runtime.getManifest().version,
      ...properties,
    };

    eventQueue.push(event);

    // Auto-flush if batch is full
    if (eventQueue.length >= BATCH_SIZE) {
      flush();
    }
  }

  // Flush events to storage (for future backend submission)
  async function flush() {
    if (eventQueue.length === 0) return;

    try {
      const stored = await chrome.storage.local.get(STORAGE_KEY);
      const existing = stored[STORAGE_KEY] || [];
      const combined = [...existing, ...eventQueue].slice(-100); // Keep last 100 events max

      await chrome.storage.local.set({ [STORAGE_KEY]: combined });
      eventQueue = [];
    } catch (e) {
      // Silently fail - analytics should never break the app
    }
  }

  // Get stored analytics (for debug/export)
  async function getStoredEvents() {
    const stored = await chrome.storage.local.get(STORAGE_KEY);
    return stored[STORAGE_KEY] || [];
  }

  // Clear stored analytics
  async function clear() {
    await chrome.storage.local.remove(STORAGE_KEY);
    eventQueue = [];
  }

  // Periodic flush
  if (typeof setInterval !== 'undefined') {
    setInterval(flush, FLUSH_INTERVAL);
  }

  // === Pre-defined Events ===

  function trackProductDetected(platform, hasBrand, hasGTIN) {
    track('product_detected', { platform, has_brand: hasBrand, has_gtin: hasGTIN });
  }

  function trackDealsFound(count, bestSavingsPercent, searchTimeMs) {
    track('deals_found', { count, best_savings_pct: bestSavingsPercent, search_time_ms: searchTimeMs });
  }

  function trackNoDeals() {
    track('no_deals_found');
  }

  function trackDealClicked(platform, savingsPercent, position) {
    track('deal_clicked', { platform, savings_pct: savingsPercent, position });
  }

  function trackSortChanged(sortBy) {
    track('sort_changed', { sort_by: sortBy });
  }

  function trackShowMore() {
    track('show_more_clicked');
  }

  function trackError(errorType) {
    track('error', { error_type: errorType });
  }

  function trackRetry() {
    track('retry_clicked');
  }

  function trackCacheHit() {
    track('cache_hit');
  }

  return {
    track,
    flush,
    getStoredEvents,
    clear,
    // Convenience methods
    trackProductDetected,
    trackDealsFound,
    trackNoDeals,
    trackDealClicked,
    trackSortChanged,
    trackShowMore,
    trackError,
    trackRetry,
    trackCacheHit,
  };
})();

// Export for use in other scripts
if (typeof globalThis !== 'undefined') {
  globalThis.DealinkAnalytics = DealinkAnalytics;
}


