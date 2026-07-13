# Configurable Weights
WEIGHT_PPE = 0.3
WEIGHT_ZONE = 0.4
WEIGHT_ANOMALY = 0.2
WEIGHT_TREND = 0.1

def compute_risk_score(ppe_flags: dict, zone_risk: str, anomaly_score: float, predicted_trend: float) -> float:
    """
    Computes a weighted risk score between 0 and 1.
    """
    score = 0.0
    
    # PPE
    if ppe_flags:
        if not ppe_flags.get("helmet", False):
            score += WEIGHT_PPE * 0.5
        if not ppe_flags.get("vest", False):
            score += WEIGHT_PPE * 0.5
        
    # Zone
    if zone_risk == "CRITICAL":
        score += WEIGHT_ZONE * 1.0
    elif zone_risk == "CAUTION":
        score += WEIGHT_ZONE * 0.5
        
    # Anomaly
    score += WEIGHT_ANOMALY * anomaly_score
    
    # Trend
    score += WEIGHT_TREND * predicted_trend
    
    return min(1.0, max(0.0, score))
