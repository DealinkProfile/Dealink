// Dealink Popup - Clean & Minimal
// Inspired by Honey, Capital One Shopping, Savely

// ========================================
// Store Logos (using Google Favicons API)
// ========================================
const STORE_LOGOS = {
  amazon: 'https://www.google.com/s2/favicons?domain=amazon.com&sz=64',
  ebay: 'https://www.google.com/s2/favicons?domain=ebay.com&sz=64',
  walmart: 'https://www.google.com/s2/favicons?domain=walmart.com&sz=64',
  aliexpress: 'https://www.google.com/s2/favicons?domain=aliexpress.com&sz=64',
  bestbuy: 'https://www.google.com/s2/favicons?domain=bestbuy.com&sz=64',
  target: 'https://www.google.com/s2/favicons?domain=target.com&sz=64',
  newegg: 'https://www.google.com/s2/favicons?domain=newegg.com&sz=64',
  costco: 'https://www.google.com/s2/favicons?domain=costco.com&sz=64',
  bhphoto: 'https://www.google.com/s2/favicons?domain=bhphotovideo.com&sz=64',
  adorama: 'https://www.google.com/s2/favicons?domain=adorama.com&sz=64',
  homedepot: 'https://www.google.com/s2/favicons?domain=homedepot.com&sz=64',
  apple: 'https://www.google.com/s2/favicons?domain=apple.com&sz=64',
  samsung: 'https://www.google.com/s2/favicons?domain=samsung.com&sz=64',
  sennheiser: 'https://www.google.com/s2/favicons?domain=sennheiser.com&sz=64',
  sony: 'https://www.google.com/s2/favicons?domain=sony.com&sz=64',
  dell: 'https://www.google.com/s2/favicons?domain=dell.com&sz=64',
  hp: 'https://www.google.com/s2/favicons?domain=hp.com&sz=64',
  lenovo: 'https://www.google.com/s2/favicons?domain=lenovo.com&sz=64',
  swappa: 'https://www.google.com/s2/favicons?domain=swappa.com&sz=64',
  backmarket: 'https://www.google.com/s2/favicons?domain=backmarket.com&sz=64',
  staples: 'https://www.google.com/s2/favicons?domain=staples.com&sz=64',
  macys: 'https://www.google.com/s2/favicons?domain=macys.com&sz=64',
  temu: 'https://www.google.com/s2/favicons?domain=temu.com&sz=64',
  ksp: 'https://www.google.com/s2/favicons?domain=ksp.co.il&sz=64',
  ivory: 'https://www.google.com/s2/favicons?domain=ivory.co.il&sz=64',
  bug: 'https://www.google.com/s2/favicons?domain=bug.co.il&sz=64',
  zap: 'https://www.google.com/s2/favicons?domain=zap.co.il&sz=64',
  lastprice: 'https://www.google.com/s2/favicons?domain=lastprice.co.il&sz=64',
  tms: 'https://www.google.com/s2/favicons?domain=tms.co.il&sz=64',
  plonter: 'https://www.google.com/s2/favicons?domain=plonter.co.il&sz=64',
  allincell: 'https://www.google.com/s2/favicons?domain=allincell.co.il&sz=64',
  ace: 'https://www.google.com/s2/favicons?domain=ace.co.il&sz=64',
  hamashbir: 'https://www.google.com/s2/favicons?domain=hamashbir365.co.il&sz=64',
  currys: 'https://www.google.com/s2/favicons?domain=currys.co.uk&sz=64',
  argos: 'https://www.google.com/s2/favicons?domain=argos.co.uk&sz=64',
  mediamarkt: 'https://www.google.com/s2/favicons?domain=mediamarkt.de&sz=64',
  jbhifi: 'https://www.google.com/s2/favicons?domain=jbhifi.com.au&sz=64',
  // EU
  otto: 'https://www.google.com/s2/favicons?domain=otto.de&sz=64',
  bol: 'https://www.google.com/s2/favicons?domain=bol.com&sz=64',
  cdiscount: 'https://www.google.com/s2/favicons?domain=cdiscount.com&sz=64',
  coolblue: 'https://www.google.com/s2/favicons?domain=coolblue.nl&sz=64',
  conrad: 'https://www.google.com/s2/favicons?domain=conrad.de&sz=64',
  fnac: 'https://www.google.com/s2/favicons?domain=fnac.com&sz=64',
  saturn: 'https://www.google.com/s2/favicons?domain=saturn.de&sz=64',
  // UK
  johnlewis: 'https://www.google.com/s2/favicons?domain=johnlewis.com&sz=64',
  ao: 'https://www.google.com/s2/favicons?domain=ao.com&sz=64',
  scan: 'https://www.google.com/s2/favicons?domain=scan.co.uk&sz=64',
  // AU
  harveynorman: 'https://www.google.com/s2/favicons?domain=harveynorman.com.au&sz=64',
  kogan: 'https://www.google.com/s2/favicons?domain=kogan.com&sz=64',
  officeworks: 'https://www.google.com/s2/favicons?domain=officeworks.com.au&sz=64',
  // India
  flipkart: 'https://www.google.com/s2/favicons?domain=flipkart.com&sz=64',
  croma: 'https://www.google.com/s2/favicons?domain=croma.com&sz=64',
  // LATAM
  mercadolibre: 'https://www.google.com/s2/favicons?domain=mercadolibre.com.mx&sz=64',
  americanas: 'https://www.google.com/s2/favicons?domain=americanas.com.br&sz=64',
  // Canada
  canadacomputers: 'https://www.google.com/s2/favicons?domain=canadacomputers.com&sz=64',
  thesource: 'https://www.google.com/s2/favicons?domain=thesource.ca&sz=64',
  // Japan
  rakuten: 'https://www.google.com/s2/favicons?domain=rakuten.co.jp&sz=64',
  logitech: 'https://www.google.com/s2/favicons?domain=logitech.com&sz=64',
  razer: 'https://www.google.com/s2/favicons?domain=razer.com&sz=64',
  corsair: 'https://www.google.com/s2/favicons?domain=corsair.com&sz=64',
  bose: 'https://www.google.com/s2/favicons?domain=bose.com&sz=64',
  jbl: 'https://www.google.com/s2/favicons?domain=jbl.com&sz=64',
  guitarcenter: 'https://www.google.com/s2/favicons?domain=guitarcenter.com&sz=64',
  microcenter: 'https://www.google.com/s2/favicons?domain=microcenter.com&sz=64',
  officedepot: 'https://www.google.com/s2/favicons?domain=officedepot.com&sz=64',
  wayfair: 'https://www.google.com/s2/favicons?domain=wayfair.com&sz=64',
  nordstrom: 'https://www.google.com/s2/favicons?domain=nordstrom.com&sz=64',
};

