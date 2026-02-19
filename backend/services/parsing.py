# backend/services/parsing.py
"""
Advanced Title Parsing Module for Dealink
מודול משופר לפירוק כותרות מוצרים - מזהה brand, model, ו-attributes מפורטים

Brand data is loaded from backend/data/brands.json for easy maintenance.
Regex-based product line patterns remain in Python.
"""
import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ParsedTitle:
    """מבנה נתונים מורחב לתוצאות הפירוק"""
    brand: str = "Unknown"
    model: str = "Unknown"
    product_line: Optional[str] = None  # קו מוצרים (iPhone, Galaxy, ThinkPad)
    
    # Attributes מפורטים
    attributes: list[str] = field(default_factory=list)
    color: Optional[str] = None
    size: Optional[str] = None
    capacity: Optional[str] = None  # 256GB, 1TB
    year: Optional[int] = None
    generation: Optional[str] = None  # Gen 4, 4th Gen, etc.
    
    # מידע נוסף
    condition: Optional[str] = None  # New, Refurbished, Used
    variant: Optional[str] = None  # Pro, Max, Plus, Mini, Lite
    connectivity: list[str] = field(default_factory=list)  # WiFi, Bluetooth, 5G
    
    # ציון אמינות
    confidence: float = 0.0  # 0.0-1.0
    raw_title: str = ""


# =============================================================================
# LOAD BRAND DATA FROM JSON
# =============================================================================

_DATA_DIR = Path(__file__).parent.parent / "data"
_BRANDS_JSON_PATH = _DATA_DIR / "brands.json"

