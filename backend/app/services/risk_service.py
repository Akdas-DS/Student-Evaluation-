import json
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app import models
from app.ml.adaptive_risk import calculate_adaptive_risk


def _percentage(score: Optional[float], max_score: Optional[float]) -> Optional[float]:
    if score is None or not max_score:
        return None
    return max(0.0, min(100.0, (float(score) / float(max_score)) * 100.0))


def _average(values):
    values = [v for v in values if v is not None]
    if not values:
        return None
    return sum(values) / len(values)


def _compute_trend(dated_values: List[Tuple]) -> Optional[float]:
    """
    Given a list of (date, value) pairs, compute trend as:
      average of newer half − average of older half.
    Positive means improving.
    """
    if len(dated_values) < 2:
        return None
    sorted_vals = sorted(dated_values, key=lambda x: x[0])
    mid = len(sorted_vals) // 2
    older = [v for _, v in sorted_vals[:mid]]
    newer = [v for _, v in sorted_vals[mid:]]
    older_avg = sum(older) / len(older) if older else 0
    newer_avg = sum(newer) / len(newer) if newer else 0
    return round(newer_avg - older_avg, 1)


def ensure_enrollment(db: Session, student_id: int, subject_id: int) -> models.Enrollment:
    enrollment = (
        db.query(models.Enrollment)
        .filter(models.Enrollment.student_id == student_id, models.Enrollment.subject_id == subject_id)
        .first()
    )
    if enrollment:
        return enrollment

    enrollment = models.Enrollment(student_id=student_id, subject_id=subject_id, status="active")
    db.add(enrollment)
    db.flush()
    return enrollment


def build_signals(db: Session, student_id: int, subject_id: int) -> Dict:
    """Current-state snapshot of all academic signals for a student+subject."""
    attendance_rows = (
        db.query(models.AttendanceRecord)
        .filter(models.AttendanceRecord.student_id == student_id, models.AttendanceRecord.subject_id == subject_id)
        .all()
    )
    total_classes = sum(row.total_classes for row in attendance_rows)
    attended_classes = sum(row.attended_classes for row in attendance_rows)
    attendance_pct = _percentage(attended_classes, total_classes) if total_classes else None

    internals = (
        db.query(models.InternalExamScore)
        .filter(models.InternalExamScore.student_id == student_id, models.InternalExamScore.subject_id == subject_id)
        .all()
    )
    internal_avg_pct = _average([_percentage(row.score, row.max_score) for row in internals])

    assignments = (
        db.query(models.AssignmentRecord)
        .filter(models.AssignmentRecord.student_id == student_id, models.AssignmentRecord.subject_id == subject_id)
        .all()
    )
    submitted_assignments = [row for row in assignments if row.submitted]
    assignment_completion_pct = _percentage(len(submitted_assignments), len(assignments)) if assignments else None
    assignment_avg_pct = _average([_percentage(row.score, row.max_score) for row in submitted_assignments])

    practicals = (
        db.query(models.PracticalScore)
        .filter(models.PracticalScore.student_id == student_id, models.PracticalScore.subject_id == subject_id)
        .all()
    )
    practical_avg_pct = _average([_percentage(row.score, row.max_score) for row in practicals])

    prior_kt_count = (
        db.query(models.FinalResult)
        .filter(models.FinalResult.student_id == student_id, models.FinalResult.got_kt == True)
        .count()
    )

    latest_assessment = (
        db.query(models.Assessment)
        .filter(models.Assessment.student_id == student_id, models.Assessment.subject_id == subject_id)
        .order_by(models.Assessment.created_at.desc())
        .first()
    )

    return {
        "attendance_pct": round(attendance_pct, 1) if attendance_pct is not None else None,
        "internal_avg_pct": round(internal_avg_pct, 1) if internal_avg_pct is not None else None,
        "assignment_avg_pct": round(assignment_avg_pct, 1) if assignment_avg_pct is not None else None,
        "assignment_completion_pct": round(assignment_completion_pct, 1) if assignment_completion_pct is not None else None,
        "practical_avg_pct": round(practical_avg_pct, 1) if practical_avg_pct is not None else None,
        "prior_kt_count": prior_kt_count,
        "self_assessment_risk": round(latest_assessment.risk_score, 1) if latest_assessment else None,
    }


