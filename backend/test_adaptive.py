"""Quick test: run the adaptive engine with different student archetypes."""
from app.ml.adaptive_risk import calculate_adaptive_risk

def run(label, signals, trends):
    result = calculate_adaptive_risk(signals, trends)
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  Risk: {result['risk_score']}% ({result['risk_level']})")
    print(f"  Confidence: {result['confidence']}")
    print(f"  Archetype: {result['factors']['archetype_label']}")
    print(f"  Momentum: {result['factors']['momentum_label']}")
    print(f"  Redemption applied: {result['factors']['redemption_applied']}")
    print(f"\n  --- NARRATIVE ---")
    for line in result["factors"]["narrative"]:
        print(f"  {line}")
    print(f"\n  --- STUDENT ACTIONS ---")
    for a in result["recommendations"]["student_actions"]:
        print(f"    • {a}")
    print(f"\n  --- TEACHER ACTIONS ---")
    for a in result["recommendations"]["teacher_actions"]:
        print(f"    • {a}")


# Test 1: COMEBACK KID — Has 2 prior KTs but currently scoring well and improving
run("COMEBACK KID — Past KTs but improving now", {
    "attendance_pct": 78,
    "internal_avg_pct": 72,
    "assignment_avg_pct": 65,
    "assignment_completion_pct": 90,
    "practical_avg_pct": 60,
    "prior_kt_count": 2,
    "self_assessment_risk": 40,
}, {
    "attendance_trend": 5,
    "internal_trend": 18,
    "assignment_score_trend": 10,
    "practical_trend": 5,
    "self_assessment_trend": -8,
    "total_records": 14,
})

# Test 2: SLIPPING STAR — Was great but attendance and scores dropping
run("SLIPPING STAR — Was good, now declining", {
    "attendance_pct": 68,
    "internal_avg_pct": 62,
    "assignment_avg_pct": 70,
    "assignment_completion_pct": 75,
    "practical_avg_pct": 65,
    "prior_kt_count": 0,
    "self_assessment_risk": 35,
}, {
    "attendance_trend": -15,
    "internal_trend": -12,
    "assignment_score_trend": -5,
    "practical_trend": -3,
    "self_assessment_trend": 8,
    "total_records": 10,
})

# Test 3: STRUGGLING STUDENT — Poor across the board, no improvement
run("STRUGGLING STUDENT — Consistently weak", {
    "attendance_pct": 45,
    "internal_avg_pct": 28,
    "assignment_avg_pct": 30,
    "assignment_completion_pct": 50,
    "practical_avg_pct": 35,
    "prior_kt_count": 1,
    "self_assessment_risk": 70,
}, {
    "attendance_trend": -2,
    "internal_trend": -3,
    "assignment_score_trend": 0,
    "practical_trend": -1,
    "self_assessment_trend": 5,
    "total_records": 8,
})

# Test 4: NEW STUDENT — Almost no data
run("NEW STUDENT — Very little data", {
    "attendance_pct": None,
    "internal_avg_pct": None,
    "assignment_avg_pct": None,
    "assignment_completion_pct": None,
    "practical_avg_pct": None,
    "prior_kt_count": 0,
    "self_assessment_risk": 55,
}, {
    "attendance_trend": None,
    "internal_trend": None,
    "assignment_score_trend": None,
    "practical_trend": None,
    "self_assessment_trend": None,
    "total_records": 1,
})

# Test 5: RISING STUDENT — Low scores but clearly improving
run("RISING STUDENT — Low but improving fast", {
    "attendance_pct": 82,
    "internal_avg_pct": 38,
    "assignment_avg_pct": 42,
    "assignment_completion_pct": 85,
    "practical_avg_pct": 40,
    "prior_kt_count": 0,
    "self_assessment_risk": 55,
}, {
    "attendance_trend": 10,
    "internal_trend": 15,
    "assignment_score_trend": 12,
    "practical_trend": 8,
    "self_assessment_trend": -10,
    "total_records": 10,
})

print("\n" + "="*60)
print("  All tests complete!")
print("="*60)