def _load_brands_data() -> dict:
    """Load brand data from external JSON file for easy maintenance."""
    try:
        with open(_BRANDS_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[WARNING] brands.json not found at {_BRANDS_JSON_PATH}, using empty defaults")
        return {}
    except json.JSONDecodeError as e:
        print(f"[WARNING] brands.json parse error: {e}, using empty defaults")
        return {}

_brand_data = _load_brands_data()

BRANDS_BY_CATEGORY = _brand_data.get("brands_by_category", {})
BRAND_ALIASES = _brand_data.get("brand_aliases", {})

# Flatten all brands into a single set for quick lookup
ALL_BRANDS = set()
BRAND_TO_CATEGORY = {}
for category, subcats in BRANDS_BY_CATEGORY.items():
    for subcat, brands in subcats.items():
        for brand in brands:
            ALL_BRANDS.add(brand.lower())
            BRAND_TO_CATEGORY[brand.lower()] = (category, subcat)


# =============================================================================
# PRODUCT LINE PATTERNS - קווי מוצרים ספציפיים
# =============================================================================

PRODUCT_LINES = {
    "Apple": {
        "patterns": [
            r"\b(iPhone\s*\d{1,2}(?:\s*(?:Pro|Plus|Max|Mini|SE))*)\b",
            r"\b(iPad\s*(?:Pro|Air|Mini)?(?:\s*\d{1,2})?)\b",
            r"\b(MacBook\s*(?:Pro|Air)?(?:\s*\d{2})?)\b",
            r"\b(Apple\s*Watch\s*(?:Series\s*\d+|Ultra|SE)?)\b",
            r"\b(AirPods\s*(?:Pro|Max)?(?:\s*\d)?)\b",
            r"\b(iMac(?:\s*\d{2})?)\b",
            r"\b(Mac\s*(?:Mini|Studio|Pro))\b",
        ],
        "model_pattern": r"(?:M[1-4](?:\s*(?:Pro|Max|Ultra))?)",
    },
    "Samsung": {
        "patterns": [
            r"\b(Galaxy\s*[SAZM]\d{1,2}(?:\s*(?:FE|Ultra|Plus|\+))*)\b",
            r"\b(Galaxy\s*(?:Tab\s*)?[SAZM]\d{1,2}(?:\s*(?:FE|Ultra|Plus|\+))*)\b",
            r"\b(Galaxy\s*(?:Fold|Flip|Z\s*(?:Fold|Flip))\s*\d?)\b",
            r"\b(Galaxy\s*Buds\s*(?:Pro|Plus|Live|FE|\d)?)\b",
            r"\b(Galaxy\s*Watch\s*(?:\d|Ultra)?)\b",
        ],
        "model_pattern": r"(?:SM-[A-Z]\d{3,4}[A-Z]?)",
    },
    "Sony": {
        "patterns": [
            r"\b(WH-\d{4}[A-Z]*\d*)\b",  # WH-1000XM5
            r"\b(WF-\d{4}[A-Z]*\d*)\b",  # WF-1000XM4
            r"\b(PlayStation\s*\d)\b",
            r"\b(PS[45])\b",
            r"\b(Xperia\s*[A-Z0-9]+)\b",
            r"\b(Alpha\s*[A-Z]?\d+)\b",  # Alpha cameras
            r"\b(A[679]\d{3})\b",  # A7III, A6400
        ],
    },
    "Dyson": {
        "patterns": [
            r"\b(V\d{1,2}(?:\s*(?:Absolute|Animal|Motorhead|Fluffy|Outsize|Detect))?)\b",
            r"\b(Airwrap(?:\s*(?:Complete|Multi-Styler))?)\b",
            r"\b(Supersonic)\b",
            r"\b(Pure\s*(?:Cool|Hot\+Cool|Humidify\+Cool)?)\b",
            r"\b((?:360|TP|HP|AM)\d{2})\b",
        ],
    },
    "Lenovo": {
        "patterns": [
            r"\b(ThinkPad\s*[TXLEPW]\d{2,3}[a-z]?(?:\s*(?:Gen\s*\d+|Yoga))?)\b",
            r"\b(IdeaPad\s*(?:Slim\s*)?\d{1,3}[a-z]?)\b",
            r"\b(Legion\s*(?:Pro\s*)?\d{1}(?:i)?)\b",
            r"\b(Yoga\s*(?:Slim\s*)?\d{1,3}[a-z]?)\b",
        ],
    },
    "Dell": {
        "patterns": [
            r"\b(XPS\s*\d{2}(?:\s*(?:Plus|\d{4}))?)\b",
            r"\b(Latitude\s*\d{4})\b",
            r"\b(Inspiron\s*\d{2,4})\b",
            r"\b(Alienware\s*(?:m\d{2}|x\d{2}|Aurora)?)\b",
            r"\b(Precision\s*\d{4})\b",
        ],
    },
    "LEVOIT": {
        "patterns": [
            r"\b(Core\s*\d{3}[SP]?(?:\s*(?:True\s*HEPA|Smart))?)\b",
            r"\b(LV-H\d{3}[A-Z]*)\b",
            r"\b(Vital\s*\d{3}[SP]?)\b",
        ],
    },
    "Bose": {
        "patterns": [
            r"\b(QuietComfort\s*(?:Ultra\s*)?(?:Earbuds|Headphones|\d{2,3}))\b",
            r"\b(QC\s*\d{2,3})\b",
            r"\b(SoundLink\s*(?:Flex|Revolve|Mini|Micro|Color)?(?:\s*(?:II|2))?)\b",
            r"\b(Noise\s*Cancelling\s*Headphones\s*\d{3})\b",
        ],
    },
    "JBL": {
        "patterns": [
            r"\b(Flip\s*\d)\b",
            r"\b(Charge\s*\d)\b",
            r"\b(Pulse\s*\d)\b",
            r"\b(Xtreme\s*\d)\b",
            r"\b(PartyBox\s*\d{2,3})\b",
            r"\b(Live\s*\d{3}(?:\s*(?:NC|BT))?)\b",
            r"\b(Tune\s*\d{3}(?:\s*(?:NC|BT|TWS))?)\b",
            r"\b(Tour\s*(?:One|Pro)\s*\d?)\b",
        ],
    },
    "Logitech": {
        "patterns": [
            r"\b(MX\s*(?:Master|Anywhere|Keys|Mechanical|Ergo)\s*\d?[Ss]?)\b",
            # G PRO X SUPERLIGHT, G PRO X, G PRO Wireless, G502 X Plus Lightspeed, etc.
            r"\b(G\s*PRO\s*(?:X\s*)?(?:SUPERLIGHT|Superlight|Lightspeed|Wireless|Hero)?(?:\s*\d)?)\b",
            r"\b(G\s*(?:502|903|903|305|304|309|705|733|435|535|733|935|604|203)(?:\s*(?:X|SE|HERO|Lightspeed|Hero|Plus|PLUS))*)\b",
            r"\b(G\d{3}(?:\s*(?:X|SE|HERO|Lightspeed|Hero|Plus|PLUS))*)\b",  # Generic G+3digits
            r"\b(C\d{3,4}(?:x|e|s)?)\b",  # Webcams: C920, C922, C930e
            r"\b(StreamCam)\b",
            r"\b(Zone\s*(?:Vibe|Wired|Wireless)?(?:\s*\d{3})?)\b",
            r"\b(ERGO\s*(?:K\d{3}|M\d{3}))\b",  # ERGO K860, ERGO M575
            r"\b(M\d{3}[a-z]?)\b",  # M720, M750
            r"\b(K\d{3}[a-z]?)\b",  # K780, K380
            r"\b(POP\s*(?:Keys|Mouse))\b",
            r"\b(Pebble\s*(?:Mouse\s*)?2?)\b",
        ],
    },
    "Nintendo": {
        "patterns": [
            r"\b(Switch\s*(?:OLED|Lite)?(?:\s*Model)?)\b",
            r"\b(Joy-Con)\b",
            r"\b(3DS\s*(?:XL)?)\b",
            r"\b(Wii\s*U?)\b",
        ],
    },
    "Google": {
        "patterns": [
            r"\b(Pixel\s*\d[a]?\s*(?:Pro|XL)?)\b",
            r"\b(Pixel\s*Buds\s*(?:Pro|A-Series)?)\b",
            r"\b(Pixel\s*Watch\s*\d?)\b",
            r"\b(Nest\s*(?:Hub|Audio|Mini|Wifi|Doorbell|Cam)?(?:\s*(?:Max|2nd\s*Gen))?)\b",
            r"\b(Chromecast(?:\s*with\s*Google\s*TV)?)\b",
        ],
    },
    "Microsoft": {
        "patterns": [
            r"\b(Surface\s*(?:Pro|Laptop|Go|Book|Studio)\s*\d?)\b",
            r"\b(Xbox\s*(?:Series\s*[XS]|One\s*[XS]?))\b",
        ],
    },
    "Amazon": {
        "patterns": [
            r"\b(Kindle\s*(?:Paperwhite|Oasis|Scribe)?(?:\s*\d+)?)\b",
            r"\b(Echo\s*(?:Dot|Show|Studio|Pop)?(?:\s*\d+)?)\b",
            r"\b(Fire\s*(?:TV|HD|Max)?(?:\s*\d+)?)\b",
            r"\b(Ring\s*(?:Doorbell|Stick Up Cam|Floodlight)?(?:\s*\d+)?)\b",
        ],
    },
    "Sennheiser": {
        "patterns": [
            r"\b(MOMENTUM\s*\d?\s*(?:True\s*)?(?:Wireless)?)\b",
            r"\b(HD\s*\d{3,4}(?:\s*[A-Z]+)?)\b",  # HD 600, HD 650, HD 800S
            r"\b(IE\s*\d{2,3}(?:\s*Pro)?)\b",  # IE 600, IE 300
            r"\b(CX\s*(?:True\s*Wireless|Plus|Sport)?)\b",
            r"\b(PXC\s*\d{3})\b",  # PXC 550
            r"\b(Ambeo\s*(?:Soundbar)?)\b",
        ],
    },
    "Beyerdynamic": {
        "patterns": [
            r"\b(DT\s*\d{3,4}(?:\s*Pro)?(?:\s*X)?)\b",  # DT 770, DT 990 Pro X
            r"\b(Amiron)\b",
            r"\b(T\d\s*(?:Gen\s*\d)?)\b",  # T1, T5
            r"\b(MMX\s*\d{3})\b",  # MMX 300
        ],
    },
    "AKG": {
        "patterns": [
            r"\b(K\d{3,4}(?:\s*[A-Z]+)?)\b",  # K702, K712 Pro
            r"\b(N\d{2,3}(?:\s*NC)?)\b",  # N700NC
        ],
    },
    "Shure": {
        "patterns": [
            r"\b(SE\d{3,4})\b",  # SE215, SE535
            r"\b(SRH\d{3,4})\b",  # SRH840
            r"\b(SM\d{1,2}[A-Z]?)\b",  # SM7B, SM58
            r"\b(Aonic\s*\d{2,3})\b",  # Aonic 50
        ],
    },
    # === KEYBOARD BRANDS ===
    "RK ROYAL KLUDGE": {
        "patterns": [
            r"\b(RK\s*\d{2,3})\b",  # RK84, RK61, RK68, RK71, RK100
            r"\b(RK\s*G\d{2})\b",  # RK G68
        ],
    },
    "Keychron": {
        "patterns": [
            r"\b(K\d{1,2}(?:\s*(?:Pro|Max|SE|HE))?)\b",  # K2, K8 Pro, K1 Max
            r"\b(Q\d{1,2}(?:\s*(?:Pro|Max|HE))?)\b",  # Q1, Q2 Pro
            r"\b(V\d{1,2}(?:\s*(?:Max))?)\b",  # V1, V6 Max
            r"\b(C\d{1,2}(?:\s*(?:Pro))?)\b",  # C1, C2 Pro
            r"\b(S\d{1,2})\b",  # S1
        ],
    },
    "Corsair": {
        "patterns": [
            r"\b(K\d{2,3}(?:\s*(?:RGB|PRO|MAX))*)\b",  # K70, K100
            r"\b(Void\s*(?:RGB\s*)?(?:Elite|Pro)?)\b",
            r"\b(HS\d{2,3}(?:\s*(?:Pro|X|Wireless))*)\b",  # HS80, HS70 Pro
            r"\b(Scimitar\s*(?:RGB\s*)?(?:Elite)?)\b",
            r"\b(Vengeance\s*(?:RGB\s*)?(?:Pro|RT)?)\b",
            r"\b(Dark\s*Core\s*(?:RGB\s*)?(?:Pro|SE)?)\b",
        ],
    },
    "Razer": {
        "patterns": [
            r"\b(BlackWidow\s*(?:V\d|Lite|Mini|Elite|TE)?)\b",
            r"\b(Huntsman\s*(?:V\d|Mini|Elite|TE)?)\b",
            r"\b(DeathAdder\s*(?:V\d|Essential|Elite)?)\b",
            r"\b(Viper\s*(?:V\d|Mini|Ultimate|Lite)?)\b",
            r"\b(Basilisk\s*(?:V\d|X|Ultimate|Lite)?)\b",
            r"\b(Kraken\s*(?:V\d|X|Kitty|Ultimate|TE|Pro)?)\b",
            r"\b(Naga\s*(?:V\d|X|Pro|Trinity)?)\b",
            r"\b(Ornata\s*(?:V\d|Chroma)?)\b",
            r"\b(Barracuda\s*(?:X|Pro)?)\b",
        ],
    },
    "SteelSeries": {
        "patterns": [
            r"\b(Arctis\s*(?:Nova\s*)?(?:Pro|7|9|1|Prime)?(?:\s*Wireless)?)\b",
            r"\b(Apex\s*(?:Pro|7|5|3)?(?:\s*(?:TKL|Mini))?)\b",
            r"\b(Rival\s*\d{3}(?:\s*(?:Wireless))?)\b",
            r"\b(Aerox\s*\d(?:\s*(?:Wireless))?)\b",
            r"\b(Sensei\s*(?:Ten)?)\b",
            r"\b(Prime\s*(?:Mini|Wireless)?)\b",
        ],
    },
    "HyperX": {
        "patterns": [
            r"\b(Alloy\s*(?:Origins|Elite|FPS|Core)?(?:\s*\d{2})?)\b",
            r"\b(Cloud\s*(?:Alpha|II|III|Core|Stinger|Mix|Flight|Orbit)?(?:\s*(?:Wireless|S))?)\b",
            r"\b(Pulsefire\s*(?:Haste|Surge|Core|Dart|Raid)?(?:\s*\d)?)\b",
        ],
    },
    # === OTHER BRANDS ===
    "Garmin": {
        "patterns": [
            r"\b(Forerunner\s*\d{3,4})\b",  # Forerunner 955, 265
            r"\b(Fenix\s*\d(?:\s*(?:X|S|Pro|Plus|Solar))*)\b",  # Fenix 7X Pro
            r"\b(Venu\s*\d?(?:\s*(?:Sq|Plus))?)\b",  # Venu 3, Venu Sq 2
            r"\b(Instinct\s*\d?(?:\s*(?:Solar|Tactical))?)\b",
            r"\b(Edge\s*\d{3,4}(?:\s*(?:Plus|Explore))?)\b",
        ],
    },
    "GoPro": {
        "patterns": [
            r"\b(HERO\s*\d{1,2}(?:\s*(?:Black|Silver|White|Session|Max))?)\b",
        ],
    },
    "DJI": {
        "patterns": [
            r"\b(Mavic\s*(?:\d|Air|Mini|Pro|Classic)?(?:\s*(?:Pro|S|SE))?)\b",
            r"\b(Mini\s*\d(?:\s*(?:Pro|SE))?)\b",
            r"\b(Osmo\s*(?:Action|Pocket|Mobile)?(?:\s*\d)?)\b",
            r"\b(Air\s*\d[ST]?)\b",
        ],
    },
}


# =============================================================================
# ATTRIBUTE PATTERNS - תבניות לזיהוי מאפיינים
# =============================================================================

# צבעים - loaded from JSON
COLORS = set(_brand_data.get("colors", []))

# גודל/מידה
SIZE_PATTERNS = [
    r'\b(\d+(?:\.\d+)?)\s*(?:inch|inches|"|\'\'|in)\b',  # 15.6 inch
    r'\b(\d+(?:\.\d+)?)\s*(?:mm|cm|m)\b',  # 45mm
    r'\b((?:XX?)?(?:S|M|L|XL|XXL|XXXL))\b',  # S, M, L, XL
    r'\b(small|medium|large|extra large)\b',
    r'\b(\d+(?:\.\d+)?)\s*(?:oz|ml|L|liter|litre|gallon|gal)\b',  # volume
]

# קיבולת אחסון
CAPACITY_PATTERNS = [
    r'\b(\d+)\s*(?:GB|gb|Gb)\b',
    r'\b(\d+)\s*(?:TB|tb|Tb)\b',
    r'\b(\d+)\s*(?:MB|mb|Mb)\b',
    r'\b(\d+)\s*(?:PB|pb)\b',
]

# זיכרון RAM
RAM_PATTERNS = [
    r'\b(\d+)\s*(?:GB|gb)\s*(?:RAM|ram|memory|DDR\d?)\b',
    r'\bRAM[:\s]*(\d+)\s*GB\b',
]

# תצוגה
DISPLAY_PATTERNS = [
    r'\b(\d+)\s*(?:Hz|hz|HZ)\b',  # Refresh rate
    r'\b(4K|8K|FHD|QHD|UHD|HD|1080p|1440p|2160p|720p)\b',
    r'\b(OLED|LCD|LED|Mini-LED|QLED|AMOLED|IPS|TN|VA)\b',
    r'\b(Retina|Liquid\s*Retina|ProMotion)\b',
]

# קישוריות
CONNECTIVITY_PATTERNS = [
    r'\b(WiFi|Wi-Fi|wifi)\s*\d*[a-z]?\b',
    r'\b(Bluetooth|BT)\s*\d*\.?\d*\b',
    r'\b(5G|4G|LTE|3G)\b',
    r'\b(NFC)\b',
    r'\b(USB[-\s]?C|USB[-\s]?A|USB\s*\d\.?\d?|Thunderbolt\s*\d?)\b',
    r'\b(HDMI\s*\d?\.?\d?|DisplayPort|DP)\b',
    r'\b(Ethernet|RJ45|LAN)\b',
    r'\b(Wireless|Cordless|Wired)\b',
]

# מצב המוצר - loaded from JSON
CONDITION_KEYWORDS = _brand_data.get("condition_keywords", {})

# וריאנטים - loaded from JSON
VARIANT_KEYWORDS = _brand_data.get("variant_keywords", {})

# שנים ודורות
YEAR_PATTERN = r'\b(20[1-3]\d)\b'
GENERATION_PATTERNS = [
    r'\b(?:Gen(?:eration)?|gen)[\s.-]*(\d+)\b',
    r'\b(\d+)(?:st|nd|rd|th)\s*Gen(?:eration)?\b',
    r'\b(?:Mark|Mk)[\s.-]*(\d+|[IVX]+)\b',
    r'\b([IVX]+)\b',  # Roman numerals (I, II, III, IV, V)
]

# תוכן אריזה (לסינון) - loaded from JSON
BUNDLE_KEYWORDS = _brand_data.get("bundle_keywords", [])


# =============================================================================
# PARSING FUNCTIONS
# =============================================================================

def normalize_text(text: str) -> str:
    """נרמול טקסט - הסרת תווים מיוחדים והמרה ל-lowercase לחיפוש"""
    # שמור את המקור
    normalized = text.lower()
    # הסר תווים מיוחדים מיותרים
    normalized = re.sub(r'[™®©]', '', normalized)
    # נרמל רווחים
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized


def _resolve_brand_name(brand_lower: str) -> str:
    """
    Find the properly-cased brand name from the ALL_BRANDS set.
    """
    for cat in BRANDS_BY_CATEGORY.values():
        for brands in cat.values():
            for b in brands:
                if b.lower() == brand_lower:
                    return b
    return brand_lower.title()


def extract_brand(title: str) -> tuple[str, float]:
    """
    חילוץ מותג מהכותרת - position-aware
    מוצא את כל המותגים הפוטנציאליים ובוחר את זה שמופיע הכי מוקדם בכותרת.
    Returns: (brand_name, confidence)
    """
    title_lower = normalize_text(title)
    title_words = title.split()
    
    # Collect all candidate brands with their position in title
    # Each candidate: (position, brand_name, confidence, source)
    candidates = []
    
    # 1. חפש brand מדויק ברשימה (ALL_BRANDS)
    for brand in ALL_BRANDS:
        match = re.search(rf'\b{re.escape(brand)}\b', title_lower)
        if match:
            proper_name = _resolve_brand_name(brand)
            candidates.append((match.start(), proper_name, 0.9, "direct"))
    
    # 2. בדוק aliases (airpods, iphone וכו')
    for alias, brand in BRAND_ALIASES.items():
        match = re.search(rf'\b{re.escape(alias)}\b', title_lower)
        if match:
            candidates.append((match.start(), brand, 0.95, "alias"))
    
    # 3. בדוק שתי מילים ראשונות (למותגים כמו "The North Face", "RK ROYAL KLUDGE")
    if len(title_words) >= 2:
        two_words = f"{title_words[0]} {title_words[1]}".lower()
        if two_words in ALL_BRANDS:
            proper_name = _resolve_brand_name(two_words)
            candidates.append((0, proper_name, 0.85, "two_word"))
        elif two_words in BRAND_ALIASES:
            candidates.append((0, BRAND_ALIASES[two_words], 0.85, "two_word_alias"))
        
        # בדוק שלוש מילים ראשונות
        if len(title_words) >= 3:
            three_words = f"{title_words[0]} {title_words[1]} {title_words[2]}".lower()
            if three_words in ALL_BRANDS:
                proper_name = _resolve_brand_name(three_words)
                candidates.append((0, proper_name, 0.9, "three_word"))
            elif three_words in BRAND_ALIASES:
                candidates.append((0, BRAND_ALIASES[three_words], 0.9, "three_word_alias"))
    
    if not candidates:
        # 4. Fallback: בדוק מילה ראשונה כ-brand
        if title_words:
            first_word = title_words[0].strip('()[]"\'').lower()
            if first_word in ALL_BRANDS:
                proper_name = _resolve_brand_name(first_word)
                return (proper_name, 0.8)
        return ("Unknown", 0.0)
    
    # בחר את המועמד שמופיע הכי מוקדם בכותרת
    # אם שני מועמדים באותה עמדה, העדף direct match על alias
    SOURCE_PRIORITY = {"three_word": 0, "two_word": 1, "direct": 2, "three_word_alias": 3, "two_word_alias": 4, "alias": 5}
    candidates.sort(key=lambda c: (c[0], SOURCE_PRIORITY.get(c[3], 99)))
    
    best = candidates[0]
    return (best[1], best[2])


def extract_product_line(title: str, brand: str) -> tuple[str, str, float]:
    """
    חילוץ קו מוצרים ומודל
    Returns: (product_line, model, confidence)
    """
    if brand in PRODUCT_LINES:
        brand_config = PRODUCT_LINES[brand]
        
        # חפש קו מוצרים
        for pattern in brand_config.get("patterns", []):
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                product_line = match.group(1).strip()
                
                # חפש גם מודל ספציפי אם יש pattern
                model = product_line
                if "model_pattern" in brand_config:
                    model_match = re.search(brand_config["model_pattern"], title, re.IGNORECASE)
                    if model_match:
                        model = f"{product_line} {model_match.group(0)}"
                
                return (product_line, model, 0.85)
    
    # Fallback: חפש patterns גנריים
    generic_patterns = [
        r'\b([A-Z]{2,4}[-]?\d{3,6}[A-Z]{0,2})\b',  # ABC-1234X
        r'\b([A-Z]{2,4}\d{4,6})\b',  # XPS1530
        r'\b(Model\s*[#:]?\s*[A-Z0-9-]+)\b',
    ]
    
    for pattern in generic_patterns:
        match = re.search(pattern, title)
        if match:
            return (None, match.group(1), 0.5)
    
    # אם יש brand, נסה לקחת מילים אחריו
    if brand and brand != "Unknown":
        brand_pos = title.lower().find(brand.lower())
        if brand_pos >= 0:
            after_brand = title[brand_pos + len(brand):].strip()
            words = after_brand.split()[:3]
            # סנן מילים שהן attributes ולא model
            model_words = []
            for word in words:
                word_lower = word.lower().strip('()[],"\'')
                if word_lower not in COLORS and len(word) > 1:
                    model_words.append(word)
                else:
                    break
            if model_words:
                return (None, " ".join(model_words), 0.4)
    
    return (None, "Unknown", 0.0)


def extract_color(title: str) -> Optional[str]:
    """חילוץ צבע"""
    title_lower = normalize_text(title)
    
    # חפש צבעים מהרשימה (מהארוך לקצר כדי לתפוס "space gray" לפני "gray")
    sorted_colors = sorted(COLORS, key=len, reverse=True)
    for color in sorted_colors:
        if re.search(rf'\b{re.escape(color)}\b', title_lower):
            return color.title()
    
    # חפש pattern של צבע + מילה (למשל "Midnight Green")
    color_pattern = r'\b((?:deep|light|dark|bright|matte|glossy)\s+\w+)\b'
    match = re.search(color_pattern, title_lower)
    if match:
        potential_color = match.group(1)
        # וודא שזה באמת צבע
        color_words = ["blue", "green", "red", "black", "white", "gray", "grey", "purple", "pink"]
        if any(cw in potential_color for cw in color_words):
            return potential_color.title()
    
    return None


def extract_capacity(title: str) -> Optional[str]:
    """חילוץ קיבולת אחסון (לא RAM)"""
    title_lower = title.lower()
    
    # קודם נסה למצוא storage מפורש (SSD, storage, flash, memory card)
    storage_patterns = [
        r'\b(\d+)\s*(?:TB)\b(?!\s*RAM)',  # TB כמעט תמיד storage
        r'\b(\d+)\s*(?:GB|gb)\s*(?:SSD|HDD|storage|flash|eMMC|NVMe)\b',
        r'\bSSD[:\s]*(\d+)\s*(?:GB|TB)\b',
        r'\bstorage[:\s]*(\d+)\s*(?:GB|TB)\b',
    ]
    
    for pattern in storage_patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            value = match.group(1)
            # מצא את היחידה
            unit_match = re.search(r'(GB|TB)', match.group(0), re.IGNORECASE)
            if unit_match:
                return f"{value}{unit_match.group(1).upper()}"
    
    # אם אין storage מפורש, חפש capacity שאינה RAM
    for pattern in CAPACITY_PATTERNS:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            # בדוק שזה לא RAM
            full_match = match.group(0)
            # חפש context סביב ה-match
            match_pos = title.lower().find(full_match.lower())
            context_start = max(0, match_pos - 10)
            context_end = min(len(title), match_pos + len(full_match) + 10)
            context = title[context_start:context_end].lower()
            
            # דלג אם זה RAM
            if 'ram' in context or 'memory' in context or 'ddr' in context:
                continue
                
            value = match.group(1)
            unit_match = re.search(r'(GB|TB|MB|PB)', match.group(0), re.IGNORECASE)
            if unit_match:
                return f"{value}{unit_match.group(1).upper()}"
    
    return None


def extract_size(title: str) -> Optional[str]:
    """חילוץ גודל/מידה"""
    for pattern in SIZE_PATTERNS:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None


def extract_year(title: str) -> Optional[int]:
    """חילוץ שנה"""
    match = re.search(YEAR_PATTERN, title)
    if match:
        year = int(match.group(1))
        # וודא שזו שנה סבירה (לא מספר אקראי)
        if 2015 <= year <= 2030:
            return year
    return None


def extract_generation(title: str) -> Optional[str]:
    """חילוץ דור/גרסה"""
    for pattern in GENERATION_PATTERNS:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return match.group(1) if match.lastindex else match.group(0)
    return None


def extract_condition(title: str) -> Optional[str]:
    """חילוץ מצב המוצר"""
    title_lower = normalize_text(title)
    for condition, keywords in CONDITION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in title_lower:
                return condition.title()
    return None


def extract_variant(title: str) -> Optional[str]:
    """חילוץ וריאנט (Pro, Max, Plus וכו')"""
    title_lower = normalize_text(title)
    
    # מילים שלא להתייחס אליהן כ-variant (חלק משם מוצר)
    exclude_contexts = [
        "air purifier", "air filter", "air cleaner", "air conditioner",
        "macbook air", "ipad air", "galaxy tab air",
    ]
    
    for variant, keywords in VARIANT_KEYWORDS.items():
        for keyword in keywords:
            if re.search(rf'\b{re.escape(keyword)}\b', title_lower):
                # בדוק אם זה בהקשר שצריך לדלג עליו
                skip = False
                for context in exclude_contexts:
                    if context in title_lower and keyword.lower() in context:
                        skip = True
                        break
                
                if not skip:
                    return variant.upper() if len(variant) <= 2 else variant.title()
    return None


def extract_connectivity(title: str) -> list[str]:
    """חילוץ אפשרויות קישוריות"""
    connectivity = []
    title_upper = title.upper()
    
    for pattern in CONNECTIVITY_PATTERNS:
        matches = re.findall(pattern, title, re.IGNORECASE)
        for match in matches:
            # נרמל את הערך
            value = match.strip().upper() if len(match) <= 4 else match.strip().title()
            if value not in connectivity:
                connectivity.append(value)
    
    return connectivity


def extract_display_specs(title: str) -> list[str]:
    """חילוץ מפרטי תצוגה"""
    specs = []
    for pattern in DISPLAY_PATTERNS:
        matches = re.findall(pattern, title, re.IGNORECASE)
        for match in matches:
            value = match.strip().upper()
            if value not in specs:
                specs.append(value)
    return specs


def extract_attributes(title: str) -> list[str]:
    """חילוץ כל ה-attributes"""
    attrs = []
    
    # קישוריות
    attrs.extend(extract_connectivity(title))
    
    # תצוגה
    attrs.extend(extract_display_specs(title))
    
    # Keywords נוספים
    additional_keywords = [
        "HEPA", "True HEPA", "waterproof", "water resistant", "dustproof",
        "noise cancelling", "noise canceling", "ANC", "active noise",
        "fast charging", "quick charge", "wireless charging",
        "touchscreen", "touch screen", "fingerprint", "face id", "face unlock",
        "stereo", "surround", "dolby", "atmos",
        "portable", "compact", "foldable", "folding",
        "rechargeable", "battery powered", "solar",
        "smart", "alexa", "google assistant", "siri",
        "rgb", "backlit", "mechanical",
    ]
    
    title_lower = normalize_text(title)
    for keyword in additional_keywords:
        if keyword.lower() in title_lower:
            attrs.append(keyword.title())
    
    return list(set(attrs))  # הסר כפילויות


def calculate_confidence(parsed: ParsedTitle) -> float:
    """חישוב ציון אמינות כולל"""
    score = 0.0
    factors = 0
    
    # Brand
    if parsed.brand != "Unknown":
        score += 0.3
    factors += 0.3
    
    # Model/Product Line
    if parsed.model != "Unknown":
        score += 0.25
    elif parsed.product_line:
        score += 0.15
    factors += 0.25
    
    # Attributes
    attr_count = len(parsed.attributes) + (1 if parsed.color else 0) + (1 if parsed.capacity else 0)
    if attr_count >= 3:
        score += 0.2
    elif attr_count >= 1:
        score += 0.1
    factors += 0.2
    
    # Year/Generation
    if parsed.year or parsed.generation:
        score += 0.1
    factors += 0.1
    
    # Variant
    if parsed.variant:
        score += 0.15
    factors += 0.15
    
    return round(score / factors, 2) if factors > 0 else 0.0


def parse_title(title: str) -> ParsedTitle:
    """
    הפונקציה הראשית - פירוק כותרת מוצר לכל המרכיבים
    
    Args:
        title: כותרת המוצר המקורית
        
    Returns:
        ParsedTitle object עם כל המידע שחולץ
    """
    result = ParsedTitle(raw_title=title)
    
    if not title or not title.strip():
        return result
    
    # 1. חילוץ Brand
    brand, brand_conf = extract_brand(title)
    result.brand = brand
    
    # 2. חילוץ Product Line ו-Model
    product_line, model, model_conf = extract_product_line(title, brand)
    result.product_line = product_line
    result.model = model
    
    # 3. חילוץ צבע
    result.color = extract_color(title)
    
    # 4. חילוץ קיבולת
    result.capacity = extract_capacity(title)
    
    # 5. חילוץ גודל
    result.size = extract_size(title)
    
    # 6. חילוץ שנה
    result.year = extract_year(title)
    
    # 7. חילוץ דור
    result.generation = extract_generation(title)
    
    # 8. חילוץ מצב
    result.condition = extract_condition(title)
    
    # 9. חילוץ וריאנט
    result.variant = extract_variant(title)
    
    # 10. חילוץ קישוריות
    result.connectivity = extract_connectivity(title)
    
    # 11. חילוץ attributes כלליים
    result.attributes = extract_attributes(title)
    
    # 12. חישוב confidence
    result.confidence = calculate_confidence(result)
    
    return result


def get_search_query(parsed: ParsedTitle) -> str:
    """
    יצירת שאילתת חיפוש אופטימלית מה-parsed title
    """
    parts = []
    used_words = set()  # למניעת כפילויות
    
    def add_part(text: str):
        """הוסף חלק רק אם המילים לא נוספו כבר"""
        if not text:
            return
        words = text.lower().split()
        # בדוק אם רוב המילים כבר נוספו
        new_words = [w for w in words if w not in used_words]
        if len(new_words) > len(words) / 2 or not used_words:  # יותר מחצי חדש
            parts.append(text)
            used_words.update(words)
    
    if parsed.brand and parsed.brand != "Unknown":
        add_part(parsed.brand)
    
    if parsed.product_line:
        add_part(parsed.product_line)
    elif parsed.model and parsed.model != "Unknown":
        add_part(parsed.model)
    
    # הוסף variant רק אם לא כבר חלק מה-product_line/model
    if parsed.variant and parsed.variant.lower() not in used_words:
        add_part(parsed.variant)
    
    if parsed.capacity:
        add_part(parsed.capacity)
    
    if parsed.color:
        add_part(parsed.color)
    
    return " ".join(parts) if parts else parsed.raw_title


# =============================================================================
# HYBRID PARSING - Structured Data + Rules + LLM Fallback
# =============================================================================

@dataclass
class HybridParsedProduct:
    """תוצאת parsing היברידית עם מקור המידע"""
    brand: Optional[str] = None
    model: Optional[str] = None
    product_line: Optional[str] = None
    color: Optional[str] = None
    capacity: Optional[str] = None
    ram: Optional[str] = None
    size: Optional[str] = None
    year: Optional[int] = None
    generation: Optional[str] = None
    variant: Optional[str] = None
    condition: Optional[str] = None
    connectivity: list[str] = field(default_factory=list)
    attributes: list[str] = field(default_factory=list)
    confidence: float = 0.0
    source: str = "unknown"  # structured, rules, llm, hybrid
    raw_title: str = ""


def clean_brand_name(brand: str) -> str:
    """
    Clean brand name - remove store/official suffixes
    "Sennheiser Store" -> "Sennheiser"
    "Apple Official" -> "Apple"
    """
    if not brand:
        return None
    
    # Patterns to remove
    remove_patterns = [
        r'\s+Store$',
        r'\s+Official$',
        r'\s+Shop$',
        r'\s+Outlet$',
        r'\s+Direct$',
        r'\s+Online$',
        r'^Visit the\s+',
        r'^Visit\s+',
        r'^Brand:\s*',
        r'\s+on Amazon$',
    ]
    
    cleaned = brand.strip()
    for pattern in remove_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE).strip()
    
    return cleaned if cleaned else None