const STORE_NAMES = {
  amazon: 'Amazon',
  ebay: 'eBay', 
  walmart: 'Walmart',
  aliexpress: 'AliExpress',
  bestbuy: 'Best Buy',
  target: 'Target',
  newegg: 'Newegg',
  costco: 'Costco',
  bhphoto: 'B&H Photo',
  adorama: 'Adorama',
  homedepot: 'Home Depot',
  apple: 'Apple',
  samsung: 'Samsung',
  sennheiser: 'Sennheiser',
  sony: 'Sony',
  dell: 'Dell',
  hp: 'HP',
  lenovo: 'Lenovo',
  swappa: 'Swappa',
  backmarket: 'Back Market',
  staples: 'Staples',
  macys: "Macy's",
  temu: 'Temu',
  ksp: 'KSP',
  ivory: 'Ivory',
  bug: 'Bug',
  zap: 'Zap',
  lastprice: 'LastPrice',
  tms: 'TMS',
  plonter: 'Plonter',
  allincell: 'All in Cell',
  ace: 'ACE',
  hamashbir: 'המשביר',
  currys: 'Currys',
  argos: 'Argos',
  mediamarkt: 'MediaMarkt',
  jbhifi: 'JB Hi-Fi',
  // EU
  otto: 'Otto',
  bol: 'Bol.com',
  cdiscount: 'Cdiscount',
  coolblue: 'Coolblue',
  conrad: 'Conrad',
  fnac: 'Fnac',
  saturn: 'Saturn',
  // UK
  johnlewis: 'John Lewis',
  ao: 'AO.com',
  scan: 'Scan',
  // AU
  harveynorman: 'Harvey Norman',
  kogan: 'Kogan',
  officeworks: 'Officeworks',
  // India
  flipkart: 'Flipkart',
  croma: 'Croma',
  // LATAM
  mercadolibre: 'Mercado Libre',
  americanas: 'Americanas',
  // Canada
  canadacomputers: 'Canada Computers',
  thesource: 'The Source',
  // Japan
  rakuten: 'Rakuten',
  logitech: 'Logitech',
  razer: 'Razer',
  corsair: 'Corsair',
  bose: 'Bose',
  jbl: 'JBL',
  guitarcenter: 'Guitar Center',
  microcenter: 'Micro Center',
  officedepot: 'Office Depot',
  wayfair: 'Wayfair',
  nordstrom: 'Nordstrom',
};

