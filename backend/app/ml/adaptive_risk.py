"""
Adaptive K.T. Risk Engine v2
─────────────────────────────
"Feels human, not like a machine."

A good teacher doesn't define a student by their worst semester.
They notice who's improving, who's slipping, and who just needs a nudge.
This engine works the same way.

Design principles:
  1. MOMENTUM > HISTORY — a rising trajectory reduces risk even with a bad past.
  2. REDEMPTION IS REAL — prior KTs lose weight when current performance is strong.
  3. TRENDS BEAT SNAPSHOTS — declining attendance matters more than one low reading.
  4. ENGAGEMENT COUNTS — a student who shows up and submits work gets benefit of doubt.
  5. HONESTY — when data is thin, say "I don't know" instead of pretending confidence.
  6. EXPLAIN LIKE A MENTOR — every prediction comes with a plain-language narrative.
"""
from typing import Dict, List, Optional

MODEL_VERSION = "adaptive-v2"


# ── Utilities ────────────────────────────────────────────────────────────────

def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _risk_from_pct(value: Optional[float]) -> Optional[float]:
    """Higher performance → lower risk."""
    return None if value is None else 100.0 - _clamp(value)


def _level(score: float) -> str:
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def _avg(values: list) -> Optional[float]:
    clean = [v for v in values if v is not None]
    return sum(clean) / len(clean) if clean else None


# ── Confidence (richer than before) ──────────────────────────────────────────

def _confidence(data_completeness: float, total_records: int) -> str:
    """
    Confidence depends on BOTH signal coverage and volume of records.
    5 signals present but only 1 record each → Medium at best.
    """
    if data_completeness >= 75 and total_records >= 8:
        return "High"
    if data_completeness >= 50 and total_records >= 4:
        return "Medium"
    if data_completeness >= 30 or total_records >= 2:
        return "Low"
    return "Very Low"


# ── Student Archetypes ───────────────────────────────────────────────────────

def _classify_archetype(
    current_perf: Optional[float],
    momentum: float,
    prior_kts: int,
    data_completeness: float,
) -> str:
    """
    Classify the student into a human-recognisable pattern.
    Teachers think in these patterns — the engine should too.
    """
    if data_completeness < 20:
        return "new_student"

    perf = current_perf if current_perf is not None else 50.0

    if prior_kts > 0 and perf >= 55 and momentum >= 0:
        return "comeback_kid"
    if prior_kts > 0 and momentum > 8:
        return "comeback_kid"
    if perf >= 60 and momentum < -8:
        return "slipping_star"
    if perf >= 60 and momentum >= -3:
        return "consistent_performer"
    if perf < 50 and momentum > 5:
        return "rising_student"
    if perf < 40 and momentum <= 0:
        return "struggling_student"
    if momentum > 10:
        return "rising_student"
    return "moderate_student"


ARCHETYPE_LABELS = {
    "new_student": "New — Not enough data yet",
    "comeback_kid": "Comeback — Improving despite past setbacks",
    "slipping_star": "Slipping — Was strong but trending down",
    "consistent_performer": "Consistent — Doing well, keep going",
    "rising_student": "Rising — Scores are low but improving",
    "struggling_student": "Struggling — Needs focused support",
    "moderate_student": "Moderate — Average, room to grow",
}


# ── Core Calculations ────────────────────────────────────────────────────────

