# Configurable Weights
WEIGHT_PPE = 0.3
WEIGHT_ZONE = 0.4
WEIGHT_ANOMALY = 0.2
WEIGHT_TREND = 0.1


def compute_risk_score(ppe_flags: dict, zone_risk: str, anomaly_score, predicted_trend) -> float:
    """
    Computes a weighted risk score between 0 and 1.

    anomaly_score / predicted_trend may be None when those models aren't
    loaded (see anomaly_model.py / risk_predictor.py) — in that case their
    weight is excluded and the remaining weights are renormalized, rather
    than silently treating "unavailable" as "zero risk".
    """
    contributions = {}

    if ppe_flags:
        ppe_score = 0.0
        if not ppe_flags.get("helmet", False):
            ppe_score += 0.5
        if not ppe_flags.get("vest", False):
            ppe_score += 0.5
        contributions[WEIGHT_PPE] = ppe_score

    if zone_risk == "CRITICAL":
        contributions[WEIGHT_ZONE] = 1.0
    elif zone_risk == "CAUTION":
        contributions[WEIGHT_ZONE] = 0.5
    else:
        contributions[WEIGHT_ZONE] = 0.0

    if anomaly_score is not None:
        contributions[WEIGHT_ANOMALY] = anomaly_score

    if predicted_trend is not None:
        contributions[WEIGHT_TREND] = predicted_trend

    total_weight = sum(contributions.keys())
    if total_weight == 0:
        return 0.0

    score = sum(w * v for w, v in contributions.items()) / total_weight
    return min(1.0, max(0.0, score))