// ========================================
// Utilities
// ========================================

function formatPrice(price, currency = 'USD') {
  if (!price && price !== 0) return '—';
  const num = parseFloat(price);
  if (isNaN(num)) return '—';
  
  const symbols = {
    USD: '$', ILS: '₪', EUR: '€', GBP: '£',
    CAD: 'C$', AUD: 'A$', JPY: '¥', CNY: '¥',
    INR: '₹', KRW: '₩', BRL: 'R$', MXN: 'MX$',
    SEK: 'kr', NOK: 'kr', DKK: 'kr', CHF: 'CHF ',
    PLN: 'zł', CZK: 'Kč', TRY: '₺', ZAR: 'R',
  };
  const symbol = symbols[currency] || currency + ' ';
  
  // No decimals for currencies that don't use them
  const noDecimals = ['JPY', 'KRW'];
  const formatted = noDecimals.includes(currency) ? num.toFixed(0) : num.toFixed(2);
  
  return `${symbol}${formatted}`;
}

function calcSavingsPercent(original, current) {
  if (!original || !current) return 0;
  return Math.round(((original - current) / original) * 100);
}

function calcSavingsAmount(original, current) {
  if (!original || !current) return 0;
  return original - current;
}

function getStoreLogo(platform) {
  return STORE_LOGOS[platform?.toLowerCase()] || 
         `https://www.google.com/s2/favicons?domain=${platform}&sz=64`;
}

function getStoreName(platform) {
  return STORE_NAMES[platform?.toLowerCase()] || platform || 'Store';
}

function formatReviews(count) {
  if (!count && count !== 0) return '';
  if (count >= 10000) return (count / 1000).toFixed(0) + 'K';
  if (count >= 1000) return (count / 1000).toFixed(1) + 'K';
  return count.toString();
}

function starSvg() {
  return `<svg viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`;
}

/**
 * Add ?dealink_source=1 to URLs so the extension knows
 * not to search again when the user clicks
 */
function addDealinkParam(url) {
  if (!url || url === '#') return url;
  try {
    const u = new URL(url);
    u.searchParams.set('dealink_source', '1');
    return u.toString();
  } catch {
    // If URL parsing fails, append manually
    const sep = url.includes('?') ? '&' : '?';
    return url + sep + 'dealink_source=1';
  }
}

// ========================================
// Demo Products — shown when no real results found
// ========================================
const DEMO_PRODUCTS = [
  { store: 'Amazon',     platform: 'amazon',     price: 68.50, price_str: '$68.50', url: 'https://www.amazon.com',       rating: 4.5, reviews: 2847, condition: 'new' },
  { store: 'eBay',       platform: 'ebay',        price: 61.99, price_str: '$61.99', url: 'https://www.ebay.com',         rating: 4.2, reviews: 456,  condition: 'new' },
  { store: 'Walmart',    platform: 'walmart',     price: 71.00, price_str: '$71.00', url: 'https://www.walmart.com',      rating: 4.0, reviews: 123,  condition: 'new' },
  { store: 'Best Buy',   platform: 'bestbuy',     price: 79.99, price_str: '$79.99', url: 'https://www.bestbuy.com',      rating: 4.3, reviews: 891,  condition: 'new' },
  { store: 'AliExpress', platform: 'aliexpress',  price: 48.30, price_str: '$48.30', url: 'https://www.aliexpress.com',   rating: 3.8, reviews: 3200, condition: 'new' },
];
const DEMO_CURRENT_PRICE = 99.99;

// ========================================
// Sort / Filter State
// ========================================
const INITIAL_VISIBLE = 3; // 1 best deal + 2 more cards shown initially
let currentSort = 'price'; // 'price' | 'popularity' | 'rating'
let currentResults = [];   // keep a reference for re-sorting
let currentOriginalPrice = 0;
let currentCurrency = 'USD';
let isExpanded = false;     // tracks whether "Show More" is open

