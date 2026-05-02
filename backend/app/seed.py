"""
Database seed script.
Creates initial admin user, fields, semesters, subjects, and question templates.
"""
from app.database import SessionLocal, engine, Base
from app import models
from app.auth import hash_password


SEED_DATA = {
    "Computer Science": {
        "semesters": {
            1: [
                {
                    "name": "Programming Fundamentals", "code": "CS101",
                    "questions": [
                        {"text": "Rate your understanding of variables, data types, and operators", "category": "programming", "weight": 1.5},
                        {"text": "Rate your proficiency in loops and conditional statements", "category": "programming", "weight": 1.5},
                        {"text": "How confident are you with functions and recursion?", "category": "programming", "weight": 1.3},
                        {"text": "Rate your problem-solving and logical thinking ability", "category": "theory", "weight": 1.2},
                        {"text": "How regularly do you attend classes?", "category": "practical", "weight": 1.0},
                        {"text": "Rate your assignment completion rate", "category": "practical", "weight": 1.0},
                    ],
                },
                {
                    "name": "Mathematics I", "code": "MA101",
                    "questions": [
                        {"text": "Rate your understanding of calculus (limits, derivatives)", "category": "mathematics", "weight": 1.5},
                        {"text": "How confident are you with linear algebra?", "category": "mathematics", "weight": 1.3},
                        {"text": "Rate your ability to solve mathematical proofs", "category": "theory", "weight": 1.2},
                        {"text": "How regularly do you practice math problems?", "category": "practical", "weight": 1.0},
                        {"text": "Rate your class attendance", "category": "practical", "weight": 0.8},
                    ],
                },
            ],
            2: [
                {
                    "name": "Data Structures", "code": "CS201",
                    "questions": [
                        {"text": "Rate your understanding of arrays, linked lists, stacks, and queues", "category": "programming", "weight": 1.5},
                        {"text": "How confident are you with trees and graphs?", "category": "programming", "weight": 1.5},
                        {"text": "Rate your ability to analyze time/space complexity (Big-O)", "category": "theory", "weight": 1.4},
                        {"text": "How proficient are you in writing code for sorting/searching algorithms?", "category": "programming", "weight": 1.3},
                        {"text": "Rate your coding speed and debugging ability", "category": "practical", "weight": 1.0},
                        {"text": "How regularly do you practice coding problems?", "category": "practical", "weight": 1.1},
                    ],
                },
                {
                    "name": "Object-Oriented Programming", "code": "CS202",
                    "questions": [
                        {"text": "Rate your understanding of classes, objects, and inheritance", "category": "programming", "weight": 1.5},
                        {"text": "How confident are you with polymorphism and abstraction?", "category": "programming", "weight": 1.3},
                        {"text": "Rate your understanding of design patterns", "category": "theory", "weight": 1.2},
                        {"text": "How proficient are you in Java/C++/Python OOP syntax?", "category": "programming", "weight": 1.4},
                        {"text": "Rate your project/assignment completion", "category": "practical", "weight": 1.0},
                    ],
                },
            ],
            3: [
                {
                    "name": "Database Management Systems", "code": "CS301",
                    "questions": [
                        {"text": "Rate your understanding of SQL queries (SELECT, JOIN, subqueries)", "category": "programming", "weight": 1.5},
                        {"text": "How confident are you with normalization and ER diagrams?", "category": "theory", "weight": 1.4},
                        {"text": "Rate your understanding of transaction management and ACID properties", "category": "theory", "weight": 1.3},
                        {"text": "How proficient are you with database design projects?", "category": "practical", "weight": 1.2},
                        {"text": "Rate your class attendance and lab participation", "category": "practical", "weight": 1.0},
                    ],
                },
                {
                    "name": "Operating Systems", "code": "CS302",
                    "questions": [
                        {"text": "Rate your understanding of process management and scheduling", "category": "theory", "weight": 1.5},
                        {"text": "How confident are you with memory management concepts?", "category": "theory", "weight": 1.4},
                        {"text": "Rate your understanding of file systems and I/O", "category": "theory", "weight": 1.2},
                        {"text": "How proficient are you with Linux/Unix commands?", "category": "practical", "weight": 1.3},
                        {"text": "Rate your lab exercise completion", "category": "practical", "weight": 1.0},
                    ],
                },
            ],
            4: [
                {
                    "name": "Machine Learning", "code": "CS401",
                    "questions": [
                        {"text": "Rate your Python proficiency", "category": "programming", "weight": 1.5},
                        {"text": "How confident are you with NumPy, Pandas, and Scikit-learn?", "category": "programming", "weight": 1.5},
                        {"text": "Rate your understanding of statistics and probability", "category": "mathematics", "weight": 1.4},
                        {"text": "How well do you understand supervised vs unsupervised learning?", "category": "theory", "weight": 1.3},
                        {"text": "Rate your linear algebra knowledge (matrices, eigenvalues)", "category": "mathematics", "weight": 1.2},
                        {"text": "How regularly do you practice ML implementations?", "category": "practical", "weight": 1.1},
                        {"text": "Rate your previous programming grades", "category": "practical", "weight": 1.0},
                    ],
                },
                {
                    "name": "Cloud Computing", "code": "CS402",
                    "questions": [
                        {"text": "Rate your understanding of virtualization concepts", "category": "theory", "weight": 1.4},
                        {"text": "How confident are you with Linux and networking basics?", "category": "practical", "weight": 1.5},
                        {"text": "Rate your understanding of cloud service models (IaaS, PaaS, SaaS)", "category": "theory", "weight": 1.3},
                        {"text": "How proficient are you with cloud platforms (AWS/Azure/GCP)?", "category": "practical", "weight": 1.2},
                        {"text": "Rate your understanding of containerization (Docker/Kubernetes)", "category": "practical", "weight": 1.1},
                    ],
                },
            ],
        },
    },
    "Data Science": {
        "semesters": {
            1: [
                {
                    "name": "Statistics for Data Science", "code": "DS101",
                    "questions": [
                        {"text": "Rate your understanding of descriptive statistics", "category": "mathematics", "weight": 1.5},
                        {"text": "How confident are you with probability distributions?", "category": "mathematics", "weight": 1.4},
                        {"text": "Rate your understanding of hypothesis testing", "category": "theory", "weight": 1.3},
                        {"text": "How proficient are you with statistical software (R/Python)?", "category": "programming", "weight": 1.2},
                        {"text": "Rate your class attendance and participation", "category": "practical", "weight": 1.0},
                    ],
                },
                {
                    "name": "Python for Data Analysis", "code": "DS102",
                    "questions": [
                        {"text": "Rate your Python programming proficiency", "category": "programming", "weight": 1.5},
                        {"text": "How confident are you with Pandas and data manipulation?", "category": "programming", "weight": 1.5},
                        {"text": "Rate your data visualization skills (Matplotlib/Seaborn)", "category": "programming", "weight": 1.3},
                        {"text": "How regularly do you practice data analysis projects?", "category": "practical", "weight": 1.1},
                        {"text": "Rate your assignment completion rate", "category": "practical", "weight": 1.0},
                    ],
                },
            ],
            2: [
                {
                    "name": "Machine Learning Foundations", "code": "DS201",
                    "questions": [
                        {"text": "Rate your understanding of regression algorithms", "category": "theory", "weight": 1.5},
                        {"text": "How confident are you with classification techniques?", "category": "theory", "weight": 1.4},
                        {"text": "Rate your understanding of model evaluation metrics", "category": "theory", "weight": 1.3},
                        {"text": "How proficient are you with Scikit-learn?", "category": "programming", "weight": 1.4},
                        {"text": "Rate your linear algebra and calculus foundation", "category": "mathematics", "weight": 1.2},
                        {"text": "How regularly do you implement ML algorithms from scratch?", "category": "practical", "weight": 1.1},
                    ],
                },
            ],
        },
    },
    "Information Technology": {
        "semesters": {
            1: [
                {
                    "name": "Web Technologies", "code": "IT101",
                    "questions": [
                        {"text": "Rate your HTML/CSS proficiency", "category": "programming", "weight": 1.5},
                        {"text": "How confident are you with JavaScript?", "category": "programming", "weight": 1.5},
                        {"text": "Rate your understanding of responsive design", "category": "theory", "weight": 1.2},
                        {"text": "How proficient are you with frontend frameworks (React/Angular)?", "category": "programming", "weight": 1.3},
                        {"text": "Rate your project completion rate", "category": "practical", "weight": 1.0},
                    ],
                },
                {
                    "name": "Networking Fundamentals", "code": "IT102",
                    "questions": [
                        {"text": "Rate your understanding of OSI/TCP-IP models", "category": "theory", "weight": 1.5},
                        {"text": "How confident are you with IP addressing and subnetting?", "category": "theory", "weight": 1.4},
                        {"text": "Rate your knowledge of network protocols", "category": "theory", "weight": 1.3},
                        {"text": "How proficient are you with networking tools (Wireshark, ping, traceroute)?", "category": "practical", "weight": 1.2},
                        {"text": "Rate your lab exercise completion", "category": "practical", "weight": 1.0},
                    ],
                },
            ],
        },
    },
    "Commerce": {
        "semesters": {
            1: [
                {
                    "name": "Financial Accounting", "code": "COM101",
                    "questions": [
                        {"text": "Rate your understanding of double-entry bookkeeping", "category": "theory", "weight": 1.5},
                        {"text": "How confident are you with journal entries and ledger posting?", "category": "practical", "weight": 1.4},
                        {"text": "Rate your understanding of financial statements", "category": "theory", "weight": 1.3},
                        {"text": "How proficient are you with accounting software (Tally)?", "category": "practical", "weight": 1.1},
                        {"text": "Rate your class attendance", "category": "practical", "weight": 1.0},
                    ],
                },
                {
                    "name": "Business Economics", "code": "COM102",
                    "questions": [
                        {"text": "Rate your understanding of demand and supply concepts", "category": "theory", "weight": 1.5},
                        {"text": "How confident are you with market structures?", "category": "theory", "weight": 1.3},
                        {"text": "Rate your understanding of national income accounting", "category": "theory", "weight": 1.2},
                        {"text": "How regularly do you read case studies?", "category": "practical", "weight": 1.0},
                        {"text": "Rate your assignment submission rate", "category": "practical", "weight": 1.0},
                    ],
                },
            ],
            2: [
                {
                    "name": "Cost Accounting", "code": "COM201",
                    "questions": [
                        {"text": "Rate your understanding of cost classification and behavior", "category": "theory", "weight": 1.5},
                        {"text": "How confident are you with budgeting and variance analysis?", "category": "theory", "weight": 1.4},
                        {"text": "Rate your ability to solve cost accounting problems", "category": "practical", "weight": 1.3},
                        {"text": "How regularly do you practice numerical problems?", "category": "practical", "weight": 1.1},
                        {"text": "Rate your attendance and participation", "category": "practical", "weight": 1.0},
                    ],
                },
            ],
        },
    },
}


