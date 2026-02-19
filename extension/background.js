// Dealink Background Service Worker
// Handles communication between content script and backend

// Backend URL — change to production URL when deploying
// Local development: http://127.0.0.1:8000
// Production: https://your-app.railway.app (or Render URL)
const BACKEND_URL = 'https://dealink-api-production.up.railway.app/api/v1/search';
const MAX_RETRIES = 2;
const RETRY_DELAY = 1000; // 1 second base delay
const CACHE_TTL = 1 * 60 * 60 * 1000; // 1 hour (aligned with backend cache)
const REQUEST_TIMEOUT = 15000; // 15 seconds — SerpApi responds in 1-4s, 15s is generous

// Error types for better handling
const ErrorTypes = {
  NETWORK: 'network',
  TIMEOUT: 'timeout',
  SERVER: 'server',
  UNKNOWN: 'unknown',
};

/**
 * Fetch with timeout support
 */
async function fetchWithTimeout(url, options, timeout = REQUEST_TIMEOUT) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
}

/**
 * Fetch with retry and exponential backoff
 */
async function fetchWithRetry(url, options, retries = MAX_RETRIES) {
  let lastError;
  
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetchWithTimeout(url, options);
      
      if (!response.ok) {
        const errorText = await response.text().catch(() => '');
        throw { type: ErrorTypes.SERVER, status: response.status, message: errorText };
      }
      
      return await response.json();
    } catch (error) {
      lastError = error;
      console.log(`[Dealink] Attempt ${i + 1}/${retries} failed:`, error.message || error);
      
      if (i < retries - 1) {
        // Exponential backoff
        const delay = RETRY_DELAY * Math.pow(2, i);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  // Classify the error
  if (lastError.name === 'AbortError') {
    throw { type: ErrorTypes.TIMEOUT, message: 'Request timed out' };
  } else if (lastError.type === ErrorTypes.SERVER) {
    throw lastError;
  } else if (lastError.message?.includes('Failed to fetch') || lastError.message?.includes('NetworkError')) {
    throw { type: ErrorTypes.NETWORK, message: 'Network connection failed' };
  }
  
  throw { type: ErrorTypes.UNKNOWN, message: lastError.message || 'Unknown error' };
}

/**
 * Store results and notify popup
 */
async function storeResults(result, product = null) {
  const dataToStore = { dealinkResult: result };
  
  if (product) {
    dataToStore.dealinkProduct = product;
  }
  
  await chrome.storage.local.set(dataToStore);
  
  // Update badge based on results
  updateBadge(result, product);
  
  // Notify popup if it's open
  try {
    chrome.runtime.sendMessage({ type: 'RESULTS_UPDATED' });
  } catch (e) {
    // Popup might not be open, ignore
  }
}

/**
 * Update extension badge to show savings
 */
function updateBadge(result, product) {
  if (!result || result.error) {
    // Clear badge on error
    chrome.action.setBadgeText({ text: '' });
    return;
  }
  
  const sameProducts = result.same_products || [];
  
  if (sameProducts.length === 0) {
    // No deals found
    chrome.action.setBadgeText({ text: '' });
    return;
  }
  
  // Find best price
  const originalPrice = product?.price || result.original_price;
  const prices = sameProducts.map(p => p.total || p.price).filter(p => p);
  const bestPrice = Math.min(...prices);
  
  if (originalPrice && bestPrice < originalPrice) {
    // Calculate savings percentage
    const savingsPercent = Math.round(((originalPrice - bestPrice) / originalPrice) * 100);
    
    if (savingsPercent > 0) {
      // Show savings on badge
      chrome.action.setBadgeText({ text: `-${savingsPercent}%` });
      chrome.action.setBadgeBackgroundColor({ color: '#3B82F6' }); // Blue (matches logo)
      chrome.action.setTitle({ title: `Dealink - חסוך ${savingsPercent}%!` });
      return;
    }
  }
  
  // Deals found but no savings (same price or higher)
  chrome.action.setBadgeText({ text: '✓' });
  chrome.action.setBadgeBackgroundColor({ color: '#6B7280' }); // Gray
  chrome.action.setTitle({ title: 'Dealink - נמצאו תוצאות' });
}

/**
 * Clear badge when navigating away from product pages
 */
function clearBadge() {
  chrome.action.setBadgeText({ text: '' });
  chrome.action.setTitle({ title: 'Dealink' });
}

/**
 * Get cache key for a product URL
 */
function getCacheKey(url) {
  return `dealink_cache_${url}`;
}

/**
 * Process product detection request
 */
async function processProductDetection(productData) {
  const cacheKey = getCacheKey(productData.url);
  const now = Date.now();
  
  // Store product info for popup display
  const productInfo = {
    title: productData.title,
    price: productData.price,
    currency: productData.currency || 'USD',
    image: productData.image,
    platform: productData.platform,
    brand: productData.structured?.brand || null,
    url: productData.url,
  };
  
  try {
    // Check cache first
    const cached = await chrome.storage.local.get([cacheKey]);
    const cachedData = cached[cacheKey];
    
    if (cachedData && cachedData.timestamp && (now - cachedData.timestamp) < CACHE_TTL) {
      console.log('[Dealink] Using cached result');
      await storeResults(cachedData.data, productInfo);
      return;
    }
    
    // No valid cache, fetch from backend
    console.log('[Dealink] Fetching from backend...');

    // Extract GTIN from identifiers (prefer GTIN > EAN > UPC)
    const ids = productData.identifiers || {};
    const gtin = ids.gtin || ids.ean || ids.upc || null;

    const searchPayload = {
      gtin: gtin,
      title: productData.title || '',
      source_url: productData.url || '',
      current_price: productData.price || null,
    };

    const result = await fetchWithRetry(BACKEND_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(searchPayload),
    });
    
    console.log('[Dealink] Backend response:', result);

    // Transform new API format → popup-compatible format
    // affiliate_url is used as the click URL so every purchase earns commission
    const popupResult = {
      original_price: searchPayload.current_price,
      same_products: (result.results || []).map(r => ({
        source: r.store,
        platform: r.store?.toLowerCase().replace(/[^a-z0-9]/g, ''),
        title: r.title,
        price: r.price,
        total: r.price,
        price_str: r.price_str,
        url: r.affiliate_url || r.url,  // affiliate link = commission
        image: r.image,
        rating: r.rating,
        reviews: r.reviews,
        condition: 'new',
      })),
      similar_products: [],
      used_products: [],
    };

    // Store in cache
    await chrome.storage.local.set({
      [cacheKey]: {
        data: popupResult,
        timestamp: now,
      },
    });

    // Store results for popup
    await storeResults(popupResult, productInfo);
    
  } catch (error) {
    console.error('[Dealink] Error after retries:', error);
    
    // Try to use expired cache as fallback
    const cached = await chrome.storage.local.get([cacheKey]);
    const cachedData = cached[cacheKey];
    
    if (cachedData?.data) {
      console.log('[Dealink] Using expired cache as fallback');
      await storeResults(cachedData.data, productInfo);
      return;
    }
    
    // No cache available, store error
    const errorResult = {
      error: error.type || ErrorTypes.UNKNOWN,
      message: getErrorMessage(error),
      same_products: [],
      similar_products: [],
      used_products: [],
    };
    
    await storeResults(errorResult, productInfo);
  }
}