// ========================================
// State Management
// ========================================

const States = {
  LOADING: 'loading',
  RESULTS: 'results', 
  NO_PRODUCT: 'no-product',
  NO_DEALS: 'no-deals',
  ERROR: 'error'
};

function showState(state) {
  ['loading', 'results', 'no-product', 'no-deals', 'error'].forEach(s => {
    const el = document.getElementById(`state-${s}`);
    if (el) el.classList.toggle('hidden', s !== state);
  });
}

// ========================================
// Progress Animation
// ========================================

let progressInterval = null;
let patienceTimeout = null;

function startProgressAnimation() {
  const fill = document.getElementById('progress-fill');
  const text = document.getElementById('progress-text');
  const subtitle = document.getElementById('loading-msg');
  let progress = 0;

  // Progress stages with descriptive messages
  const stages = [
    { at: 15, msg: 'מזהה את המוצר...' },
    { at: 35, msg: 'מחפש דילים מדויקים...' },
    { at: 55, msg: 'משווה מחירים בחנויות...' },
    { at: 75, msg: 'בודק מבצעים נוספים...' },
    { at: 90, msg: 'מסיים...' },
  ];

  progressInterval = setInterval(() => {
    // Slow down as we approach 90%
    const increment = progress < 60 ? 3 : progress < 80 ? 1 : 0.5;
    progress = Math.min(progress + increment, 90);

    fill.style.width = progress + '%';
    text.textContent = Math.round(progress) + '%';

    // Update subtitle text at each stage
    if (subtitle) {
      for (let i = stages.length - 1; i >= 0; i--) {
        if (progress >= stages[i].at) {
          subtitle.textContent = stages[i].msg;
          break;
        }
      }
    }
  }, 100);

  // After 6 seconds, show patience message
  patienceTimeout = setTimeout(() => {
    if (subtitle) {
      subtitle.textContent = 'עדיין מחפש... תודה על הסבלנות! 🔍';
    }
  }, 6000);
}

function completeProgress(callback) {
  if (progressInterval) {
    clearInterval(progressInterval);
    progressInterval = null;
  }
  if (patienceTimeout) {
    clearTimeout(patienceTimeout);
    patienceTimeout = null;
  }
  
  const fill = document.getElementById('progress-fill');
  const text = document.getElementById('progress-text');
  
  fill.style.width = '100%';
  text.textContent = '100%';
  
  // Small delay before showing results
  setTimeout(callback, 300);
}

function stopProgress() {
  if (progressInterval) {
    clearInterval(progressInterval);
    progressInterval = null;
  }
  if (patienceTimeout) {
    clearTimeout(patienceTimeout);
    patienceTimeout = null;
  }
}

function showDemoResults() {
  const banner = document.getElementById('demo-banner');
  if (banner) banner.classList.remove('hidden');
  renderResults(DEMO_PRODUCTS, DEMO_CURRENT_PRICE, 'USD');
}

// ========================================
// Render Functions  
// ========================================