def parse_from_structured(structured: dict) -> HybridParsedProduct:
    """
    Parse product info from structured data (JSON-LD, microdata, meta tags)
    This is the most reliable source - data comes directly from the retailer.
    """
    result = HybridParsedProduct(source="structured")
    
    if not structured:
        return result
    
    # Direct mappings with cleaning
    result.brand = clean_brand_name(structured.get('brand'))
    result.model = structured.get('model')
    result.color = structured.get('color')
    result.capacity = structured.get('capacity')
    
    # Condition mapping
    condition = structured.get('condition', '').lower()
    if 'new' in condition:
        result.condition = 'New'
    elif 'refurbished' in condition or 'renewed' in condition:
        result.condition = 'Refurbished'
    elif 'used' in condition:
        result.condition = 'Used'
    
    # Category can give hints
    category = structured.get('category', '')
    
    # Calculate confidence based on what we got
    extracted_count = sum(1 for v in [result.brand, result.model, result.color, result.capacity] if v)
    result.confidence = min(0.95, 0.5 + (extracted_count * 0.15))  # Max 0.95 for structured
    
    return result


def merge_parsed_results(primary: HybridParsedProduct, secondary: HybridParsedProduct) -> HybridParsedProduct:
    """
    Merge two parsed results, preferring primary but filling in from secondary.
    """
    result = HybridParsedProduct()
    
    # For each field, prefer primary if exists, else use secondary
    result.brand = primary.brand or secondary.brand
    result.model = primary.model or secondary.model
    result.product_line = primary.product_line or secondary.product_line
    result.color = primary.color or secondary.color
    result.capacity = primary.capacity or secondary.capacity
    result.ram = primary.ram or secondary.ram
    result.size = primary.size or secondary.size
    result.year = primary.year or secondary.year
    result.generation = primary.generation or secondary.generation
    result.variant = primary.variant or secondary.variant
    result.condition = primary.condition or secondary.condition
    result.connectivity = primary.connectivity or secondary.connectivity
    result.attributes = list(set(primary.attributes + secondary.attributes))
    result.raw_title = primary.raw_title or secondary.raw_title
    
    # Confidence is the max
    result.confidence = max(primary.confidence, secondary.confidence)
    
    # Source is hybrid if both contributed
    if primary.source != "unknown" and secondary.source != "unknown":
        result.source = "hybrid"
    else:
        result.source = primary.source if primary.source != "unknown" else secondary.source
    
    return result


