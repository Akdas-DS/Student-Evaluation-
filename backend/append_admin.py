code = '''

# ── Bulk Student Enrollment ──
@router.post("/enrollments/bulk")
async def bulk_enroll_students(
    subject_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(admin_required),
):
    subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded CSV")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="Empty CSV file")

    required = ["name", "email", "student_id"]
    for req in required:
        if req not in reader.fieldnames:
            raise HTTPException(status_code=400, detail=f"Missing required CSV column: {req}. Found: {', '.join(reader.fieldnames)}")

    success_count = 0
    errors = []

    for row_num, row in enumerate(reader, start=2):
        name = row.get("name", "").strip()
        email = row.get("email", "").strip()
        st_id = row.get("student_id", "").strip()

        if not email or not name or not st_id:
            errors.append(f"Row {row_num}: Missing name, email, or student_id")
            continue

        student = db.query(models.User).filter(models.User.email == email).first()
        if not student:
            if db.query(models.User).filter(models.User.student_id == st_id).first():
                errors.append(f"Row {row_num}: Student ID {st_id} is already in use")
                continue
                
            student = models.User(
                name=name,
                email=email,
                student_id=st_id,
                password_hash=auth.hash_password("student123"),
                role="student"
            )
            db.add(student)
            db.commit()
            db.refresh(student)
        
        existing = db.query(models.Enrollment).filter(
            models.Enrollment.student_id == student.id,
            models.Enrollment.subject_id == subject_id
        ).first()

        if not existing:
            db.add(models.Enrollment(student_id=student.id, subject_id=subject_id))
            success_count += 1
            
    db.commit()
    return {
        "success_count": success_count,
        "errors": errors,
        "message": f"Successfully enrolled/created {success_count} students. {len(errors)} errors found."
    }
'''

with open('c:/Desktop/Smart AI for students/backend/app/routers/admin_router.py', 'a', encoding='utf-8') as f:
    f.write(code)
print('Successfully appended to admin_router.py')