def _compute_base_risk(signals: Dict) -> tuple:
    """Weighted risk from the current-state signals (snapshot)."""
    weights = {
        "attendance_pct": 0.25,
        "internal_avg_pct": 0.30,
        "assignment_health_pct": 0.20,
        "practical_avg_pct": 0.10,
        "self_assessment_risk": 0.05,
    }

    # Composite assignment health
    a_avg = signals.get("assignment_avg_pct")
    a_comp = signals.get("assignment_completion_pct")
    if a_avg is not None and a_comp is not None:
        assignment_health = a_avg * 0.65 + a_comp * 0.35
    elif a_avg is not None:
        assignment_health = a_avg
    elif a_comp is not None:
        assignment_health = a_comp
    else:
        assignment_health = None

    risk_inputs = {
        "attendance_pct": _risk_from_pct(signals.get("attendance_pct")),
        "internal_avg_pct": _risk_from_pct(signals.get("internal_avg_pct")),
        "assignment_health_pct": _risk_from_pct(assignment_health),
        "practical_avg_pct": _risk_from_pct(signals.get("practical_avg_pct")),
        "self_assessment_risk": signals.get("self_assessment_risk"),
    }

    available = sum(weights[k] for k, v in risk_inputs.items() if v is not None)
    total = sum(weights.values())
    completeness = round((available / total) * 100, 1) if total else 0.0

    if available == 0:
        base = 50.0
    else:
        base = sum(
            risk_inputs[k] * weights[k]
            for k in weights
            if risk_inputs[k] is not None
        ) / available

    # Current overall performance (0-100, higher = better)
    perf_values = [
        signals.get("attendance_pct"),
        signals.get("internal_avg_pct"),
        assignment_health,
        signals.get("practical_avg_pct"),
    ]
    current_perf = _avg(perf_values)

    return base, completeness, risk_inputs, current_perf


def _compute_momentum(trends: Dict) -> float:
    """
    Aggregate trend across all signals.
    Positive = student is improving.  Negative = declining.
    Returns a value roughly in the range -30 to +30.
    """
    trend_keys = [
        ("attendance_trend", 1.0),
        ("internal_trend", 1.3),      # exam trends matter most
        ("assignment_score_trend", 0.8),
        ("practical_trend", 0.7),
    ]

    weighted_sum = 0.0
    weight_total = 0.0

    for key, w in trend_keys:
        val = trends.get(key)
        if val is not None:
            weighted_sum += val * w
            weight_total += w

    # Self-assessment trend is inverted (lower risk = positive momentum)
    sa_trend = trends.get("self_assessment_trend")
    if sa_trend is not None:
        weighted_sum += (-sa_trend) * 0.3
        weight_total += 0.3

    if weight_total == 0:
        return 0.0

    raw_momentum = weighted_sum / weight_total

    # Scale: a 10-point improvement across signals → ~15 point momentum bonus
    return _clamp(raw_momentum * 1.5, -30, 30)


def _compute_redemption(prior_kt_count: int, current_perf: Optional[float]) -> float:
    """
    Prior KTs add risk, but the penalty SHRINKS when the student is clearly
    performing well right now.  A teacher would say: "Yes they failed before,
    but look at them now — they've turned it around."

    Returns the ADJUSTED risk contribution from prior KTs (0-100).
    """
    if prior_kt_count == 0:
        return 0.0

    base_kt_risk = _clamp(float(prior_kt_count) * 30.0)
    perf = current_perf if current_perf is not None else 50.0

    # Redemption multiplier: good current performance → KTs matter less
    if perf >= 75:
        multiplier = 0.10   # almost fully redeemed
    elif perf >= 65:
        multiplier = 0.25
    elif perf >= 55:
        multiplier = 0.45
    elif perf >= 45:
        multiplier = 0.70
    else:
        multiplier = 1.0    # still struggling — past KTs remain fully relevant

    return base_kt_risk * multiplier


def _compute_engagement(signals: Dict, trends: Dict) -> float:
    """
    Is the student TRYING?  A student who attends, submits, and participates
    deserves benefit of the doubt even if scores aren't great yet.
    Returns 0-15 risk reduction.
    """
    points = 0.0

    att = signals.get("attendance_pct")
    if att is not None and att >= 80:
        points += 4.0
    elif att is not None and att >= 70:
        points += 2.0

    comp = signals.get("assignment_completion_pct")
    if comp is not None and comp >= 90:
        points += 4.0
    elif comp is not None and comp >= 75:
        points += 2.0

    att_trend = trends.get("attendance_trend")
    if att_trend is not None and att_trend > 3:
        points += 3.0

    asc_trend = trends.get("assignment_score_trend")
    if asc_trend is not None and asc_trend > 3:
        points += 2.0

    records = trends.get("total_records", 0)
    if records >= 10:
        points += 2.0
    elif records >= 5:
        points += 1.0

    return min(15.0, points)