function renderBestDealCard(bestDeal, originalPrice, currency) {
  const card = document.getElementById('best-deal-card');
  const price = bestDeal.total || bestDeal.price;
  const savings = calcSavingsAmount(originalPrice, price);
  const percent = calcSavingsPercent(originalPrice, price);

  // ── Hero savings banner ──
  const heroBanner = document.getElementById('hero-banner');
  if (heroBanner) {
    if (savings > 0) {
      const amountEl = document.getElementById('hero-amount');
      const subEl = document.getElementById('hero-sub');
      if (amountEl) amountEl.textContent = formatPrice(savings, currency);
      if (subEl) subEl.textContent = `-${percent}%`;
      heroBanner.classList.remove('hidden');
    } else {
      heroBanner.classList.add('hidden');
    }
  }

  // ── Savings strip inside card ──
  const savingsEl = document.getElementById('best-deal-savings');
  if (savingsEl) {
    savingsEl.textContent = savings > 0
      ? `חוסך ${formatPrice(savings, currency)} (${percent}%) לעומת המחיר הנוכחי`
      : '';
  }

  // ── Store info ──
  document.getElementById('best-deal-logo').src = getStoreLogo(bestDeal.platform);
  document.getElementById('best-deal-store-name').textContent = getStoreName(bestDeal.platform);

  // ── Discount badge ──
  const badge = document.getElementById('best-deal-badge');
  if (percent > 0) {
    badge.textContent = `-${percent}%`;
    badge.style.display = 'inline-flex';
  } else {
    badge.style.display = 'none';
  }

  // ── Price ──
  document.getElementById('best-deal-price').textContent = formatPrice(price, currency);

  // ── Shipping ──
  const shippingEl = document.getElementById('best-deal-shipping');
  if (bestDeal.shipping === 0) {
    shippingEl.textContent = 'משלוח חינם ✓';
  } else if (bestDeal.shipping > 0) {
    shippingEl.textContent = `+ ${formatPrice(bestDeal.shipping, currency)} משלוח`;
  } else {
    shippingEl.textContent = '';
  }

  // ── Rating / reviews ──
  const bestMeta = document.getElementById('best-deal-meta');
  if (bestMeta) {
    let metaHtml = '';
    if (bestDeal.rating && bestDeal.rating > 0) {
      metaHtml += `${starSvg()} ${bestDeal.rating.toFixed(1)}`;
      if (bestDeal.reviews && bestDeal.reviews > 0) {
        metaHtml += ` <span style="color:var(--text-4)">(${formatReviews(bestDeal.reviews)})</span>`;
      }
    }
    bestMeta.innerHTML = metaHtml;
  }

  // ── Buy link — open in new tab without closing popup ──
  const bestDealLink = document.getElementById('best-deal-link');
  const bestDealUrl = addDealinkParam(bestDeal.url || '#');
  bestDealLink.href = '#';
  bestDealLink.removeAttribute('target');
  // Clone to remove any stale listeners
  const newLink = bestDealLink.cloneNode(true);
  bestDealLink.parentNode.replaceChild(newLink, bestDealLink);
  newLink.addEventListener('click', (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: bestDealUrl, active: false });
  });

  card.classList.remove('hidden');
}

function createResultCard(result, originalPrice, currency) {
  const price = result.total || result.price;
  const savings = calcSavingsPercent(originalPrice, price);
  const dealUrl = addDealinkParam(result.url || '#');

  const row = document.createElement('div');
  row.className = 'deal-row';

  // Badge
  let badgeHtml = '';
  if (savings > 0) {
    badgeHtml = `<span class="deal-badge save">-${savings}%</span>`;
  } else if (savings < 0) {
    badgeHtml = `<span class="deal-badge more">+${Math.abs(savings)}%</span>`;
  }

  // Rating
  let ratingHtml = '';
  if (result.rating && result.rating > 0) {
    ratingHtml = `<span class="deal-rating">${starSvg()} ${result.rating.toFixed(1)}</span>`;
    if (result.reviews && result.reviews > 0) {
      ratingHtml += `<span class="deal-reviews">(${formatReviews(result.reviews)})</span>`;
    }
  }

  row.innerHTML = `
    <img src="${getStoreLogo(result.platform)}" alt="${getStoreName(result.platform)}" class="store-icon sm">
    <div class="deal-info">
      <div class="deal-store">${getStoreName(result.platform)}</div>
      ${ratingHtml ? `<div class="deal-meta">${ratingHtml}</div>` : ''}
    </div>
    <div class="deal-right">
      <span class="deal-price">${formatPrice(price, currency)}</span>
      ${badgeHtml}
    </div>
    <div class="deal-arrow">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
        <polyline points="15 3 21 3 21 9"/>
        <line x1="10" y1="14" x2="21" y2="3"/>
      </svg>
    </div>
  `;

  row.addEventListener('click', (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: dealUrl, active: false });
    if (typeof DealinkAnalytics !== 'undefined') {
      DealinkAnalytics.trackDealClicked(result.platform, savings, 0);
    }
  });

  return row;
}

function sortResults(results, sortBy) {
  const sorted = [...results];
  switch (sortBy) {
    case 'price':
      sorted.sort((a, b) => (a.total || a.price || Infinity) - (b.total || b.price || Infinity));
      break;
    case 'popularity':
      // Sort by number of reviews (more reviews = more popular), no reviews goes last
      sorted.sort((a, b) => (b.reviews || 0) - (a.reviews || 0));
      break;
    case 'rating':
      // Sort by rating (higher first), no rating goes last
      sorted.sort((a, b) => (b.rating || 0) - (a.rating || 0));
      break;
    default:
      sorted.sort((a, b) => (a.total || a.price || Infinity) - (b.total || b.price || Infinity));
  }
  return sorted;
}