def parse_with_rules(title: str) -> HybridParsedProduct:
    """
    Parse using rules-based approach (existing logic).
    Converts ParsedTitle to HybridParsedProduct.
    """
    parsed = parse_title(title)
    
    result = HybridParsedProduct(
        brand=parsed.brand if parsed.brand != "Unknown" else None,
        model=parsed.model if parsed.model != "Unknown" else None,
        product_line=parsed.product_line,
        color=parsed.color,
        capacity=parsed.capacity,
        size=parsed.size,
        year=parsed.year,
        generation=parsed.generation,
        variant=parsed.variant,
        condition=parsed.condition,
        connectivity=parsed.connectivity,
        attributes=parsed.attributes,
        confidence=parsed.confidence,
        source="rules",
        raw_title=title
    )
    
    return result


def hybrid_parse(title: str, structured: dict = None) -> HybridParsedProduct:
    """
    MAIN PARSING FUNCTION - Structured Data + Rules
    
    פירוק מידע מוצר משני מקורות:
    1. Structured data (JSON-LD, microdata) - הכי אמין, ישירות מהאתר
    2. Rules-based parsing - מהיר, מכסה 90% מהמקרים
    
    Args:
        title: כותרת המוצר
        structured: מידע מובנה מ-content.js (אופציונלי)
    
    Returns:
        HybridParsedProduct עם התוצאות המשולבות
    """
    # Step 1: Try structured data first (most reliable - from retailer)
    structured_result = parse_from_structured(structured) if structured else HybridParsedProduct()
    
    # Step 2: Run rules-based parsing (covers 90% of popular products)
    rules_result = parse_with_rules(title)
    
    # Step 3: Merge results (prefer structured, fill gaps with rules)
    result = merge_parsed_results(structured_result, rules_result)
    result.raw_title = title
    
    return result


