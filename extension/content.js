// content.js - Dealink Product Detection
// Version 2.0 - With Structured Data Extraction

// =============================================================================
// PLATFORM DETECTION
// =============================================================================

function isProductPage() {
  const url = window.location.href;
  const hostname = window.location.hostname;
  
  // URL-based detection — covers all global domains
  const urlPatterns = {
    amazon: ['/dp/', '/gp/product/', '/product/'],
    ebay: ['/itm/'],
    walmart: ['/ip/'],
    aliexpress: ['/item/', '/i/'],
    target: ['/p/'],
    bestbuy: ['/site/'],
    newegg: ['/p/', '/Product/'],
    ksp: ['/web/item/'],
    ivory: ['/catalog.php'],
    bug: ['/item/'],
    flipkart: ['/p/'],
    mercadolibre: ['/MLM-', '/MLA-', '/MLB-', '/p/'],
    jbhifi: ['/products/'],
    currys: ['/products/'],
    argos: ['/product/'],
    otto: ['/p/'],
    mediamarkt: ['/product/'],
    bol: ['/p/'],
    coolblue: ['/product/'],
    cdiscount: ['/f-', '/v-'],
    conrad: ['/p/'],
  };
  
  for (const [platform, patterns] of Object.entries(urlPatterns)) {
    if (patterns.some(p => url.includes(p))) {
      return true;
    }
  }
  
  // DOM-based detection (for SPAs and unusual URLs — works on any site)
  const hasProductSchema = document.querySelector('script[type="application/ld+json"]');
  const hasProductMicrodata = document.querySelector('[itemtype*="Product"]');
  const hasAddToCart = document.querySelector('[data-action="add-to-cart"], .add-to-cart, #add-to-cart, .add_to_cart, [data-testid="add-to-cart"]');
  
  return hasProductSchema || hasProductMicrodata || hasAddToCart;
}

function detectPlatform() {
  const hostname = window.location.hostname;
  
  // Global platforms — all regional domains map to the same platform name
  if (hostname.includes('amazon')) return 'amazon';
  if (hostname.includes('ebay')) return 'ebay';
  if (hostname.includes('walmart')) return 'walmart';
  if (hostname.includes('aliexpress')) return 'aliexpress';
  if (hostname.includes('target')) return 'target';
  if (hostname.includes('bestbuy')) return 'bestbuy';
  if (hostname.includes('newegg')) return 'newegg';
  
  // Israel
  if (hostname.includes('ksp.co.il')) return 'ksp';
  if (hostname.includes('ivory.co.il')) return 'ivory';
  if (hostname.includes('bug.co.il')) return 'bug';
  
  // UK
  if (hostname.includes('currys.co.uk')) return 'currys';
  if (hostname.includes('argos.co.uk')) return 'argos';
  
  // EU
  if (hostname.includes('otto.de')) return 'otto';
  if (hostname.includes('mediamarkt')) return 'mediamarkt';
  if (hostname.includes('bol.com')) return 'bol';
  if (hostname.includes('coolblue')) return 'coolblue';
  if (hostname.includes('cdiscount')) return 'cdiscount';
  if (hostname.includes('conrad')) return 'conrad';
  
  // Australia
  if (hostname.includes('jbhifi')) return 'jbhifi';
  
  // India
  if (hostname.includes('flipkart')) return 'flipkart';
  
  // Latin America
  if (hostname.includes('mercadolibre') || hostname.includes('mercadolivre')) return 'mercadolibre';
  
  return 'unknown';
}

// =============================================================================
// STRUCTURED DATA EXTRACTION (JSON-LD, Microdata, Meta tags)
// =============================================================================

function extractStructuredData() {
  const data = {
    brand: null,
    model: null,
    color: null,
    capacity: null,
    sku: null,
    gtin: null,
    mpn: null,
    category: null,
    description: null,
    price: null,
    currency: null,
    availability: null,
    condition: null,
    rating: null,
    reviewCount: null,
    image: null,
    source: null, // Where the data came from
  };

  // 1. Try JSON-LD first (most reliable - used by Amazon, Walmart, Best Buy)
  const jsonLdData = extractJsonLd();
  if (jsonLdData) {
    Object.assign(data, jsonLdData);
    data.source = 'json-ld';
  }

  // 2. Try Microdata/RDFa (used by eBay, some others)
  if (!data.brand) {
    const microdataData = extractMicrodata();
    if (microdataData) {
      // Merge only missing fields
      for (const [key, value] of Object.entries(microdataData)) {
        if (!data[key] && value) {
          data[key] = value;
        }
      }
      if (!data.source) data.source = 'microdata';
    }
  }

  // 3. Try Open Graph / Meta tags (fallback)
  if (!data.brand) {
    const metaData = extractMetaTags();
    for (const [key, value] of Object.entries(metaData)) {
      if (!data[key] && value) {
        data[key] = value;
      }
    }
    if (!data.source && Object.values(metaData).some(v => v)) {
      data.source = 'meta';
    }
  }

  // 4. Platform-specific extraction (for fields not in structured data)
  const platformData = extractPlatformSpecific();
  for (const [key, value] of Object.entries(platformData)) {
    if (!data[key] && value) {
      data[key] = value;
    }
  }

  return data;
}