def build_trend_signals(db: Session, student_id: int, subject_id: int) -> Dict:
    """
    Compute trends by splitting records chronologically into an older half
    and a newer half, then measuring the difference.
    Positive trend = student is improving.
    """
    total_records = 0

    # ── Attendance trend ──
    # Each attendance record has a running count; compute % per record
    att_rows = (
        db.query(models.AttendanceRecord)
        .filter(
            models.AttendanceRecord.student_id == student_id,
            models.AttendanceRecord.subject_id == subject_id,
        )
        .order_by(models.AttendanceRecord.recorded_at)
        .all()
    )
    att_dated = []
    for row in att_rows:
        if row.total_classes and row.total_classes > 0:
            pct = (row.attended_classes / row.total_classes) * 100.0
            att_dated.append((row.recorded_at, pct))
    total_records += len(att_dated)
    attendance_trend = _compute_trend(att_dated)

    # ── Internal exam trend ──
    int_rows = (
        db.query(models.InternalExamScore)
        .filter(
            models.InternalExamScore.student_id == student_id,
            models.InternalExamScore.subject_id == subject_id,
        )
        .order_by(models.InternalExamScore.recorded_at)
        .all()
    )
    int_dated = []
    for row in int_rows:
        pct = _percentage(row.score, row.max_score)
        if pct is not None:
            int_dated.append((row.recorded_at, pct))
    total_records += len(int_dated)
    internal_trend = _compute_trend(int_dated)

    # ── Assignment score trend ──
    asgn_rows = (
        db.query(models.AssignmentRecord)
        .filter(
            models.AssignmentRecord.student_id == student_id,
            models.AssignmentRecord.subject_id == subject_id,
            models.AssignmentRecord.submitted == True,
        )
        .order_by(models.AssignmentRecord.recorded_at)
        .all()
    )
    asgn_dated = []
    for row in asgn_rows:
        pct = _percentage(row.score, row.max_score)
        if pct is not None:
            asgn_dated.append((row.recorded_at, pct))
    total_records += len(asgn_dated)
    assignment_score_trend = _compute_trend(asgn_dated)

    # ── Practical trend ──
    prac_rows = (
        db.query(models.PracticalScore)
        .filter(
            models.PracticalScore.student_id == student_id,
            models.PracticalScore.subject_id == subject_id,
        )
        .order_by(models.PracticalScore.recorded_at)
        .all()
    )
    prac_dated = []
    for row in prac_rows:
        pct = _percentage(row.score, row.max_score)
        if pct is not None:
            prac_dated.append((row.recorded_at, pct))
    total_records += len(prac_dated)
    practical_trend = _compute_trend(prac_dated)

    # ── Self-assessment risk trend (lower risk = improving, so invert) ──
    sa_rows = (
        db.query(models.Assessment)
        .filter(
            models.Assessment.student_id == student_id,
            models.Assessment.subject_id == subject_id,
        )
        .order_by(models.Assessment.created_at)
        .all()
    )
    sa_dated = [(row.created_at, row.risk_score) for row in sa_rows]
    total_records += len(sa_dated)
    self_assessment_trend = _compute_trend(sa_dated)  # positive = risk going up (bad)

    return {
        "attendance_trend": attendance_trend,
        "internal_trend": internal_trend,
        "assignment_score_trend": assignment_score_trend,
        "practical_trend": practical_trend,
        "self_assessment_trend": self_assessment_trend,
        "total_records": total_records,
    }


def compute_risk(db: Session, student_id: int, subject_id: int) -> Dict:
    """Compute adaptive risk using current signals + trends."""
    signals = build_signals(db, student_id, subject_id)
    trends = build_trend_signals(db, student_id, subject_id)
    return calculate_adaptive_risk(signals, trends)


def compute_and_store_risk(db: Session, student_id: int, subject_id: int) -> models.RiskPrediction:
    risk = compute_risk(db, student_id, subject_id)
    
    # Check previous risk to see if it changed
    prev = db.query(models.RiskPrediction).filter(
        models.RiskPrediction.student_id == student_id,
        models.RiskPrediction.subject_id == subject_id
    ).order_by(models.RiskPrediction.created_at.desc()).first()
    
    prediction = models.RiskPrediction(
        student_id=student_id,
        subject_id=subject_id,
        risk_score=risk["risk_score"],
        risk_level=risk["risk_level"],
        confidence=risk["confidence"],
        data_completeness=risk["data_completeness"],
        factors_json=json.dumps(risk["factors"]),
        recommendations_json=json.dumps(risk["recommendations"]),
        model_version=risk["model_version"],
    )
    db.add(prediction)
    db.flush()
    
    if risk["risk_level"] == "High" and (not prev or prev.risk_level != "High"):
        from app.services.email_service import send_risk_alert_email
        student = db.query(models.User).filter(models.User.id == student_id).first()
        subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
        if student and subject:
            send_risk_alert_email(student.email, student.name, subject.name, "High")
            
    return prediction


def serialize_prediction(db: Session, student_id: int, subject_id: int) -> Dict:
    student = db.query(models.User).filter(models.User.id == student_id).first()
    subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    risk = compute_risk(db, student_id, subject_id)
    return {
        "student_id": student_id,
        "subject_id": subject_id,
        "student_name": student.name if student else None,
        "student_email": student.email if student else None,
        "subject_name": subject.name if subject else None,
        "risk_score": risk["risk_score"],
        "risk_level": risk["risk_level"],
        "confidence": risk["confidence"],
        "data_completeness": risk["data_completeness"],
        "factors": risk["factors"],
        "recommendations": risk["recommendations"],
        "created_at": None,
    }
