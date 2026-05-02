from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.auth import hash_password

def fix_demo_students():
    db = SessionLocal()
    
    # Let's map old emails to new names, emails, and student IDs
    updates = {
        "comeback@university.edu": ("Student A", "studentA@university.edu", "STU001"),
        "slipping@university.edu": ("Student B", "studentB@university.edu", "STU002"),
        "struggling@university.edu": ("Student C", "studentC@university.edu", "STU003"),
        "rising@university.edu": ("Student D", "studentD@university.edu", "STU004"),
        "consistent@university.edu": ("Student E", "studentE@university.edu", "STU005"),
    }

    for old_email, (new_name, new_email, new_id) in updates.items():
        student = db.query(models.User).filter(models.User.email == old_email).first()
        if student:
            student.name = new_name
            student.email = new_email
            student.student_id = new_id
            student.password_hash = hash_password("student123")
    
    db.commit()
    print("Demo students renamed to Student A, Student B, etc.")
    db.close()

if __name__ == "__main__":
    fix_demo_students()
