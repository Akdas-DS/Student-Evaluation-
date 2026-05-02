import sqlite3
import datetime

conn = sqlite3.connect('kt_risk.db')
c = conn.cursor()

c.execute("SELECT id FROM users WHERE role='teacher'")
teacher = c.fetchone()
if teacher:
    teacher_id = teacher[0]
    c.execute("SELECT id FROM subjects")
    subject_ids = [row[0] for row in c.fetchall()]

    now = str(datetime.datetime.now())
    count = 0
    for sid in subject_ids:
        c.execute("SELECT id FROM teacher_subjects WHERE teacher_id=? AND subject_id=?", (teacher_id, sid))
        if not c.fetchone():
            c.execute("INSERT INTO teacher_subjects (teacher_id, subject_id, created_at) VALUES (?, ?, ?)", (teacher_id, sid, now))
            count += 1

    conn.commit()
    print(f"Assigned teacher to {count} additional subjects.")
else:
    print("No teacher found.")
conn.close()