function extractJsonLd() {
  const scripts = document.querySelectorAll('script[type="application/ld+json"]');
  
  for (const script of scripts) {
    try {
      let json = JSON.parse(script.textContent);
      
      // Handle @graph structure (common in some sites)
      if (json['@graph']) {
        json = json['@graph'].find(item => 
          item['@type'] === 'Product' || 
          (Array.isArray(item['@type']) && item['@type'].includes('Product'))
        );
      }
      
      // Handle array of items
      if (Array.isArray(json)) {
        json = json.find(item => 
          item['@type'] === 'Product' || 
          (Array.isArray(item['@type']) && item['@type'].includes('Product'))
        );
      }
      
      if (!json || (json['@type'] !== 'Product' && 
          !(Array.isArray(json['@type']) && json['@type'].includes('Product')))) {
        continue;
      }

      const data = {};
      
      // Brand
      if (json.brand) {
        data.brand = typeof json.brand === 'object' ? json.brand.name : json.brand;
      }
      
      // Model / SKU / MPN
      data.model = json.model || json.productID;
      data.sku = json.sku;
      data.mpn = json.mpn;
      data.gtin = json.gtin || json.gtin13 || json.gtin12 || json.gtin14 || json.gtin8;
      
      // Color (sometimes in additionalProperty or directly)
      if (json.color) {
        data.color = typeof json.color === 'object' ? json.color.name : json.color;
      }
      if (!data.color && json.additionalProperty) {
        const colorProp = json.additionalProperty.find(p => 
          p.name?.toLowerCase() === 'color' || p.propertyID === 'color'
        );
        if (colorProp) data.color = colorProp.value;
      }
      
      // Capacity (look in name, description, or additionalProperty)
      const capacityMatch = (json.name + ' ' + (json.description || '')).match(/(\d+)\s*(GB|TB)/i);
      if (capacityMatch) {
        data.capacity = capacityMatch[0];
      }
      
      // Category
      if (json.category) {
        data.category = typeof json.category === 'object' ? json.category.name : json.category;
      }
      
      // Description
      data.description = json.description?.substring(0, 500); // Limit length
      
      // Price from offers
      if (json.offers) {
        const offer = Array.isArray(json.offers) ? json.offers[0] : json.offers;
        data.price = parseFloat(offer.price) || null;
        data.currency = offer.priceCurrency;
        data.availability = offer.availability?.split('/').pop(); // Get last part of URL
      }
      
      // Condition
      if (json.itemCondition) {
        const condition = json.itemCondition.split('/').pop();
        data.condition = condition.replace('Condition', '');
      }
      
      // Rating
      if (json.aggregateRating) {
        data.rating = parseFloat(json.aggregateRating.ratingValue);
        data.reviewCount = parseInt(json.aggregateRating.reviewCount) || 
                          parseInt(json.aggregateRating.ratingCount);
      }
      
      // Image
      if (json.image) {
        data.image = Array.isArray(json.image) ? json.image[0] : 
                    (typeof json.image === 'object' ? json.image.url : json.image);
      }

      return data;
      
    } catch (e) {
      console.log('[Dealink] JSON-LD parse error:', e.message);
    }
  }
  
  return null;
}

function extractMicrodata() {
  const data = {};
  
  // Find product container
  const product = document.querySelector('[itemtype*="schema.org/Product"], [itemtype*="Product"]');
  
  if (product) {
    // Brand
    const brandEl = product.querySelector('[itemprop="brand"]');
    if (brandEl) {
      data.brand = brandEl.content || brandEl.textContent?.trim();
      // Sometimes brand has nested name
      const brandName = brandEl.querySelector('[itemprop="name"]');
      if (brandName) data.brand = brandName.content || brandName.textContent?.trim();
    }
    
    // Model
    const modelEl = product.querySelector('[itemprop="model"]');
    data.model = modelEl?.content || modelEl?.textContent?.trim();
    
    // SKU
    const skuEl = product.querySelector('[itemprop="sku"]');
    data.sku = skuEl?.content || skuEl?.textContent?.trim();
    
    // MPN
    const mpnEl = product.querySelector('[itemprop="mpn"]');
    data.mpn = mpnEl?.content || mpnEl?.textContent?.trim();
    
    // GTIN
    const gtinEl = product.querySelector('[itemprop="gtin"], [itemprop="gtin13"], [itemprop="gtin12"]');
    data.gtin = gtinEl?.content || gtinEl?.textContent?.trim();
    
    // Color
    const colorEl = product.querySelector('[itemprop="color"]');
    data.color = colorEl?.content || colorEl?.textContent?.trim();
    
    // Price
    const priceEl = product.querySelector('[itemprop="price"]');
    if (priceEl) {
      data.price = parseFloat(priceEl.content || priceEl.textContent?.replace(/[^\d.]/g, ''));
    }
    
    // Image
    const imageEl = product.querySelector('[itemprop="image"]');
    data.image = imageEl?.content || imageEl?.src;
  }
  
  return data;
}