/**
 * Core render: shows top INITIAL_VISIBLE results, hides the rest behind "Show More"
 */
function renderSortedCards(sorted, originalPrice, currency) {
  const container = document.getElementById('results-list');
  const extraContainer = document.getElementById('results-list-extra');
  const showMoreBtn = document.getElementById('show-more-btn');
  const showMoreText = document.getElementById('show-more-text');
  const showMoreCount = document.getElementById('show-more-count');

  container.innerHTML = '';
  extraContainer.innerHTML = '';

  // Best deal = sorted[0], rest starts at index 1
  renderBestDealCard(sorted[0], originalPrice, currency);

  // Initial visible cards (indices 1 to INITIAL_VISIBLE-1)
  const initialCards = sorted.slice(1, INITIAL_VISIBLE);
  initialCards.forEach((result) => {
    container.appendChild(createResultCard(result, originalPrice, currency));
  });

  // Extra cards (hidden behind "Show More")
  const extraCards = sorted.slice(INITIAL_VISIBLE);

  if (extraCards.length > 0) {
    extraCards.forEach((result) => {
      extraContainer.appendChild(createResultCard(result, originalPrice, currency));
    });

    // Update button
    showMoreCount.textContent = extraCards.length;
    showMoreBtn.classList.remove('hidden');

    // Restore expanded/collapsed state
    if (isExpanded) {
      extraContainer.classList.remove('hidden');
      showMoreText.textContent = 'הצג פחות';
      showMoreBtn.classList.add('expanded');
    } else {
      extraContainer.classList.add('hidden');
      showMoreText.textContent = 'הצג עוד תוצאות';
      showMoreBtn.classList.remove('expanded');
    }
  } else {
    showMoreBtn.classList.add('hidden');
    extraContainer.classList.add('hidden');
  }
}

function renderResults(results, originalPrice, currency) {
  if (!results || results.length === 0) {
    showState(States.NO_DEALS);
      return;
    }

  // Save for re-sorting later
  currentResults = results;
  currentOriginalPrice = originalPrice;
  currentCurrency = currency;
  isExpanded = false; // reset on fresh render
  
  const sorted = sortResults(results, currentSort);
  renderSortedCards(sorted, originalPrice, currency);
  
  showState(States.RESULTS);
}

/**
 * Re-render results when the user changes sort order
 */
function reRenderWithSort(sortBy) {
  if (!currentResults || currentResults.length === 0) return;
  
  currentSort = sortBy;
  isExpanded = false; // collapse back to top 3 on sort change
  
  // Update active button
  document.querySelectorAll('.spill').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.sort === sortBy);
  });
  
  const sorted = sortResults(currentResults, sortBy);
  renderSortedCards(sorted, currentOriginalPrice, currentCurrency);
}

/**
 * Toggle Show More / Show Less
 */
function toggleShowMore() {
  const extraContainer = document.getElementById('results-list-extra');
  const showMoreBtn = document.getElementById('show-more-btn');
  const showMoreText = document.getElementById('show-more-text');

  isExpanded = !isExpanded;
  if (isExpanded && typeof DealinkAnalytics !== 'undefined') DealinkAnalytics.trackShowMore();

  if (isExpanded) {
    extraContainer.classList.remove('hidden');
    showMoreText.textContent = 'הצג פחות';
    showMoreBtn.classList.add('expanded');
  } else {
    extraContainer.classList.add('hidden');
    showMoreText.textContent = 'הצג עוד תוצאות';
    showMoreBtn.classList.remove('expanded');
  }
}

