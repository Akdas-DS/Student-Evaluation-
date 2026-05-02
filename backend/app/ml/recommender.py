"""
Personalized Learning Recommendation Engine.
Generates study plans based on weak areas identified during assessment.
"""
from typing import List, Dict


RESOURCE_TEMPLATES = {
    "programming": {
        "videos": ["Programming fundamentals playlist", "Hands-on coding tutorials", "Problem-solving walkthrough videos"],
        "practice": ["LeetCode/HackerRank easy problems", "Mini project implementations", "Code review exercises"],
        "notes": ["Language syntax cheat sheets", "Data structure reference guides", "Algorithm pattern templates"],
    },
    "theory": {
        "videos": ["Concept explanation lectures", "Visual theory breakdowns", "Real-world application demos"],
        "practice": ["Previous year questions", "Concept mapping exercises", "Group discussion topics"],
        "notes": ["Summary notes with diagrams", "Mind maps for each chapter", "Key formula/definition sheets"],
    },
    "mathematics": {
        "videos": ["Step-by-step problem solving", "Mathematical proof walkthroughs", "Application-based tutorials"],
        "practice": ["Graded problem sets (easy→hard)", "Timed practice tests", "Formula derivation exercises"],
        "notes": ["Formula reference cards", "Solved example compilations", "Common mistake guides"],
    },
    "practical": {
        "videos": ["Lab demonstration recordings", "Tool/software tutorials", "Setup and configuration guides"],
        "practice": ["Lab exercise repetitions", "Simulated environments", "Peer lab sessions"],
        "notes": ["Step-by-step lab manuals", "Troubleshooting guides", "Quick-start references"],
    },
    "default": {
        "videos": ["Topic overview lectures", "Expert explanation sessions", "Interactive learning modules"],
        "practice": ["Practice question banks", "Self-assessment quizzes", "Peer study groups"],
        "notes": ["Chapter summaries", "Key concept flashcards", "Revision checklists"],
    },
}


def _get_resources(category: str) -> Dict:
    cat_lower = category.lower()
    for key in RESOURCE_TEMPLATES:
        if key in cat_lower:
            return RESOURCE_TEMPLATES[key]
    return RESOURCE_TEMPLATES["default"]


def generate_recommendations(answer_data: List[Dict], subject_name: str, factors: Dict) -> Dict:
    weak_areas = factors.get("weak_areas", [])
    category_analysis = factors.get("category_analysis", {})
    overall_performance = factors.get("overall_performance", 50)

    recommendations = {
        "subject": subject_name,
        "summary": "",
        "priority_topics": [],
        "study_plan": {},
        "strategies": [],
        "resources": {},
    }

    # Build priority topic list from weak areas
    sorted_categories = sorted(
        category_analysis.items(),
        key=lambda x: x[1]["avg_score_pct"]
    )

    for i, (cat, data) in enumerate(sorted_categories):
        score = data["avg_score_pct"]
        priority = "Critical" if score < 30 else "High" if score < 50 else "Medium" if score < 70 else "Low"
        if priority != "Low":
            recommendations["priority_topics"].append({
                "topic": cat,
                "current_score": score,
                "priority": priority,
                "order": i + 1,
            })

    # Generate study plan based on overall risk
    if overall_performance < 40:
        recommendations["summary"] = (
            f"Your preparation for {subject_name} needs significant improvement. "
            f"Focus on fundamentals before advancing to complex topics. "
            f"Allocate at least 2-3 hours daily for the next 4 weeks."
        )
        recommendations["study_plan"] = {
            "duration": "4-6 weeks intensive",
            "daily_hours": "2-3 hours",
            "week_1_2": "Master fundamentals — focus on weakest categories first",
            "week_3_4": "Practice problems and past papers for each weak topic",
            "week_5_6": "Full revision + timed mock tests",
            "daily_routine": [
                "30 min: Review previous day's concepts",
                "60 min: Study new topic from priority list",
                "30 min: Practice problems",
                "30 min: Self-quiz and note weak points",
            ],
        }
    elif overall_performance < 65:
        recommendations["summary"] = (
            f"You have a moderate grasp of {subject_name} but need targeted improvement. "
            f"Focus on your weak categories while maintaining strong areas."
        )
        recommendations["study_plan"] = {
            "duration": "2-3 weeks focused",
            "daily_hours": "1.5-2 hours",
            "week_1": "Address critical weak areas with focused study",
            "week_2": "Practice and application — solve problems for each topic",
            "week_3": "Revision and mock tests",
            "daily_routine": [
                "30 min: Quick revision of strong topics",
                "45 min: Deep study of weak topic",
                "30 min: Practice questions",
                "15 min: Self-assessment",
            ],
        }
    else:
        recommendations["summary"] = (
            f"You're well-prepared for {subject_name}. "
            f"Maintain consistency and focus on any remaining gaps."
        )
        recommendations["study_plan"] = {
            "duration": "1-2 weeks maintenance",
            "daily_hours": "1 hour",
            "week_1": "Review weak spots and practice advanced problems",
            "week_2": "Mock tests and final revision",
            "daily_routine": [
                "20 min: Review notes",
                "20 min: Solve challenging problems",
                "20 min: Quick self-test",
            ],
        }

    # Generate strategies based on weak categories
    strategies = []
    for weak in weak_areas:
        cat = weak["category"]
        score = weak["score_pct"]
        if score < 25:
            strategies.append(f"🔴 {cat}: Start from absolute basics. Use beginner-friendly resources and build up gradually.")
        elif score < 40:
            strategies.append(f"🟠 {cat}: Revisit core concepts. Practice with guided examples before attempting problems independently.")
        else:
            strategies.append(f"🟡 {cat}: Good foundation exists. Focus on practice and application to strengthen understanding.")

    if not strategies:
        strategies.append("✅ All areas look good! Focus on maintaining your preparation through regular practice.")

    recommendations["strategies"] = strategies

    # Attach resource recommendations per category
    for cat, data in category_analysis.items():
        if data["avg_score_pct"] < 70:
            recommendations["resources"][cat] = _get_resources(cat)

    return recommendations