# ── Narrative Generation ─────────────────────────────────────────────────────

def _trend_word(val: Optional[float]) -> str:
    if val is None:
        return ""
    if val > 10:
        return "improving strongly"
    if val > 3:
        return "improving"
    if val > -3:
        return "stable"
    if val > -10:
        return "declining"
    return "dropping sharply"


def _generate_narrative(
    signals: Dict,
    trends: Dict,
    prior_kts: int,
    archetype: str,
    risk_score: float,
    risk_level: str,
    momentum: float,
    redemption_risk: float,
    data_completeness: float,
) -> List[str]:
    """
    Build a list of plain-language sentences — the way a mentor would
    talk to a student or explain the situation to a teacher.
    """
    lines: List[str] = []
    att = signals.get("attendance_pct")
    int_avg = signals.get("internal_avg_pct")
    a_comp = signals.get("assignment_completion_pct")
    a_avg = signals.get("assignment_avg_pct")
    prac = signals.get("practical_avg_pct")

    att_trend = trends.get("attendance_trend")
    int_trend = trends.get("internal_trend")

    # ── Archetype-specific opening ──
    if archetype == "new_student":
        lines.append(
            "We don't have enough academic data for a confident prediction yet. "
            "The score shown is a cautious estimate. As more attendance, scores, "
            "and assignments get recorded, the prediction will become much sharper."
        )
        return lines

    if archetype == "comeback_kid":
        lines.append(
            f"You have {prior_kts} prior KT(s) on record, but your current performance "
            f"tells a different story. The system is giving you significant credit for "
            f"this improvement — past KTs are weighing much less in this prediction."
        )
    elif archetype == "slipping_star":
        lines.append(
            "Your past performance was strong, but recent trends are heading in the "
            "wrong direction. This prediction is based on where things are going, "
            "not where they were."
        )
    elif archetype == "rising_student":
        lines.append(
            "Your scores are still below where they need to be, but the upward trend "
            "is real and the system is recognising it. Keep the momentum — it's "
            "already reducing your risk."
        )
    elif archetype == "struggling_student":
        lines.append(
            "Multiple signals are pointing to difficulty right now. This isn't a "
            "judgement — it's a prompt to get targeted help before finals."
        )
    elif archetype == "consistent_performer":
        lines.append(
            "Things look solid. The prediction is low-risk because your current "
            "signals are consistently healthy."
        )
    else:
        lines.append(
            "You're in a moderate zone — not in danger but with room to improve. "
            "Targeted effort on weak areas can make a real difference."
        )

    # ── Specific signal commentary ──
    if att is not None:
        if att < 65:
            word = f" and {_trend_word(att_trend)}" if att_trend is not None else ""
            lines.append(
                f"Attendance is at {att}%{word}. This is below the safe zone and "
                f"is the single easiest thing to fix."
            )
        elif att_trend is not None and att_trend < -8:
            lines.append(
                f"Attendance was fine earlier but has dropped recently "
                f"({_trend_word(att_trend)}). This pattern often predicts trouble "
                f"even when exam scores are still okay."
            )

    if int_avg is not None and int_trend is not None:
        if int_trend > 8:
            lines.append(
                f"Internal exam average is {int_avg}% and {_trend_word(int_trend)}. "
                f"This positive trajectory is being rewarded in the prediction."
            )
        elif int_trend < -8:
            lines.append(
                f"Internal exam average is {int_avg}% but {_trend_word(int_trend)}. "
                f"Scores are moving the wrong way and this is the heaviest signal."
            )

    if a_comp is not None and a_comp < 70:
        lines.append(
            f"Only {a_comp}% of assignments have been submitted. "
            f"Missing work adds up fast in the prediction."
        )

    if prac is not None and prac < 45:
        lines.append(
            f"Practical/lab average is at {prac}%. "
            f"Book extra lab time — practicals are scored generously when you show up prepared."
        )

    # ── Momentum summary ──
    if momentum > 10:
        lines.append(
            "Overall momentum is strongly positive — the system is reducing risk "
            "because you're clearly putting in the work."
        )
    elif momentum > 3:
        lines.append(
            "There's a positive trend across your signals. "
            "Sustaining this will continue to bring down your risk."
        )
    elif momentum < -10:
        lines.append(
            "The overall trend is downward across multiple areas. "
            "This is increasing the risk significantly — a course correction now matters."
        )
    elif momentum < -3:
        lines.append(
            "Some signals are starting to dip. It's not critical yet but "
            "worth paying attention to before it compounds."
        )

    # ── Redemption note ──
    if prior_kts > 0 and redemption_risk < prior_kts * 15:
        lines.append(
            f"Note: Your {prior_kts} prior KT(s) would normally add significant risk, "
            f"but your current performance has reduced that penalty substantially. "
            f"This system believes in second chances backed by evidence."
        )

    return lines