/**
 * Get user-friendly error message
 */
function getErrorMessage(error) {
  switch (error.type) {
    case ErrorTypes.NETWORK:
      return 'לא ניתן להתחבר לשרת. בדוק את החיבור לאינטרנט.';
    case ErrorTypes.TIMEOUT:
      return 'הבקשה ארכה יותר מדי זמן. נסה שוב.';
    case ErrorTypes.SERVER:
      return `שגיאת שרת (${error.status}). נסה שוב מאוחר יותר.`;
    default:
      return error.message || 'שגיאה לא צפויה. נסה שוב.';
  }
}

// Message listener
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('[Dealink] Received message:', message.action || message.type);
  
  // Handle Dealink redirect (user clicked a Dealink link - skip search)
  if (message.action === 'DEALINK_SOURCE') {
    console.log('[Dealink] User arrived from Dealink link - skip search, keep old results intact');
    // DON'T overwrite dealinkResult — keep previous results so user can still
    // see them when switching back to the original product tab.
    // The popup checks the URL for dealink_source=1 and shows the right UI.
    chrome.action.setBadgeText({ text: '✓' });
    chrome.action.setBadgeBackgroundColor({ color: '#22C55E' });
    chrome.action.setTitle({ title: 'Dealink - זה הדיל שמצאנו!' });
    return true;
  }

  // Handle product detection from content script
  if (message.action === 'PRODUCT_DETECTED') {
    console.log('[Dealink] Product detected:', message.data?.title?.substring(0, 50));
    processProductDetection(message.data);
    return true;
  }
  
  // Handle retry request from popup
  if (message.type === 'RETRY_FETCH') {
    console.log('[Dealink] Retry requested');
    
    // Get the last product data and retry
    chrome.storage.local.get('dealinkProduct', async (result) => {
      if (result.dealinkProduct?.url) {
        // Clear cache for this URL
        const cacheKey = getCacheKey(result.dealinkProduct.url);
        await chrome.storage.local.remove([cacheKey, 'dealinkResult']);
        
        // Request fresh data from content script
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
          if (tabs[0]?.id) {
            chrome.tabs.sendMessage(tabs[0].id, { action: 'RESCAN_PAGE' });
          }
        });
      }
    });
    
    return true;
  }
  
  return false;
});

