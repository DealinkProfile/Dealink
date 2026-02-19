# backend/app/services/similarity.py
"""
String similarity utilities - Jaro-Winkler
"""
# Copy from existing similarity.py
def jaro_winkler_similarity(s1: str, s2: str) -> float:
    """
    חישוב Jaro-Winkler similarity בין שני strings
    מחזיר ערך בין 0 ל-1 (1 = זהה לחלוטין)
    """
    if not s1 or not s2:
        return 0.0
    
    s1 = s1.lower().strip()
    s2 = s2.lower().strip()
    
    if s1 == s2:
        return 1.0
    
    # Jaro distance
    match_window = max(len(s1), len(s2)) // 2 - 1
    if match_window < 0:
        match_window = 0
    
    s1_matches = [False] * len(s1)
    s2_matches = [False] * len(s2)
    
    matches = 0
    transpositions = 0
    
    # מצא matches
    for i in range(len(s1)):
        start = max(0, i - match_window)
        end = min(i + match_window + 1, len(s2))
        
        for j in range(start, end):
            if s2_matches[j] or s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break
    
    if matches == 0:
        return 0.0
    
    # מצא transpositions
    k = 0
    for i in range(len(s1)):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1
    
    jaro = (matches / len(s1) + matches / len(s2) + (matches - transpositions / 2) / matches) / 3.0
    
    # Winkler modification - prefix bonus
    prefix = 0
    for i in range(min(len(s1), len(s2), 4)):
        if s1[i] == s2[i]:
            prefix += 1
        else:
            break
    
    winkler = jaro + (0.1 * prefix * (1 - jaro))
    
    return min(1.0, winkler)


def are_similar(title1: str, title2: str, threshold: float = 0.7) -> bool:
    """
    בודק אם שני titles דומים מספיק (מעל threshold)
    """
    return jaro_winkler_similarity(title1, title2) >= threshold


def find_best_match(query_title: str, candidates: list[str], threshold: float = 0.6) -> tuple[str, float] | None:
    """
    מוצא את ה-candidate הכי דומה ל-query_title
    מחזיר (title, similarity_score) או None אם אין match מעל threshold
    """
    best_match = None
    best_score = 0.0
    
    for candidate in candidates:
        score = jaro_winkler_similarity(query_title, candidate)
        if score > best_score:
            best_score = score
            best_match = candidate
    
    if best_score >= threshold:
        return (best_match, best_score)
    return None