function extractMetaTags() {
  const data = {};
  
  // Open Graph product tags
  const ogBrand = document.querySelector('meta[property="product:brand"], meta[property="og:brand"]');
  data.brand = ogBrand?.content;
  
  const ogPrice = document.querySelector('meta[property="product:price:amount"], meta[property="og:price:amount"]');
  data.price = ogPrice ? parseFloat(ogPrice.content) : null;
  
  const ogCurrency = document.querySelector('meta[property="product:price:currency"], meta[property="og:price:currency"]');
  data.currency = ogCurrency?.content;
  
  const ogImage = document.querySelector('meta[property="og:image"]');
  data.image = ogImage?.content;
  
  // Standard meta tags
  const metaGtin = document.querySelector('meta[name="gtin"], meta[property="product:gtin"]');
  data.gtin = metaGtin?.content;
  
  const metaMpn = document.querySelector('meta[name="mpn"], meta[property="product:mpn"]');
  data.mpn = metaMpn?.content;
  
  const metaSku = document.querySelector('meta[name="sku"], meta[property="product:sku"]');
  data.sku = metaSku?.content;
  
  return data;
}

function extractPlatformSpecific() {
  const platform = detectPlatform();
  const data = {};
  
  switch (platform) {
    case 'amazon':
      // Brand from byline - clean up "Visit the X Store" pattern
      const byline = document.querySelector('#bylineInfo, #brand, a#bylineInfo');
      if (byline) {
        let brandText = byline.textContent?.trim() || '';
        // Remove common prefixes/suffixes
        brandText = brandText
          .replace(/^Visit the\s+/i, '')
          .replace(/^Brand:\s*/i, '')
          .replace(/\s+Store$/i, '')
          .replace(/\s+Official$/i, '')
          .replace(/\s+on Amazon$/i, '')
          .trim();
        if (brandText) data.brand = brandText;
      }
      
      // Also try to get brand from product details table
      if (!data.brand) {
        const brandRow = document.querySelector('#productDetails_detailBullets_sections1 tr:has(th:contains("Brand")) td');
        if (brandRow) data.brand = brandRow.textContent?.trim();
      }
      
      // Try technical details table
      const techDetails = document.querySelector('#productDetails_techSpec_section_1, #detailBullets_feature_div, #prodDetails');
      if (techDetails) {
        const text = techDetails.textContent;
        
        // Brand from table
        if (!data.brand) {
          const brandMatch = text.match(/Brand[:\s]+([A-Za-z0-9\s&'-]+?)(?:\n|$)/i);
          if (brandMatch) data.brand = brandMatch[1].trim();
        }
        
        // Model Number
        const modelMatch = text.match(/(?:Model|Item)\s*(?:Number|Name)?[:\s]*([A-Z0-9-]+)/i);
        if (modelMatch) data.model = modelMatch[1];
        
        // Color
        const colorMatch = text.match(/Colo(?:u)?r[:\s]*([A-Za-z\s\/]+?)(?:\n|,|$)/i);
        if (colorMatch) data.color = colorMatch[1].trim();
      }
      
      // ASIN from URL or page
      const asinMatch = window.location.href.match(/\/dp\/([A-Z0-9]{10})/);
      if (asinMatch) data.asin = asinMatch[1];
      
      // Try to get brand from title if still missing (first word often is brand)
      if (!data.brand) {
        const title = document.querySelector('#productTitle')?.textContent?.trim();
        if (title) {
          const firstWord = title.split(/\s+/)[0];
          // Check if it looks like a brand (capitalized, not a common word)
          const commonWords = ['the', 'new', 'original', 'genuine', 'authentic', 'official', 'premium'];
          if (firstWord && !commonWords.includes(firstWord.toLowerCase()) && /^[A-Z]/.test(firstWord)) {
            data.brand = firstWord;
          }
        }
      }
      break;
      
    case 'ebay':
      // eBay specifics
      const ebayBrand = document.querySelector('.ux-labels-values--brand .ux-labels-values__values-content span');
      if (ebayBrand) data.brand = ebayBrand.textContent?.trim();
      
      const ebayMpn = document.querySelector('.ux-labels-values--mpn .ux-labels-values__values-content span');
      if (ebayMpn) data.mpn = ebayMpn.textContent?.trim();
      
      // eBay UPC/EAN from item specifics section
      const ebaySpecifics = document.querySelectorAll('.ux-labels-values__labels, .ux-labels-values-with-hints__labels');
      for (const label of ebaySpecifics) {
        const labelText = (label.textContent || '').trim().toLowerCase();
        const valueEl = label.nextElementSibling || label.closest('.ux-labels-values')?.querySelector('.ux-labels-values__values-content');
        const valueText = (valueEl?.textContent || '').trim();
        
        if (labelText.includes('upc') && /^\d{12}$/.test(valueText)) {
          data.upc = valueText;
          console.log('[Dealink] eBay UPC:', data.upc);
        }
        if (labelText.includes('ean') && /^\d{13}$/.test(valueText)) {
          data.ean = valueText;
          console.log('[Dealink] eBay EAN:', data.ean);
        }
        if (labelText.includes('gtin') && /^\d{8,14}$/.test(valueText)) {
          data.gtin = valueText;
          console.log('[Dealink] eBay GTIN:', data.gtin);
        }
      }
      
      // Item condition
      const condition = document.querySelector('[data-testid="ux-labels-values-label"]:has(+ [data-testid="ux-labels-values-value"] span)');
      if (condition?.textContent?.includes('Condition')) {
        data.condition = condition.nextElementSibling?.textContent?.trim();
      }
      break;
      
    case 'walmart':
      // Walmart specifics
      const walmartBrand = document.querySelector('[data-testid="product-brand"]');
      if (walmartBrand) data.brand = walmartBrand.textContent?.trim();
      
      // Walmart UPC/GTIN from product details
      const walmartSpecs = document.querySelectorAll('.dangerous-html table tr, [data-testid="product-specification"] tr, .specification-table tr');
      for (const row of walmartSpecs) {
        const cells = row.querySelectorAll('td, th');
        if (cells.length >= 2) {
          const label = (cells[0].textContent || '').trim().toLowerCase();
          const value = (cells[1].textContent || '').trim();
          if (label.includes('upc') && /^\d{12}$/.test(value)) {
            data.upc = value;
            console.log('[Dealink] Walmart UPC:', data.upc);
          }
          if (label.includes('gtin') && /^\d{8,14}$/.test(value)) {
            data.gtin = value;
            console.log('[Dealink] Walmart GTIN:', data.gtin);
          }
        }
      }
      
      // Walmart also has UPC in hidden data attributes
      const walmartUpcMeta = document.querySelector('meta[itemprop="gtin13"], meta[itemprop="gtin12"]');
      if (walmartUpcMeta?.content) {
        const val = walmartUpcMeta.content;
        if (/^\d{12}$/.test(val)) data.upc = val;
        else if (/^\d{13}$/.test(val)) data.ean = val;
        else data.gtin = val;
        console.log('[Dealink] Walmart meta GTIN:', val);
      }
      break;
      
    case 'aliexpress':
      // AliExpress - often has brand in breadcrumbs or title
      const aliBrand = document.querySelector('.store-header-title, [data-role="store-name"]');
      if (aliBrand) data.brand = aliBrand.textContent?.trim();
      break;
      
    case 'bestbuy':
      // Best Buy specifics (US + CA)
      const bbBrand = document.querySelector('.sku-header [data-track="brand"]');
      if (bbBrand) data.brand = bbBrand.textContent?.trim();
      
      const bbModel = document.querySelector('.model-number .model');
      if (bbModel) data.model = bbModel.textContent?.trim();
      
      // BestBuy UPC from specifications tab/section
      const bbSpecs = document.querySelectorAll('.specs-table tr, .specification-table tr, .shop-specifications tr');
      for (const row of bbSpecs) {
        const thEl = row.querySelector('th, td:first-child');
        const tdEl = row.querySelector('td:last-child');
        if (thEl && tdEl) {
          const label = (thEl.textContent || '').trim().toLowerCase();
          const value = (tdEl.textContent || '').trim();
          if (label.includes('upc') && /^\d{12}$/.test(value)) {
            data.upc = value;
            console.log('[Dealink] BestBuy UPC:', data.upc);
          }
        }
      }
      
      // BestBuy SKU (useful for exact search)
      const bbSku = document.querySelector('.sku-value, .model-data .sku .product-data-value');
      if (bbSku) {
        data.sku = bbSku.textContent?.trim();
        console.log('[Dealink] BestBuy SKU:', data.sku);
      }
      break;
    
    // === Israel ===
    case 'ksp':
      // KSP product pages — structured data (JSON-LD) should handle most fields
      // Supplement with KSP-specific selectors
      const kspBrand = document.querySelector('.brandName, .product-brand, [data-test="brand"]');
      if (kspBrand) data.brand = kspBrand.textContent?.trim();
      
      const kspSku = document.querySelector('.product-sku, .sku-value, [data-test="sku"]');
      if (kspSku) {
        const skuText = kspSku.textContent?.trim().replace(/[^\w-]/g, '');
        if (skuText) data.sku = skuText;
      }
      
      // KSP barcode/GTIN from product details
      const kspDetails = document.querySelectorAll('.product-details-section tr, .product-specs tr');
      for (const row of kspDetails) {
        const cells = row.querySelectorAll('td');
        if (cells.length >= 2) {
          const label = (cells[0].textContent || '').trim().toLowerCase();
          const value = (cells[1].textContent || '').trim();
          if ((label.includes('ברקוד') || label.includes('barcode') || label.includes('gtin')) && /^\d{8,14}$/.test(value)) {
            data.gtin = value;
            console.log('[Dealink] KSP GTIN:', data.gtin);
          }
          if ((label.includes('יצרן') || label.includes('brand') || label.includes('מותג')) && value) {
            if (!data.brand) data.brand = value;
          }
        }
      }
      break;
    
    case 'ivory':
      // Ivory product pages
      const ivoryBrand = document.querySelector('.product-brand, .brand-name');
      if (ivoryBrand) data.brand = ivoryBrand.textContent?.trim();
      break;
    
    case 'bug':
      // Bug.co.il product pages
      const bugBrand = document.querySelector('.product-brand, .brand');
      if (bugBrand) data.brand = bugBrand.textContent?.trim();
      break;
    
    // === UK ===
    case 'currys':
      // Currys product pages
      const currysBrand = document.querySelector('[data-product="brand"], .product-brand');
      if (currysBrand) data.brand = currysBrand.textContent?.trim();
      
      const currysModel = document.querySelector('[data-product="model"]');
      if (currysModel) data.model = currysModel.textContent?.trim();
      
      // Currys EAN from product specs
      const currysSpecs = document.querySelectorAll('.product-spec-table tr, .specification tr');
      for (const row of currysSpecs) {
        const cells = row.querySelectorAll('td, th');
        if (cells.length >= 2) {
          const label = (cells[0].textContent || '').trim().toLowerCase();
          const value = (cells[1].textContent || '').trim();
          if (label.includes('ean') && /^\d{13}$/.test(value)) {
            data.ean = value;
            console.log('[Dealink] Currys EAN:', data.ean);
          }
        }
      }
      break;
    
    case 'argos':
      const argosBrand = document.querySelector('[data-test="product-brand"], .product-brand');
      if (argosBrand) data.brand = argosBrand.textContent?.trim();
      break;
    
    // === EU ===
    case 'otto':
      const ottoBrand = document.querySelector('.prd_brand__brand, [data-qa="productBrand"]');
      if (ottoBrand) data.brand = ottoBrand.textContent?.trim();
      break;
    
    case 'mediamarkt':
      const mmBrand = document.querySelector('[data-test="product-brand"], .product-brand');
      if (mmBrand) data.brand = mmBrand.textContent?.trim();
      break;
    
    case 'bol':
      // Bol.com (Netherlands/Belgium)
      const bolBrand = document.querySelector('[data-test="product-brand"], .pdp-header__brand');
      if (bolBrand) data.brand = bolBrand.textContent?.trim();
      
      // Bol.com EAN from product specs
      const bolSpecs = document.querySelectorAll('.specs__row, .product-specs tr');
      for (const row of bolSpecs) {
        const label = row.querySelector('.specs__title, td:first-child');
        const value = row.querySelector('.specs__value, td:last-child');
        if (label && value) {
          const labelText = (label.textContent || '').trim().toLowerCase();
          const valueText = (value.textContent || '').trim();
          if (labelText.includes('ean') && /^\d{13}$/.test(valueText)) {
            data.ean = valueText;
            console.log('[Dealink] Bol.com EAN:', data.ean);
          }
        }
      }
      break;
    
    case 'coolblue':
      const cbBrand = document.querySelector('.product-header__brand, [data-test="product-brand"]');
      if (cbBrand) data.brand = cbBrand.textContent?.trim();
      break;
    
    case 'cdiscount':
      const cdBrand = document.querySelector('.fpBrdName, [itemprop="brand"]');
      if (cdBrand) data.brand = cdBrand.textContent?.trim() || cdBrand.content;
      break;
    
    case 'conrad':
      const conradBrand = document.querySelector('[data-test="product-brand"], .product-brand');
      if (conradBrand) data.brand = conradBrand.textContent?.trim();
      break;
    
    // === Australia ===
    case 'jbhifi':
      const jbBrand = document.querySelector('.product-brand, [data-test="product-brand"]');
      if (jbBrand) data.brand = jbBrand.textContent?.trim();
      break;
    
    // === India ===
    case 'flipkart':
      const fkBrand = document.querySelector('.G6XhRU, ._2whKao');
      if (fkBrand) data.brand = fkBrand.textContent?.trim();
      
      // Flipkart product specs
      const fkSpecs = document.querySelectorAll('._14cfVK tr, .flxcaE tr');
      for (const row of fkSpecs) {
        const cells = row.querySelectorAll('td');
        if (cells.length >= 2) {
          const label = (cells[0].textContent || '').trim().toLowerCase();
          const value = (cells[1].textContent || '').trim();
          if (label.includes('ean') && /^\d{13}$/.test(value)) {
            data.ean = value;
          }
          if (!data.brand && label.includes('brand')) {
            data.brand = value;
          }
        }
      }
      break;
    
    // === Latin America ===
    case 'mercadolibre':
      const mlBrand = document.querySelector('.ui-pdp-brand, [data-testid="brand"]');
      if (mlBrand) data.brand = mlBrand.textContent?.trim();
      
      const mlSpecs = document.querySelectorAll('.andes-table__row, .ui-pdp-specs tr');
      for (const row of mlSpecs) {
        const cells = row.querySelectorAll('td, th');
        if (cells.length >= 2) {
          const label = (cells[0].textContent || '').trim().toLowerCase();
          const value = (cells[1].textContent || '').trim();
          if ((label.includes('ean') || label.includes('gtin')) && /^\d{13}$/.test(value)) {
            data.ean = value;
          }
          if (!data.brand && (label.includes('marca') || label.includes('brand'))) {
            data.brand = value;
          }
        }
      }
      break;
  }
  
  return data;
}

// =============================================================================
// BASIC INFO EXTRACTION (Title, Price, Image - fallbacks)
// =============================================================================

function extractBasicInfo() {
  const platform = detectPlatform();
  
  // Title extraction with platform-specific selectors
  const titleSelectors = {
    amazon: ['#productTitle', '#title', 'h1.a-size-large'],
    ebay: ['h1.x-item-title__mainTitle', '.x-item-title', 'h1[itemprop="name"]'],
    walmart: ['h1[itemprop="name"]', 'h1.prod-ProductTitle', '[data-testid="product-title"]'],
    aliexpress: ['.product-title-text', 'h1.product-title', '.hf-header-title'],
    bestbuy: ['.sku-title h1', '.heading-5', 'h1[data-track]'],
    target: ['h1[data-test="product-title"]', 'h1.Heading'],
    newegg: ['h1.product-title', '.product-title-container h1'],
    // Israel
    ksp: ['h1.product-title', '.product-name h1', 'h1'],
    ivory: ['h1.product-name', '.product-title', 'h1'],
    bug: ['h1.item-title', '.product-name', 'h1'],
    // UK
    currys: ['h1.product-title', '.product-name h1', 'h1[data-product="name"]'],
    argos: ['h1.product-title', '[data-test="product-title"]', 'h1'],
    // EU
    otto: ['h1.prd_title__name', '[data-qa="productName"]', 'h1'],
    mediamarkt: ['h1.product-title', '[data-test="product-title"]', 'h1'],
    bol: ['h1.pdp-header__title', '[data-test="product-title"]', 'h1'],
    coolblue: ['h1.product-title', '.js-product-name', 'h1'],
    cdiscount: ['h1.fpTitleBox', '.product-title h1', 'h1'],
    conrad: ['h1.product-title', '[data-test="product-title"]', 'h1'],
    // AU
    jbhifi: ['h1.product-title', '.product-name', 'h1'],
    // India
    flipkart: ['h1.yhB1nd span', '.B_NuCI', 'h1'],
    // LATAM
    mercadolibre: ['h1.ui-pdp-title', '.item-title__primary', 'h1'],
    default: ['h1', '[itemprop="name"]', '.product-title']
  };
  
  const selectors = titleSelectors[platform] || titleSelectors.default;
  let title = null;
  for (const sel of selectors) {
    const el = document.querySelector(sel);
    if (el?.textContent?.trim()) {
      title = el.textContent.trim();
      break;
    }
  }
  
  // Price extraction with platform-specific selectors
  const priceSelectors = {
    amazon: [
      '.a-price .a-offscreen',
      '#priceblock_ourprice',
      '#priceblock_dealprice',
      '.a-price-whole',
      '[data-a-color="price"] .a-offscreen'
    ],
    ebay: [
      '.x-price-primary span',
      '[itemprop="price"]',
      '#prcIsum',
      '.vi-VR-cvipPrice'
    ],
    walmart: [
      '[itemprop="price"]',
      '[data-testid="price-wrap"] span',
      '.prod-PriceHero .price-characteristic'
    ],
    aliexpress: [
      '.product-price-value',
      '.uniform-banner-box-price',
      '[itemprop="price"]'
    ],
    bestbuy: [
      '.priceView-customer-price span',
      '[data-testid="customer-price"] span'
    ],
    // Israel
    ksp: ['.price-val', '.product-price', '[itemprop="price"]'],
    ivory: ['.product-price', '.price', '[itemprop="price"]'],
    bug: ['.item-price', '.price', '[itemprop="price"]'],
    // UK
    currys: ['[data-product="price"]', '.product-price', '[itemprop="price"]'],
    argos: ['[data-test="product-price"]', '.product-price', '[itemprop="price"]'],
    // EU
    otto: ['.prd_price__total', '[data-qa="productPrice"]', '[itemprop="price"]'],
    mediamarkt: ['[data-test="product-price"]', '.product-price', '[itemprop="price"]'],
    bol: ['.priceblock__price', '[data-test="price"]', '[itemprop="price"]'],
    coolblue: ['.sales-price__current', '.product-price', '[itemprop="price"]'],
    cdiscount: ['.fpPrice', '.product-price', '[itemprop="price"]'],
    conrad: ['[data-test="product-price"]', '.product-price', '[itemprop="price"]'],
    // AU
    jbhifi: ['.product-price', '.price', '[itemprop="price"]'],
    // India (prices in ₹)
    flipkart: ['._30jeq3', '._16Jk6d', '[itemprop="price"]'],
    // LATAM
    mercadolibre: ['.andes-money-amount__fraction', '.price-tag-fraction', '[itemprop="price"]'],
    default: ['[itemprop="price"]', '.price', '.product-price']
  };
  
  let price = null;
  const pSelectors = priceSelectors[platform] || priceSelectors.default;
  for (const sel of pSelectors) {
    const el = document.querySelector(sel);
    if (el) {
      const priceText = el.content || el.textContent || '';
      const parsed = parseFloat(priceText.replace(/[^\d.]/g, ''));
      if (!isNaN(parsed) && parsed > 0) {
        price = parsed;
        break;
      }
    }
  }
  
  // Image extraction
  const imageSelectors = {
    amazon: ['#landingImage', '#imgBlkFront', '.a-dynamic-image'],
    ebay: ['img.ux-image-magnify__image--original', '[itemprop="image"]'],
    walmart: ['[data-testid="hero-image"] img', '.hover-zoom-hero-image img'],
    default: ['[itemprop="image"]', '.product-image img', 'img.main-image']
  };
  
  let image = null;
  const imgSelectors = imageSelectors[platform] || imageSelectors.default;
  for (const sel of imgSelectors) {
    const el = document.querySelector(sel);
    if (el?.src) {
      image = el.src;
      break;
    }
  }
  
  return { title, price, image };
}

// =============================================================================
// IDENTIFIERS EXTRACTION (ASIN, UPC, EAN, MPN)
// =============================================================================

function extractIdentifiers() {
  const platform = detectPlatform();
  const url = window.location.href;
  const html = document.body?.innerHTML || '';
  
  const identifiers = {
    asin: null,
    upc: null,
    ean: null,
    gtin: null,
    mpn: null,
    sku: null
  };
  
  // ASIN (Amazon only)
  if (platform === 'amazon') {
    const asinMatch = url.match(/\/dp\/([A-Z0-9]{10})/) || 
                     url.match(/\/product\/([A-Z0-9]{10})/);
    if (asinMatch) {
      identifiers.asin = asinMatch[1];
    } else {
      const asinEl = document.querySelector('[data-asin]');
      if (asinEl) identifiers.asin = asinEl.getAttribute('data-asin');
    }
    
    // Amazon-specific: extract UPC/EAN from product details table
    // Amazon hides GTIN in the product information section
    const detailTables = document.querySelectorAll(
      '#productDetails_detailBullets_sections1, #productDetails_techSpec_section_1, #detailBullets_feature_div, .detail-bullet-list, #prodDetails table'
    );
    
    for (const table of detailTables) {
      const rows = table.querySelectorAll('tr, .detail-bullet-list span.a-list-item');
      for (const row of rows) {
        const text = row.textContent || '';
        
        // Look for UPC (12 digits)
        const upcTableMatch = text.match(/UPC[\s:]+(\d{12})/i);
        if (upcTableMatch && !identifiers.upc) {
          identifiers.upc = upcTableMatch[1];
          console.log('[Dealink] Found UPC in Amazon table:', identifiers.upc);
        }
        
        // Look for EAN (13 digits)
        const eanTableMatch = text.match(/(?:EAN|GTIN)[\s:]+(\d{13})/i);
        if (eanTableMatch && !identifiers.ean) {
          identifiers.ean = eanTableMatch[1];
          console.log('[Dealink] Found EAN in Amazon table:', identifiers.ean);
        }
        
        // Look for ASIN in table (backup)
        if (!identifiers.asin) {
          const asinTableMatch = text.match(/ASIN[\s:]+([A-Z0-9]{10})/i);
          if (asinTableMatch) {
            identifiers.asin = asinTableMatch[1].toUpperCase();
          }
        }
        
        // Look for Manufacturer Part Number
        if (!identifiers.mpn) {
          const mpnTableMatch = text.match(/(?:Manufacturer|Part\s*Number|Item\s*model\s*number)[\s:]+([A-Z0-9][A-Z0-9\-\.]+)/i);
          if (mpnTableMatch) {
            identifiers.mpn = mpnTableMatch[1];
            console.log('[Dealink] Found MPN in Amazon table:', identifiers.mpn);
          }
        }
      }
    }
    
    // Also check Amazon's hidden input fields and data attributes
    const asinInput = document.querySelector('input[name="ASIN"]');
    if (asinInput?.value && !identifiers.asin) {
      identifiers.asin = asinInput.value;
    }
  }
  
  // === Generic UPC/EAN extraction from HTML ===
  // More flexible patterns that handle HTML tags between label and value
  if (!identifiers.upc) {
    // Pattern: "UPC" followed by 12 digits (possibly with HTML/whitespace between)
    const upcMatch = html.match(/\bUPC\b[^0-9]*?(\d{12})\b/i);
    if (upcMatch) identifiers.upc = upcMatch[1];
  }
  
  if (!identifiers.ean) {
    // Pattern: "EAN" or "GTIN" followed by 13 digits
    const eanMatch = html.match(/\b(?:EAN|GTIN)\b[^0-9]*?(\d{13})\b/i);
    if (eanMatch) identifiers.ean = eanMatch[1];
  }
  
  // MPN
  if (!identifiers.mpn) {
    const mpnMatch = html.match(/\bMPN\b[^A-Z0-9]*?([A-Z0-9][A-Z0-9\-]{2,})\b/i);
    if (mpnMatch) identifiers.mpn = mpnMatch[1];
  }
  
  // Also check meta tags
  const metaUpc = document.querySelector('meta[property="product:upc"], meta[name="upc"]');
  if (metaUpc?.content && !identifiers.upc) identifiers.upc = metaUpc.content;
  
  const metaGtin = document.querySelector('meta[property="product:gtin"], meta[name="gtin"]');
  if (metaGtin?.content && !identifiers.gtin) identifiers.gtin = metaGtin.content;
  
  const metaMpn = document.querySelector('meta[property="product:mpn"], meta[name="mpn"]');
  if (metaMpn?.content && !identifiers.mpn) identifiers.mpn = metaMpn.content;
  
  console.log('[Dealink] Extracted identifiers:', JSON.stringify(identifiers));
  return identifiers;
}

// =============================================================================
// MAIN EXTRACTION FUNCTION
// =============================================================================

function extractProductInfo() {
  const platform = detectPlatform();
  const url = window.location.href;
  
  // Get structured data (primary source)
  const structured = extractStructuredData();
  
  // Get basic info (fallbacks)
  const basic = extractBasicInfo();
  
  // Get identifiers
  const identifiers = extractIdentifiers();
  
  // Merge structured with identifiers
  if (structured.gtin) {
    if (structured.gtin.length === 12) identifiers.upc = structured.gtin;
    else if (structured.gtin.length === 13) identifiers.ean = structured.gtin;
    else identifiers.gtin = structured.gtin;
  }
  if (structured.mpn && !identifiers.mpn) identifiers.mpn = structured.mpn;
  if (structured.sku && !identifiers.sku) identifiers.sku = structured.sku;
  
  // Merge platform-specific identifiers (eBay/Walmart/BestBuy UPC/EAN/GTIN)
  const platformData = extractPlatformSpecific();
  if (platformData.upc && !identifiers.upc) identifiers.upc = platformData.upc;
  if (platformData.ean && !identifiers.ean) identifiers.ean = platformData.ean;
  if (platformData.gtin && !identifiers.gtin) identifiers.gtin = platformData.gtin;
  if (platformData.sku && !identifiers.sku) identifiers.sku = platformData.sku;
  
  // Build final product data
  const productData = {
    // Basic info (prefer structured, fallback to basic extraction)
    title: basic.title || 'Unknown Product',
    price: structured.price || basic.price || null,
    url: url,
    platform: platform,
    image: structured.image || basic.image || null,
    
    // Identifiers
    identifiers: identifiers,
    
    // Structured data (for advanced parsing on backend)
    structured: {
      brand: structured.brand,
      model: structured.model,
      color: structured.color,
      capacity: structured.capacity,
      category: structured.category,
      condition: structured.condition,
      currency: structured.currency,
      availability: structured.availability,
      rating: structured.rating,
      reviewCount: structured.reviewCount,
      source: structured.source, // Where data came from (json-ld, microdata, meta, platform)
    },
    
    // Metadata
    extractedAt: new Date().toISOString(),
    hasStructuredData: structured.source !== null,
    
    // User locale info (for multi-location search)
    user_locale: {
      language: navigator.language || 'en-US',
      languages: Array.from(navigator.languages || ['en-US']),
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      country: Intl.DateTimeFormat().resolvedOptions().locale?.split('-').pop() || null,
    },
  };
  
  // Clean up null/undefined values in structured
  productData.structured = Object.fromEntries(
    Object.entries(productData.structured).filter(([_, v]) => v != null)
  );
  
  return productData;
}

// =============================================================================
// SPA SUPPORT (MutationObserver)
// =============================================================================

let lastUrl = window.location.href;
let extractionTimeout = null;

function onPageChange() {
  // Debounce to avoid multiple extractions on rapid changes
  if (extractionTimeout) clearTimeout(extractionTimeout);
  
  extractionTimeout = setTimeout(() => {
    if (isProductPage()) {
      if (isDealinkRedirect()) {
        console.log('[Dealink] SPA nav from Dealink link - skipping');
        chrome.runtime.sendMessage({
          action: "DEALINK_SOURCE",
          data: { url: window.location.href }
        });
        return;
      }
      
      const info = extractProductInfo();
      console.log('[Dealink] Product detected:', info);
      
      chrome.runtime.sendMessage({
        action: "PRODUCT_DETECTED",
        data: info
      });
    }
  }, 500); // Wait 500ms for page to stabilize
}

// Watch for URL changes (SPA navigation)
const observer = new MutationObserver(() => {
  if (window.location.href !== lastUrl) {
    lastUrl = window.location.href;
    onPageChange();
  }
});

// Start observing
observer.observe(document.body, {
  childList: true,
  subtree: true
});

// =============================================================================
// MESSAGE LISTENER (for popup retry requests)
// =============================================================================

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'RESCAN_PAGE') {
    console.log('[Dealink] Rescan requested');
    if (isProductPage()) {
      const info = extractProductInfo();
      console.log('[Dealink] Rescan result:', info);
      
      chrome.runtime.sendMessage({
        action: "PRODUCT_DETECTED",
        data: info
      });
    }
    sendResponse({ success: true });
  }
  return true;
});

// =============================================================================
// DEALINK_SOURCE CHECK - Skip search if user came from Dealink
// =============================================================================

function isDealinkRedirect() {
  const url = new URL(window.location.href);
  return url.searchParams.has('dealink_source');
}

// =============================================================================
// INITIAL EXTRACTION
// =============================================================================

if (isProductPage()) {
  // Check if user arrived from a Dealink link
  if (isDealinkRedirect()) {
    console.log('[Dealink] User came from Dealink link - skipping search');
    chrome.runtime.sendMessage({
      action: "DEALINK_SOURCE",
      data: { url: window.location.href }
    });
  } else {
    // Wait a bit for dynamic content to load
    setTimeout(() => {
      const info = extractProductInfo();
      console.log('[Dealink] Product detected:', info);
      
      chrome.runtime.sendMessage({
        action: "PRODUCT_DETECTED",
        data: info
      });
    }, 300);
  }
}