def get_hybrid_search_query(parsed: HybridParsedProduct) -> str:
    """
    Generate optimized search query from hybrid parsed result.
    """
    parts = []
    used_words = set()
    
    def add_part(text: str):
        if not text:
            return
        words = text.lower().split()
        new_words = [w for w in words if w not in used_words]
        if len(new_words) > len(words) / 2 or not used_words:
            parts.append(text)
            used_words.update(words)
    
    add_part(parsed.brand)
    add_part(parsed.model or parsed.product_line)
    
    if parsed.variant and parsed.variant.lower() not in used_words:
        add_part(parsed.variant)
    
    add_part(parsed.capacity)
    add_part(parsed.color)
    
    return " ".join(parts) if parts else parsed.raw_title


# =============================================================================
# BACKWARDS COMPATIBILITY
# =============================================================================

# שמירה על תאימות עם הקוד הישן
def parse_title_legacy(title: str):
    """Wrapper לתאימות לאחור"""
    parsed = parse_title(title)
    return ParsedTitle(
        brand=parsed.brand,
        model=parsed.model,
        attributes=parsed.attributes
    )


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    # בדיקות
    test_titles = [
        "Apple iPhone 15 Pro Max 256GB Natural Titanium",
        "Samsung Galaxy S24 Ultra 512GB Titanium Black 5G Unlocked",
        "Sony WH-1000XM5 Wireless Noise Cancelling Headphones Black",
        "Dyson V15 Detect Absolute Cordless Vacuum Cleaner",
        "LEVOIT Core 300S Smart True HEPA Air Purifier White",
        "Dell XPS 15 9530 Laptop 15.6\" OLED 4K Intel i7-13700H 32GB RAM 1TB SSD",
        "Bose QuietComfort Ultra Earbuds - Black",
        "Logitech MX Master 3S Wireless Mouse - Graphite",
        "JBL Flip 6 Portable Bluetooth Speaker Waterproof - Red",
        "Nintendo Switch OLED Model - White",
        "Refurbished Apple MacBook Pro 14\" M3 Pro 18GB 512GB Space Gray 2023",
        "Google Pixel 8 Pro 256GB Obsidian 5G Unlocked",
        "Microsoft Surface Pro 9 13\" Intel i7 16GB RAM 256GB SSD Platinum",
        "Amazon Echo Dot 5th Gen Smart Speaker with Alexa Charcoal",
        "Anker PowerCore 26800 Portable Charger Power Bank",
    ]
    
    print("=" * 80)
    print("PARSING TESTS")
    print("=" * 80)
    
    for title in test_titles:
        print(f"\n[TITLE] {title}")
        parsed = parse_title(title)
        print(f"   Brand: {parsed.brand}")
        print(f"   Model: {parsed.model}")
        print(f"   Product Line: {parsed.product_line}")
        print(f"   Color: {parsed.color}")
        print(f"   Capacity: {parsed.capacity}")
        print(f"   Year: {parsed.year}")
        print(f"   Variant: {parsed.variant}")
        print(f"   Condition: {parsed.condition}")
        print(f"   Connectivity: {parsed.connectivity}")
        print(f"   Attributes: {parsed.attributes}")
        print(f"   Confidence: {parsed.confidence}")
        print(f"   [SEARCH] {get_search_query(parsed)}")
        print("-" * 80)