def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(models.User).filter(models.User.role == "admin").first():
            print("[Seed] Database already seeded, skipping.")
            return

        # Create default admin
        admin = models.User(
            name="System Admin",
            email="admin@university.edu",
            password_hash=hash_password("admin123"),
            role="admin",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"[Seed] Created admin user: admin@university.edu / admin123")

        # Create default teacher
        teacher = models.User(
            name="Prof. Sharma",
            email="teacher@university.edu",
            password_hash=hash_password("teacher123"),
            role="teacher",
        )
        db.add(teacher)
        db.commit()
        print(f"[Seed] Created teacher user: teacher@university.edu / teacher123")

        # Seed fields, semesters, subjects, questions
        for field_name, field_data in SEED_DATA.items():
            field = models.Field(name=field_name, description=f"Department of {field_name}")
            db.add(field)
            db.commit()
            db.refresh(field)
            print(f"[Seed] Created field: {field_name}")

            for sem_num, subjects in field_data["semesters"].items():
                semester = models.Semester(number=sem_num, field_id=field.id)
                db.add(semester)
                db.commit()
                db.refresh(semester)

                for subj_data in subjects:
                    subject = models.Subject(
                        name=subj_data["name"],
                        code=subj_data["code"],
                        semester_id=semester.id,
                        created_by=admin.id,
                    )
                    db.add(subject)
                    db.commit()
                    db.refresh(subject)

                    for i, q_data in enumerate(subj_data["questions"]):
                        question = models.Question(
                            subject_id=subject.id,
                            text=q_data["text"],
                            category=q_data["category"],
                            weight=q_data["weight"],
                            min_val=0,
                            max_val=10,
                            order_index=i,
                        )
                        db.add(question)

                    db.commit()
                    print(f"  [Seed] {field_name} > Sem {sem_num} > {subj_data['name']} ({len(subj_data['questions'])} questions)")

        print("[Seed] Database seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"[Seed] Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
