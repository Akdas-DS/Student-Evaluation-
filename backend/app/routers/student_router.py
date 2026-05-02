from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json
from app.database import get_db
from app import models, schemas, auth
from app.ml.predictor import predict_risk
from app.ml.recommender import generate_recommendations
from app.services.risk_service import ensure_enrollment, compute_and_store_risk, serialize_prediction

router = APIRouter(prefix="/api/student", tags=["Student"])


def student_required(current_user: models.User = Depends(auth.require_role("student"))):
    return current_user


@router.get("/fields", response_model=List[schemas.FieldWithSemesters])
def list_available_fields(db: Session = Depends(get_db), _=Depends(student_required)):
    fields = db.query(models.Field).filter(models.Field.is_active == True).all()
    result = []
    for f in fields:
        semesters = [schemas.SemesterOut.model_validate(s) for s in f.semesters]
        result.append(schemas.FieldWithSemesters(
            id=f.id, name=f.name, description=f.description,
            is_active=f.is_active, semesters=semesters
        ))
    return result


@router.get("/subjects/{semester_id}", response_model=List[schemas.SubjectOut])
def get_semester_subjects(semester_id: int, db: Session = Depends(get_db), _=Depends(student_required)):
    return db.query(models.Subject).filter(models.Subject.semester_id == semester_id).all()


@router.get("/questions/{subject_id}", response_model=List[schemas.QuestionOut])
def get_subject_questions(subject_id: int, db: Session = Depends(get_db), _=Depends(student_required)):
    questions = (
        db.query(models.Question)
        .filter(models.Question.subject_id == subject_id)
        .order_by(models.Question.order_index)
        .all()
    )
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for this subject")
    return questions


@router.post("/assess", response_model=schemas.AssessmentOut)
def submit_assessment(data: schemas.AssessmentSubmit, db: Session = Depends(get_db), user=Depends(student_required)):
    subject = db.query(models.Subject).filter(models.Subject.id == data.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Build answer map with question metadata
    answer_data = []
    for ans in data.answers:
        question = (
            db.query(models.Question)
            .filter(models.Question.id == ans.question_id, models.Question.subject_id == data.subject_id)
            .first()
        )
        if not question:
            raise HTTPException(status_code=400, detail=f"Question {ans.question_id} does not belong to this subject")
        if ans.answer_value < question.min_val or ans.answer_value > question.max_val:
            raise HTTPException(status_code=400, detail=f"Answer for question {ans.question_id} is out of range")
        answer_data.append({
            "question_id": question.id,
            "text": question.text,
            "category": question.category,
            "weight": question.weight,
            "max_val": question.max_val,
            "min_val": question.min_val,
            "value": ans.answer_value,
        })

    # Run ML prediction
    risk_score, risk_level, factors = predict_risk(answer_data)

    # Generate recommendations
    recommendations = generate_recommendations(answer_data, subject.name, factors)

    # Save assessment
    assessment = models.Assessment(
        student_id=user.id,
        subject_id=data.subject_id,
        risk_score=risk_score,
        risk_level=risk_level,
        factors_json=json.dumps(factors),
        recommendation_json=json.dumps(recommendations),
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    # Save individual answers
    for ans in data.answers:
        db_answer = models.AssessmentAnswer(
            assessment_id=assessment.id,
            question_id=ans.question_id,
            answer_value=ans.answer_value,
        )
        db.add(db_answer)
    ensure_enrollment(db, user.id, data.subject_id)
    compute_and_store_risk(db, user.id, data.subject_id)
    db.commit()

    return schemas.AssessmentOut(
        id=assessment.id,
        subject_id=assessment.subject_id,
        risk_score=round(risk_score, 1),
        risk_level=risk_level,
        factors=factors,
        recommendations=recommendations,
        subject_name=subject.name,
        created_at=assessment.created_at,
    )


@router.get("/history", response_model=List[schemas.AssessmentOut])
def get_history(db: Session = Depends(get_db), user=Depends(student_required)):
    assessments = (
        db.query(models.Assessment)
        .filter(models.Assessment.student_id == user.id)
        .order_by(models.Assessment.created_at.desc())
        .all()
    )
    result = []
    for a in assessments:
        factors = json.loads(a.factors_json) if a.factors_json else {}
        recommendations = json.loads(a.recommendation_json) if a.recommendation_json else {}
        result.append(schemas.AssessmentOut(
            id=a.id,
            subject_id=a.subject_id,
            risk_score=round(a.risk_score, 1),
            risk_level=a.risk_level,
            factors=factors,
            recommendations=recommendations,
            subject_name=a.subject.name,
            created_at=a.created_at,
        ))
    return result


@router.get("/profile")
def get_profile(db: Session = Depends(get_db), user=Depends(student_required)):
    assessment_count = db.query(models.Assessment).filter(models.Assessment.student_id == user.id).count()
    latest = (
        db.query(models.Assessment)
        .filter(models.Assessment.student_id == user.id)
        .order_by(models.Assessment.created_at.desc())
        .first()
    )
    return {
        "user": schemas.UserOut.model_validate(user),
        "total_assessments": assessment_count,
        "latest_risk_score": round(latest.risk_score, 1) if latest else None,
        "latest_risk_level": latest.risk_level if latest else None,
        "field_name": user.field.name if user.field else None,
    }


@router.get("/risk", response_model=List[schemas.RiskPredictionOut])
def get_my_risk(db: Session = Depends(get_db), user=Depends(student_required)):
    enrollments = (
        db.query(models.Enrollment)
        .filter(models.Enrollment.student_id == user.id, models.Enrollment.status == "active")
        .all()
    )
    return [serialize_prediction(db, user.id, e.subject_id) for e in enrollments]


@router.get("/risk/{subject_id}", response_model=schemas.RiskPredictionOut)
def get_my_subject_risk(subject_id: int, db: Session = Depends(get_db), user=Depends(student_required)):
    enrollment = (
        db.query(models.Enrollment)
        .filter(models.Enrollment.student_id == user.id, models.Enrollment.subject_id == subject_id)
        .first()
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="You are not enrolled in this subject yet")
    return serialize_prediction(db, user.id, subject_id)


@router.get("/interventions", response_model=List[schemas.InterventionOut])
def get_my_interventions(db: Session = Depends(get_db), user=Depends(student_required)):
    return (
        db.query(models.Intervention)
        .filter(models.Intervention.student_id == user.id)
        .order_by(models.Intervention.created_at.desc())
        .all()
    )
