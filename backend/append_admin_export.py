import sys
sys.path.append('.')
from app.services.email_service import send_risk_alert_email

code = '''
from fastapi.responses import StreamingResponse
import io
import csv

@router.get("/export/risk-report")
def export_risk_report(db: Session = Depends(get_db), _=Depends(admin_required)):
    # Simple risk report export
    assessments = db.query(models.RiskPrediction).all()
    # To keep it simple, just grab the latest prediction for each student/subject
    
    # Let's just output raw enrollments and their latest risk
    enrollments = db.query(models.Enrollment).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student Name", "Student Email", "Student ID", "Subject", "Risk Score", "Risk Level", "Archetype", "Confidence"])
    
    for e in enrollments:
        student = db.query(models.User).filter(models.User.id == e.student_id).first()
        subject = db.query(models.Subject).filter(models.Subject.id == e.subject_id).first()
        
        # Get latest risk
        risk = db.query(models.RiskPrediction).filter(
            models.RiskPrediction.student_id == e.student_id,
            models.RiskPrediction.subject_id == e.subject_id
        ).order_by(models.RiskPrediction.created_at.desc()).first()
        
        if risk:
            import json
            factors = json.loads(risk.factors_json) if risk.factors_json else {}
            archetype = factors.get("archetype", "Unknown")
            
            writer.writerow([
                student.name,
                student.email,
                student.student_id or "-",
                subject.name,
                round(risk.risk_score, 1),
                risk.risk_level,
                archetype,
                risk.confidence
            ])
        else:
            writer.writerow([
                student.name,
                student.email,
                student.student_id or "-",
                subject.name,
                "N/A", "N/A", "N/A", "N/A"
            ])
            
    output.seek(0)
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=risk_report.csv"
    return response
'''

with open('c:/Desktop/Smart AI for students/backend/app/routers/admin_router.py', 'a', encoding='utf-8') as f:
    f.write(code)
print('CSV export route added to admin_router.py')