function renderUsedProducts(products, originalPrice, currency) {
  const section = document.getElementById('used-section');
  const list = document.getElementById('used-list');
  const countBadge = document.getElementById('used-count-badge');
  
  if (!products || products.length === 0) {
    section.classList.add('hidden');
    return;
  }

  section.classList.remove('hidden');
  countBadge.textContent = products.length;
  list.innerHTML = '';
  
  // Sort used products by price
  const sorted = [...products].sort((a, b) => (a.total || a.price) - (b.total || b.price));
  
  sorted.forEach(product => {
    const card = createResultCard(product, originalPrice, currency);
    
    // Add a "used/refurbished" badge to the store name
    const storeNameEl = card.querySelector('.deal-store');
    if (storeNameEl) {
      const condition = product.condition === 'refurbished' ? 'מחודש' : 'משומש';
      storeNameEl.innerHTML += ` <span class="used-badge">${condition}</span>`;
    }
    
    list.appendChild(card);
  });
  
  // Toggle click handler is set up in DOMContentLoaded
}

function renderSimilar(products, currency) {
  const section = document.getElementById('similar-section');
  const list = document.getElementById('similar-list');
  
  if (!products || products.length === 0) {
    section.classList.add('hidden');
      return;
    }

  section.classList.remove('hidden');
  list.innerHTML = '';
  
  products.forEach(product => {
    const card = createResultCard(product, null, currency);
    list.appendChild(card);
  });
}

// ========================================
// Report Issue
// ========================================

async function reportIssue() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const { dealinkResult, dealinkProduct } = await chrome.storage.local.get(['dealinkResult', 'dealinkProduct']);
    
    const report = {
      url: tab?.url,
      timestamp: new Date().toISOString(),
      product: dealinkProduct,
      result: dealinkResult
    };
    
    await navigator.clipboard.writeText(JSON.stringify(report, null, 2));
    alert('פרטי הדיווח הועתקו! שלח אותם במייל.');
  } catch (e) {
    alert('שגיאה ביצירת הדיווח');
  }
}

// ========================================
// Main Initialization
// ========================================

