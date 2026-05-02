# 🎓 Student K.T. Risk Prediction & Adaptive Learning System

A full-stack university-grade system that predicts students' probability of getting a K.T. (Keep Term / backlog) and provides personalized learning recommendations.

## Features

- **3 Role-Based Portals** — Admin, Teacher, and Student with separate dashboards
- **ML-Powered Risk Prediction** — Hybrid weighted scoring engine with category analysis
- **Adaptive Assessment Flow** — Subject-specific questions with slider-based UI
- **Personalized Recommendations** — Study plans, priority topics, and resource suggestions
- **Analytics Dashboard** — Risk distribution charts, subject analytics, high-risk student alerts
- **3D Glassmorphism UI** — Modern dark theme with animated card effects

## Tech Stack

| Layer      | Technology                            |
|------------|---------------------------------------|
| Frontend   | React 18 + Vite, Recharts, Axios     |
| Backend    | Python FastAPI, SQLAlchemy ORM        |
| Database   | SQLite (upgradeable to PostgreSQL)    |
| ML Engine  | NumPy + hybrid rule-based predictor   |
| Auth       | JWT (python-jose) + bcrypt            |

## Quick Start

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

The database is auto-created and seeded with sample data on first run.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

### Demo Credentials

| Role    | Email                    | Password    |
|---------|--------------------------|-------------|
| Admin   | admin@university.edu     | admin123    |
| Teacher | teacher@university.edu   | teacher123  |
| Student | (create via signup)      | —           |

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entry point
│   │   ├── config.py         # Environment config
│   │   ├── database.py       # SQLAlchemy setup
│   │   ├── models.py         # ORM models (7 tables)
│   │   ├── schemas.py        # Pydantic schemas
│   │   ├── auth.py           # JWT auth + RBAC
│   │   ├── seed.py           # Sample data seeder
│   │   ├── routers/
│   │   │   ├── auth_router.py
│   │   │   ├── admin_router.py
│   │   │   ├── teacher_router.py
│   │   │   └── student_router.py
│   │   └── ml/
│   │       ├── predictor.py   # K.T. risk prediction engine
│   │       └── recommender.py # Learning recommendation engine
│   ├── requirements.txt
│   └── .env
└── frontend/
    └── src/
        ├── App.jsx            # Router with role guards
        ├── api.js             # Axios + JWT interceptor
        ├── index.css          # 3D glassmorphism design system
        ├── components/
        │   └── Sidebar.jsx
        └── pages/
            ├── Login.jsx
            ├── Signup.jsx
            ├── admin/         # Dashboard, Fields, Subjects, Users
            ├── teacher/       # Dashboard, Subjects & Questions
            └── student/       # Dashboard, Assessment, Results, History
```

## How It Works

### For University Officials (Admin)
1. Login → Admin Dashboard shows university-wide risk analytics
2. Create academic fields (CS, IT, Commerce, etc.)
3. Add semesters to each field
4. Add subjects with assessment questions
5. Monitor high-risk students and intervene

### For Teachers
1. Login → View student assessment results
2. Add subjects and configure questions for assessments
3. Monitor which students need help

### For Students
1. Signup with Student role → Dashboard
2. Select field → Semester → Subject
3. Answer adaptive assessment questions (slider-based)
4. Get instant K.T. risk prediction with factor analysis
5. Receive personalized study plan and resource recommendations

## Future Scalability

- **PostgreSQL migration** — Change `DATABASE_URL` in `.env`
- **Authentication** — Already implemented with JWT + role-based access
- **Docker** — Add Dockerfile for containerized deployment
- **Email notifications** — Alert high-risk students automatically
- **ML model training** — Add scikit-learn model training with historical data
- **Mobile app** — API-first design supports any client
