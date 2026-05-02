"""
K.T. Risk Prediction Engine
Hybrid approach: weighted scoring + statistical analysis.
"""
import numpy as np
from typing import List, Dict, Tuple


def predict_risk(answer_data: List[Dict]) -> Tuple[float, str, Dict]:
    """
    Predict K.T. risk from student assessment answers.

    Each answer_data item contains:
      - value: student's self-reported score
      - max_val: maximum possible score
      - min_val: minimum possible score
      - weight: importance weight
      - category: question category
      - text: question text

    Returns:
      - risk_score (0-100): higher = more risk
      - risk_level: "Low" / "Medium" / "High"
      - factors: breakdown of contributing factors
    """
    if not answer_data:
        return 50.0, "Medium", {"note": "No data provided"}

    # Normalize each answer to 0-1 scale (inverted: low score = high risk)
    normalized_scores = []
    category_scores = {}
    total_weight = 0

    for item in answer_data:
        val = float(item["value"])
        max_v = float(item["max_val"])
        min_v = float(item["min_val"])
        weight = float(item["weight"])
        category = item["category"]

        range_v = max_v - min_v if max_v != min_v else 1
        normalized = (val - min_v) / range_v  # 0 = worst, 1 = best
        weighted_score = normalized * weight

        normalized_scores.append(weighted_score)
        total_weight += weight

        if category not in category_scores:
            category_scores[category] = {"scores": [], "weights": [], "questions": []}
        category_scores[category]["scores"].append(normalized)
        category_scores[category]["weights"].append(weight)
        category_scores[category]["questions"].append(item["text"])

    # Overall risk: invert so high risk = high score
    if total_weight > 0:
        overall_performance = sum(normalized_scores) / total_weight
    else:
        overall_performance = 0.5

    # Apply non-linear transformation for more realistic risk distribution
    # Students with very low scores should have exponentially higher risk
    risk_score = (1 - overall_performance) * 100

    # Apply sigmoid-like scaling for more differentiation
    if risk_score > 70:
        risk_score = min(95, risk_score * 1.1)
    elif risk_score < 30:
        risk_score = max(5, risk_score * 0.9)

    risk_score = round(min(100, max(0, risk_score)), 1)

    # Determine risk level
    if risk_score >= 65:
        risk_level = "High"
    elif risk_score >= 35:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    # Build factor analysis
    factors = {"category_analysis": {}, "weak_areas": [], "strong_areas": [], "overall_performance": round(overall_performance * 100, 1)}

    for cat, data in category_scores.items():
        avg_score = np.average(data["scores"], weights=data["weights"])
        cat_risk = round((1 - avg_score) * 100, 1)
        factors["category_analysis"][cat] = {
            "risk_contribution": cat_risk,
            "avg_score_pct": round(avg_score * 100, 1),
            "num_questions": len(data["scores"]),
        }

        if avg_score < 0.4:
            factors["weak_areas"].append({
                "category": cat,
                "score_pct": round(avg_score * 100, 1),
                "concern": f"Significant weakness in {cat} — needs focused improvement",
            })
        elif avg_score >= 0.7:
            factors["strong_areas"].append({
                "category": cat,
                "score_pct": round(avg_score * 100, 1),
            })

    # Variance penalty: inconsistent scores indicate unstable preparation
    if len(normalized_scores) > 2:
        score_variance = float(np.var([s / w if w > 0 else 0 for s, w in zip(normalized_scores, [d["weight"] for d in answer_data])]))
        if score_variance > 0.1:
            factors["consistency_warning"] = "Highly inconsistent scores — some areas strong but others critically weak"

    return risk_score, risk_level, factors
