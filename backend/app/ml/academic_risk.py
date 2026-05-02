"""
Academic K.T. risk engine.

This is intentionally a transparent rules model. It gives the university a
usable early-warning system now, while collecting labelled final-result data
for a trained model later.
"""
from typing import Dict, Optional


MODEL_VERSION = "academic-rules-v1"


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _risk_from_percentage(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return 100.0 - _clamp(value)


def _level(score: float) -> str:
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def _confidence(data_completeness: float) -> str:
    if data_completeness >= 75:
        return "High"
    if data_completeness >= 45:
        return "Medium"
    return "Low"


def calculate_academic_risk(signals: Dict) -> Dict:
    weights = {
        "attendance_pct": 0.25,
        "internal_avg_pct": 0.30,
        "assignment_health_pct": 0.20,
        "practical_avg_pct": 0.10,
        "prior_kt_risk": 0.10,
        "self_assessment_risk": 0.05,
    }

    assignment_avg = signals.get("assignment_avg_pct")
    assignment_completion = signals.get("assignment_completion_pct")
    assignment_health = None
    if assignment_avg is not None and assignment_completion is not None:
        assignment_health = (assignment_avg * 0.65) + (assignment_completion * 0.35)
    elif assignment_avg is not None:
        assignment_health = assignment_avg
    elif assignment_completion is not None:
        assignment_health = assignment_completion

    prior_kt_count = signals.get("prior_kt_count")
    prior_kt_risk = None if prior_kt_count is None else _clamp(float(prior_kt_count) * 30.0)

    risk_inputs = {
        "attendance_pct": _risk_from_percentage(signals.get("attendance_pct")),
        "internal_avg_pct": _risk_from_percentage(signals.get("internal_avg_pct")),
        "assignment_health_pct": _risk_from_percentage(assignment_health),
        "practical_avg_pct": _risk_from_percentage(signals.get("practical_avg_pct")),
        "prior_kt_risk": prior_kt_risk,
        "self_assessment_risk": signals.get("self_assessment_risk"),
    }

    available_weight = sum(weights[k] for k, v in risk_inputs.items() if v is not None)
    total_weight = sum(weights.values())
    data_completeness = round((available_weight / total_weight) * 100, 1) if total_weight else 0.0

    if available_weight == 0:
        raw_score = 50.0
    else:
        raw_score = sum(risk_inputs[k] * weights[k] for k in weights if risk_inputs[k] is not None) / available_weight

    # Low-data predictions should stay cautious instead of pretending certainty.
    completeness_ratio = data_completeness / 100.0
    risk_score = (raw_score * completeness_ratio) + (50.0 * (1.0 - completeness_ratio))
    risk_score = round(_clamp(risk_score), 1)

    factors = {
        "signals": {
            "attendance_pct": signals.get("attendance_pct"),
            "internal_avg_pct": signals.get("internal_avg_pct"),
            "assignment_avg_pct": assignment_avg,
            "assignment_completion_pct": assignment_completion,
            "practical_avg_pct": signals.get("practical_avg_pct"),
            "prior_kt_count": prior_kt_count,
            "self_assessment_risk": signals.get("self_assessment_risk"),
        },
        "main_risk_factors": [],
        "protective_factors": [],
        "missing_data": [],
    }

    labels = {
        "attendance_pct": "Attendance",
        "internal_avg_pct": "Internal exam performance",
        "assignment_health_pct": "Assignment completion/performance",
        "practical_avg_pct": "Practical/lab performance",
        "prior_kt_risk": "Previous KT history",
        "self_assessment_risk": "Student self-assessment",
    }

    for key, risk in risk_inputs.items():
        if risk is None:
            factors["missing_data"].append(labels[key])
            continue
        value = round(risk, 1)
        if value >= 55:
            factors["main_risk_factors"].append({
                "factor": labels[key],
                "risk_contribution": value,
                "message": f"{labels[key]} is currently increasing KT risk.",
            })
        elif value <= 25:
            factors["protective_factors"].append({
                "factor": labels[key],
                "risk_contribution": value,
                "message": f"{labels[key]} is currently helping reduce KT risk.",
            })

    if signals.get("attendance_pct") is not None and signals["attendance_pct"] < 65:
        factors["main_risk_factors"].append({
            "factor": "Attendance threshold",
            "risk_contribution": round(100 - signals["attendance_pct"], 1),
            "message": "Attendance is below the usual safe zone; this needs quick teacher follow-up.",
        })

    recommendations = {
        "student_actions": [],
        "teacher_actions": [],
        "next_review": "Review again after the next internal test or assignment cycle.",
    }

    if signals.get("attendance_pct") is not None and signals["attendance_pct"] < 75:
        recommendations["student_actions"].append("Attend the next two weeks of lectures/labs without gaps.")
        recommendations["teacher_actions"].append("Check attendance barrier and contact the student if absence continues.")
    if signals.get("internal_avg_pct") is not None and signals["internal_avg_pct"] < 45:
        recommendations["student_actions"].append("Revise weak units and attempt a short diagnostic test this week.")
        recommendations["teacher_actions"].append("Assign a targeted remedial test covering low-scoring units.")
    if assignment_completion is not None and assignment_completion < 80:
        recommendations["student_actions"].append("Clear pending assignments before the next review.")
        recommendations["teacher_actions"].append("Give a recovery assignment with a strict but realistic deadline.")
    if signals.get("practical_avg_pct") is not None and signals["practical_avg_pct"] < 50:
        recommendations["student_actions"].append("Book lab practice time and repeat the weakest practical task.")
        recommendations["teacher_actions"].append("Schedule supervised lab revision for this student.")
    if prior_kt_count:
        recommendations["teacher_actions"].append("Treat this as a repeat-risk case and monitor weekly.")

    if not recommendations["student_actions"]:
        recommendations["student_actions"].append("Maintain attendance, assignment completion, and internal test practice.")
    if not recommendations["teacher_actions"]:
        recommendations["teacher_actions"].append("Keep the student on regular monitoring; no urgent intervention is required.")

    return {
        "risk_score": risk_score,
        "risk_level": _level(risk_score),
        "confidence": _confidence(data_completeness),
        "data_completeness": data_completeness,
        "factors": factors,
        "recommendations": recommendations,
        "model_version": MODEL_VERSION,
    }