// Clear old cache entries periodically (every hour)
chrome.alarms.create('clearOldCache', { periodInMinutes: 60 });

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'clearOldCache') {
    clearExpiredCache();
  }
});

/**
 * Clear expired cache entries
 */
async function clearExpiredCache() {
  const now = Date.now();
  const allItems = await chrome.storage.local.get(null);
  const keysToRemove = [];
  
  for (const [key, value] of Object.entries(allItems)) {
    if (key.startsWith('dealink_cache_') && value.timestamp) {
      if (now - value.timestamp > CACHE_TTL * 2) { // Remove if expired for 2x TTL
        keysToRemove.push(key);
      }
    }
  }
  
  if (keysToRemove.length > 0) {
    console.log(`[Dealink] Clearing ${keysToRemove.length} expired cache entries`);
    await chrome.storage.local.remove(keysToRemove);
  }
}

// Run cache cleanup on startup
clearExpiredCache();

// Handle tab navigation — update badge but DON'T clear results aggressively
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'loading' && tab.url) {
    const isProductPage = /amazon|ebay|walmart|aliexpress|bestbuy|target|newegg|ksp|ivory|bug\.co\.il|currys|argos|otto\.de|bol\.com|cdiscount|coolblue|mediamarkt|jbhifi|flipkart|mercadolibre/i.test(tab.url);
    if (!isProductPage) {
      clearBadge();
      // Only clear the global result pointer — cached results (dealink_cache_*) are preserved
      chrome.storage.local.remove(['dealinkResult', 'dealinkProduct']);
    } else if (!tab.url.includes('dealink_source=1')) {
      // New product page (not from Dealink link) — clear global result so popup shows loading
      // But DON'T touch the URL-based cache — it stays valid
      chrome.storage.local.remove(['dealinkResult']);
    }
    // If dealink_source=1 — do nothing, keep old results intact
  }
});

// Clear badge when switching tabs
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  try {
    const tab = await chrome.tabs.get(activeInfo.tabId);
    const isProductPage = /amazon|ebay|walmart|aliexpress|bestbuy|target|newegg|ksp|ivory|bug\.co\.il|currys|argos|otto\.de|bol\.com|cdiscount|coolblue|mediamarkt|jbhifi|flipkart|mercadolibre/i.test(tab.url || '');
    if (!isProductPage) {
      clearBadge();
    }
  } catch (e) {
    // Tab might not exist, ignore
  }
});

console.log('[Dealink] Background service worker loaded');