# ── Recommendation Generation ────────────────────────────────────────────────

def _generate_recommendations(
    signals: Dict,
    trends: Dict,
    prior_kts: int,
    archetype: str,
    risk_level: str,
) -> Dict:
    student_actions = []
    teacher_actions = []

    att = signals.get("attendance_pct")
    int_avg = signals.get("internal_avg_pct")
    a_comp = signals.get("assignment_completion_pct")
    prac = signals.get("practical_avg_pct")
    att_trend = trends.get("attendance_trend")
    int_trend = trends.get("internal_trend")

    # ── Attendance ──
    if att is not None and att < 65:
        student_actions.append(
            "Make attendance your #1 priority for the next 2 weeks — "
            "attend every lecture and lab without exception."
        )
        teacher_actions.append(
            "Contact this student directly to understand the attendance barrier. "
            "Consider an attendance-recovery agreement."
        )
    elif att is not None and att < 75:
        student_actions.append(
            "Attendance is borderline. Aim for zero absences in the next 2 weeks "
            "to get it above the safe threshold."
        )
        teacher_actions.append(
            "Flag this student for attendance monitoring at the next review."
        )
    elif att_trend is not None and att_trend < -8:
        student_actions.append(
            "Your attendance was good but is slipping. "
            "Don't let the trend continue — it compounds quickly."
        )
        teacher_actions.append(
            "Attendance is declining — check in with the student proactively."
        )

    # ── Internals ──
    if int_avg is not None and int_avg < 35:
        student_actions.append(
            "Internal scores need urgent attention. Focus on the 2-3 weakest "
            "topics and attempt practice tests this week."
        )
        teacher_actions.append(
            "Assign a targeted remedial test on low-scoring units. "
            "Consider one-on-one concept clearing sessions."
        )
    elif int_avg is not None and int_avg < 50:
        student_actions.append(
            "Internal scores are below average. Prioritise revision of weak "
            "chapters and solve past papers."
        )
        teacher_actions.append(
            "Provide extra practice problems for this student's weak units."
        )
    elif int_trend is not None and int_trend > 8:
        student_actions.append(
            "Your exam scores are improving — great work. "
            "Maintain the study routine that's producing results."
        )

    # ── Assignments ──
    if a_comp is not None and a_comp < 70:
        student_actions.append(
            "Submit all pending assignments immediately — even partial work "
            "counts more than missing work."
        )
        teacher_actions.append(
            "Set a firm but realistic deadline for overdue assignments. "
            "A recovery assignment can help."
        )

    # ── Practicals ──
    if prac is not None and prac < 45:
        student_actions.append(
            "Book extra lab practice time. Repeat the weakest practical "
            "until you can do it independently."
        )
        teacher_actions.append(
            "Schedule supervised lab revision for this student."
        )

    # ── KT history ──
    if prior_kts > 0 and archetype != "comeback_kid":
        teacher_actions.append(
            f"This student has {prior_kts} prior KT(s). "
            f"Treat as a repeat-risk case and monitor weekly."
        )
    elif prior_kts > 0 and archetype == "comeback_kid":
        teacher_actions.append(
            f"This student has {prior_kts} prior KT(s) but is showing strong "
            f"improvement. Encourage them — recognition of growth reinforces it."
        )

    # ── Fallbacks ──
    if not student_actions:
        if risk_level == "Low":
            student_actions.append(
                "You're in a good position. Maintain consistency and stay on "
                "top of all submissions."
            )
        else:
            student_actions.append(
                "Keep attending regularly, submit all work on time, and revise "
                "steadily — small consistent effort compounds."
            )

    if not teacher_actions:
        if risk_level == "Low":
            teacher_actions.append(
                "No urgent action needed. Regular monitoring is sufficient."
            )
        else:
            teacher_actions.append(
                "Continue monitoring — check in at the next review cycle."
            )

    # ── Next review timing ──
    if risk_level == "High":
        next_review = "Review within 1 week — this student needs timely follow-up."
    elif risk_level == "Medium":
        next_review = "Review after the next internal test or assignment deadline."
    else:
        next_review = "Review at the regular next cycle — no urgency."

    return {
        "student_actions": student_actions,
        "teacher_actions": teacher_actions,
        "next_review": next_review,
    }