document.addEventListener('DOMContentLoaded', async () => {
  // Event listeners
  document.getElementById('close-btn')?.addEventListener('click', () => window.close());
  document.getElementById('retry-btn')?.addEventListener('click', () => {
    showState(States.LOADING);
    startProgressAnimation();
    chrome.runtime.sendMessage({ type: 'RETRY_FETCH' });
    if (typeof DealinkAnalytics !== 'undefined') DealinkAnalytics.trackRetry();
  });
  document.getElementById('report-btn')?.addEventListener('click', reportIssue);
  document.getElementById('similar-toggle')?.addEventListener('click', (e) => {
    e.currentTarget.classList.toggle('expanded');
    document.getElementById('similar-list').classList.toggle('hidden');
  });
  
  // Used/Refurbished toggle
  document.getElementById('used-toggle')?.addEventListener('click', (e) => {
    e.currentTarget.classList.toggle('expanded');
    document.getElementById('used-list').classList.toggle('hidden');
  });
  
  // Sort buttons
  document.querySelectorAll('.spill').forEach(btn => {
    btn.addEventListener('click', () => {
      const sortBy = btn.dataset.sort;
      if (sortBy && sortBy !== currentSort) {
        reRenderWithSort(sortBy);
        if (typeof DealinkAnalytics !== 'undefined') DealinkAnalytics.trackSortChanged(sortBy);
      }
    });
  });
  
  // Show More button
  document.getElementById('show-more-btn')?.addEventListener('click', toggleShowMore);
  
  // Get the current tab URL for checks
  const [currentTab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const currentUrl = currentTab?.url || '';
  
  // If user arrived from a Dealink link, show "already checked"
  if (currentUrl.includes('dealink_source=1')) {
    showState(States.NO_DEALS);
    document.querySelector('#state-no-deals .state-icon').textContent = '✅';
    document.querySelector('#state-no-deals .state-title').textContent = 'כבר בדקנו!';
    document.querySelector('#state-no-deals .state-sub').textContent = 'הגעת לכאן דרך Dealink — זה הדיל הכי טוב שמצאנו.';
    return;
  }
  
  // Try to get results: first from cache (URL-specific), then from global dealinkResult
  let dealinkResult = null;
  let dealinkProduct = null;
  
  // 1. Check URL-specific cache (most reliable — tied to THIS product page)
  const cacheKey = `dealink_cache_${currentUrl.split('?')[0]}`; // strip query params for cache
  const cacheData = await chrome.storage.local.get([cacheKey]);
  if (cacheData[cacheKey]?.data) {
    dealinkResult = cacheData[cacheKey].data;
  }
  
  // 2. Fall back to global dealinkResult (set by background.js for the last product)
  if (!dealinkResult) {
    const stored = await chrome.storage.local.get(['dealinkResult', 'dealinkProduct']);
    dealinkResult = stored.dealinkResult;
    dealinkProduct = stored.dealinkProduct;
  } else {
    // Also get product info
    const stored = await chrome.storage.local.get(['dealinkProduct']);
    dealinkProduct = stored.dealinkProduct;
  }
  
  // If no data, check if we're on a product page
  if (!dealinkResult) {
    const isProductPage = /amazon|ebay|walmart|aliexpress|bestbuy|target|newegg|ksp|ivory|bug\.co\.il|currys|argos|otto\.de|bol\.com|cdiscount|coolblue|mediamarkt|conrad|jbhifi|flipkart|mercadolibre|mercadolivre/i.test(currentUrl);
    
    if (isProductPage) {
      // Show loading and wait for data
      showState(States.LOADING);
      startProgressAnimation();
      
      // Proactively ask the content script to rescan (in case it hasn't run yet)
      try {
        chrome.tabs.sendMessage(currentTab.id, { action: 'RESCAN_PAGE' });
      } catch (e) { /* content script might not be ready */ }
      
      // Poll every 1.5s for up to 20 seconds
      let checkCount = 0;
      const checkInterval = setInterval(async () => {
        checkCount++;
        
        // Check both global result and URL-specific cache
        const { dealinkResult: newResult } = await chrome.storage.local.get('dealinkResult');
        const urlCache = await chrome.storage.local.get([cacheKey]);
        const cachedResult = urlCache[cacheKey]?.data;
        
        if (newResult || cachedResult) {
          clearInterval(checkInterval);
          location.reload();
        } else if (checkCount >= 22) {
          // After ~33 seconds (22 × 1.5s), give up and show demo
          clearInterval(checkInterval);
          completeProgress(() => showDemoResults());
        }
      }, 1500);
    } else {
      showState(States.NO_PRODUCT);
    }
    return;
  }
  
  // Skip if this is a dealink_source result (shouldn't happen now, but safety check)
  if (dealinkResult.dealink_source) {
    showState(States.NO_DEALS);
    document.querySelector('#state-no-deals .state-icon').textContent = '✅';
    document.querySelector('#state-no-deals .state-title').textContent = 'כבר בדקנו!';
    document.querySelector('#state-no-deals .state-sub').textContent = 'הגעת לכאן דרך Dealink — זה הדיל הכי טוב שמצאנו.';
    return;
  }

  // Handle error — show demo instead of blank error
  if (dealinkResult.error) {
    showDemoResults();
    return;
  }

  // Data is already here — show results immediately (no artificial delay)
  const originalPrice = dealinkProduct?.price || dealinkResult.original_price;
  const currency = dealinkProduct?.currency || dealinkResult.currency || 'USD';
  const sameProducts = dealinkResult.same_products || [];
  const similarProducts = dealinkResult.similar_products || [];
  const usedProducts = dealinkResult.used_products || [];

  if (sameProducts.length === 0 && similarProducts.length === 0 && usedProducts.length === 0) {
    // No real results — show demo so popup is never empty
    showDemoResults();
    if (typeof DealinkAnalytics !== 'undefined') DealinkAnalytics.trackNoDeals();
  } else if (sameProducts.length === 0 && usedProducts.length > 0) {
    showState(States.RESULTS);
    document.getElementById('best-deal-card').classList.add('hidden');
    document.getElementById('sort-bar').classList.add('hidden');
    renderUsedProducts(usedProducts, originalPrice, currency);
    renderSimilar(similarProducts, currency);
  } else {
    renderResults(sameProducts, originalPrice, currency);
    renderUsedProducts(usedProducts, originalPrice, currency);
    renderSimilar(similarProducts, currency);
    if (typeof DealinkAnalytics !== 'undefined') {
      const bestPrice = sameProducts[0]?.total || sameProducts[0]?.price;
      const bestSavings = originalPrice && bestPrice ? Math.round(((originalPrice - bestPrice) / originalPrice) * 100) : 0;
      DealinkAnalytics.trackDealsFound(sameProducts.length, bestSavings, 0);
    }
  }
});

// Listen for updates
chrome.storage.onChanged.addListener((changes, namespace) => {
  if (namespace === 'local' && changes.dealinkResult) {
    location.reload();
  }
});
