from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.auth import hash_password
from datetime import datetime, timedelta, timezone

def populate_demo_data():
    db = SessionLocal()
    
    # 1. Ensure Teacher is assigned to a subject
    teacher = db.query(models.User).filter(models.User.email == "teacher@university.edu").first()
    if not teacher:
        print("Teacher not found!")
        return

    # Find "Programming Fundamentals" or any subject
    subject = db.query(models.Subject).filter(models.Subject.name == "Programming Fundamentals").first()
    if not subject:
        print("Subject not found!")
        return

    # Assign Teacher to Subject
    ts = db.query(models.TeacherSubject).filter_by(teacher_id=teacher.id, subject_id=subject.id).first()
    if not ts:
        db.add(models.TeacherSubject(teacher_id=teacher.id, subject_id=subject.id))
        db.commit()

    # 2. Create Students for the archetypes
    students_data = [
        ("Comeback Kid", "comeback@university.edu", "C101"),
        ("Slipping Star", "slipping@university.edu", "S102"),
        ("Struggling Student", "struggling@university.edu", "S103"),
        ("Rising Student", "rising@university.edu", "R104"),
        ("Consistent Performer", "consistent@university.edu", "C105"),
    ]

    for name, email, st_id in students_data:
        student = db.query(models.User).filter(models.User.email == email).first()
        if not student:
            student = models.User(
                name=name,
                email=email,
                password_hash=hash_password("student123"),
                role="student",
                student_id=st_id
            )
            db.add(student)
            db.commit()
            db.refresh(student)
        
        # Enroll them
        enr = db.query(models.Enrollment).filter_by(student_id=student.id, subject_id=subject.id).first()
        if not enr:
            db.add(models.Enrollment(student_id=student.id, subject_id=subject.id))
            db.commit()

    print("Demo data populated! Teacher now has subjects and students.")
    db.close()

if __name__ == "__main__":
    populate_demo_data()