# ── Main Entry Point ─────────────────────────────────────────────────────────

def calculate_adaptive_risk(
    signals: Dict,
    trends: Dict,
) -> Dict:
    """
    Full adaptive risk calculation.

    Parameters
    ----------
    signals : dict
        Current-state signals from risk_service.build_signals().
        Keys: attendance_pct, internal_avg_pct, assignment_avg_pct,
              assignment_completion_pct, practical_avg_pct,
              prior_kt_count, self_assessment_risk.

    trends : dict
        Trend signals from risk_service.build_trend_signals().
        Keys: attendance_trend, internal_trend, assignment_score_trend,
              practical_trend, self_assessment_trend, total_records.

    Returns
    -------
    dict  — same shape as the old academic_risk engine so the rest of the
            codebase stays compatible.
    """
    prior_kts = signals.get("prior_kt_count", 0) or 0
    total_records = trends.get("total_records", 0)

    # Step 1: Base risk from current snapshot
    base_risk, signal_completeness, risk_inputs, current_perf = (
        _compute_base_risk(signals)
    )

    # Step 2: Momentum — are things getting better or worse?
    momentum = _compute_momentum(trends)

    # Step 3: Redemption — how much should prior KTs matter right now?
    redemption_risk = _compute_redemption(prior_kts, current_perf)

    # Step 4: Engagement — is the student showing effort?
    engagement_bonus = _compute_engagement(signals, trends)

    # Step 5: Blend everything
    #   - Base risk carries 70% of the weight (what signals currently say)
    #   - Prior KT risk carries 10% (adjusted by redemption)
    #   - Momentum can swing ±30 points
    #   - Engagement reduces by up to 15 points
    kt_contribution = redemption_risk * 0.10
    raw_risk = base_risk + kt_contribution - momentum - engagement_bonus

    # Data completeness shrinkage: pull toward 50 when data is thin
    #   Include record volume in completeness
    volume_bonus = min(20, total_records * 2.5)
    data_completeness = min(100.0, signal_completeness * 0.7 + volume_bonus * 0.3 + signal_completeness * 0.3)
    data_completeness = round(_clamp(data_completeness, 0, 100), 1)

    completeness_ratio = data_completeness / 100.0
    risk_score = (raw_risk * completeness_ratio) + (50.0 * (1.0 - completeness_ratio))
    risk_score = round(_clamp(risk_score), 1)

    risk_level_str = _level(risk_score)
    conf = _confidence(data_completeness, total_records)

    # Step 6: Classify archetype
    archetype = _classify_archetype(current_perf, momentum, prior_kts, data_completeness)

    # Step 7: Build factors (backward-compatible with the old engine)
    factors = {
        "signals": {
            "attendance_pct": signals.get("attendance_pct"),
            "internal_avg_pct": signals.get("internal_avg_pct"),
            "assignment_avg_pct": signals.get("assignment_avg_pct"),
            "assignment_completion_pct": signals.get("assignment_completion_pct"),
            "practical_avg_pct": signals.get("practical_avg_pct"),
            "prior_kt_count": prior_kts,
            "self_assessment_risk": signals.get("self_assessment_risk"),
        },
        "main_risk_factors": [],
        "protective_factors": [],
        "missing_data": [],
        # ── New fields ──
        "momentum": round(momentum, 1),
        "momentum_label": (
            "Strongly improving" if momentum > 10 else
            "Improving" if momentum > 3 else
            "Stable" if momentum > -3 else
            "Declining" if momentum > -10 else
            "Dropping sharply"
        ),
        "engagement_bonus": round(engagement_bonus, 1),
        "redemption_applied": prior_kts > 0 and redemption_risk < prior_kts * 20,
        "archetype": archetype,
        "archetype_label": ARCHETYPE_LABELS.get(archetype, ""),
        "trends": {
            "attendance": _trend_word(trends.get("attendance_trend")),
            "internals": _trend_word(trends.get("internal_trend")),
            "assignments": _trend_word(trends.get("assignment_score_trend")),
            "practicals": _trend_word(trends.get("practical_trend")),
        },
        "narrative": _generate_narrative(
            signals, trends, prior_kts, archetype,
            risk_score, risk_level_str, momentum,
            redemption_risk, data_completeness,
        ),
    }

    # Populate main_risk_factors / protective_factors (backward compatible)
    labels = {
        "attendance_pct": "Attendance",
        "internal_avg_pct": "Internal exam performance",
        "assignment_health_pct": "Assignment completion/performance",
        "practical_avg_pct": "Practical/lab performance",
        "self_assessment_risk": "Student self-assessment",
    }
    for key, risk_val in risk_inputs.items():
        if risk_val is None:
            factors["missing_data"].append(labels.get(key, key))
            continue
        rounded = round(risk_val, 1)
        if rounded >= 55:
            factors["main_risk_factors"].append({
                "factor": labels.get(key, key),
                "risk_contribution": rounded,
                "message": f"{labels.get(key, key)} is currently increasing KT risk.",
            })
        elif rounded <= 25:
            factors["protective_factors"].append({
                "factor": labels.get(key, key),
                "risk_contribution": rounded,
                "message": f"{labels.get(key, key)} is helping reduce KT risk.",
            })

    # Prior KT factor (with redemption context)
    if prior_kts > 0:
        full_kt_risk = round(_clamp(float(prior_kts) * 30.0), 1)
        adjusted = round(redemption_risk, 1)
        if adjusted < full_kt_risk * 0.6:
            factors["protective_factors"].append({
                "factor": "KT history (redeemed)",
                "risk_contribution": adjusted,
                "message": (
                    f"{prior_kts} prior KT(s) — but current performance has "
                    f"reduced this penalty from {full_kt_risk} to {adjusted}."
                ),
            })
        else:
            factors["main_risk_factors"].append({
                "factor": "Previous KT history",
                "risk_contribution": adjusted,
                "message": f"{prior_kts} prior KT(s) adding {adjusted} risk points.",
            })

    # Momentum as a factor
    if momentum > 5:
        factors["protective_factors"].append({
            "factor": "Positive momentum",
            "risk_contribution": round(-momentum, 1),
            "message": "Improving trends are actively reducing the risk score.",
        })
    elif momentum < -5:
        factors["main_risk_factors"].append({
            "factor": "Negative momentum",
            "risk_contribution": round(-momentum, 1),
            "message": "Declining trends are increasing the risk score.",
        })

    # Attendance threshold warning
    att = signals.get("attendance_pct")
    if att is not None and att < 65:
        factors["main_risk_factors"].append({
            "factor": "Attendance threshold",
            "risk_contribution": round(100 - att, 1),
            "message": "Attendance is below the safe zone — this needs immediate follow-up.",
        })

    # Step 8: Recommendations
    recommendations = _generate_recommendations(
        signals, trends, prior_kts, archetype, risk_level_str,
    )

    return {
        "risk_score": risk_score,
        "risk_level": risk_level_str,
        "confidence": conf,
        "data_completeness": data_completeness,
        "factors": factors,
        "recommendations": recommendations,
        "model_version": MODEL_VERSION,
    }
