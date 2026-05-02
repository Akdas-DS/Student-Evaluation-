import { useLocation, useNavigate } from 'react-router-dom';

export default function Results() {
    const { state } = useLocation();
    const navigate = useNavigate();
    const result = state?.result;

    if (!result) {
        return (
            <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 16 }}>
                <p>No results to display.</p>
                <button className="btn btn-primary" onClick={() => navigate('/student')}>Go to Dashboard</button>
            </div>
        );
    }

    const { risk_score, risk_level, factors, recommendations, subject_name } = result;
    const riskColor = risk_level === 'High' ? '#ef4444' : risk_level === 'Medium' ? '#f59e0b' : '#10b981';

    // SVG gauge path
    const angle = (risk_score / 100) * 180;
    const rad = (angle - 90) * (Math.PI / 180);
    const x = 100 + 80 * Math.cos(rad);
    const y = 100 + 80 * Math.sin(rad);
    const largeArc = angle > 90 ? 1 : 0;

    return (
        <div style={{ minHeight: '100vh', padding: 32, maxWidth: 900, margin: '0 auto' }}>
            <button className="btn btn-outline btn-sm" onClick={() => navigate('/student')} style={{ marginBottom: 24 }}>← Back to Dashboard</button>

            <div className="glass-card card-3d fade-in" style={{ padding: 40, textAlign: 'center', marginBottom: 32 }}>
                <h2 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: 8 }}>
                    📊 K.T. Risk Report — {subject_name}
                </h2>

                <div className="gauge-container">
                    <svg width="220" height="130" viewBox="0 0 200 120" className="gauge-svg">
                        <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="12" strokeLinecap="round" />
                        {risk_score > 0 && (
                            <path d={`M 20 100 A 80 80 0 ${largeArc} 1 ${x} ${y}`}
                                fill="none" stroke={riskColor} strokeWidth="12" strokeLinecap="round"
                                style={{ transition: 'all 1s ease' }} />
                        )}
                        <text x="100" y="85" textAnchor="middle" fill={riskColor} fontSize="28" fontWeight="800">{risk_score}%</text>
                        <text x="100" y="105" textAnchor="middle" fill="rgba(255,255,255,0.5)" fontSize="11">{risk_level} Risk</text>
                    </svg>
                </div>

                <span className={`risk-badge risk-${risk_level.toLowerCase()}`} style={{ fontSize: '1rem', padding: '8px 24px' }}>
                    {risk_level === 'High' ? '⚠️' : risk_level === 'Medium' ? '⚡' : '✅'} {risk_level} Risk Level
                </span>
            </div>

            {/* Factor Analysis */}
            {factors?.category_analysis && (
                <div className="result-section fade-in">
                    <h2>🔍 Factor Analysis</h2>
                    <div className="grid grid-2">
                        {Object.entries(factors.category_analysis).map(([cat, data]) => (
                            <div key={cat} className="glass-card recommendation-card">
                                <h3 style={{ textTransform: 'capitalize' }}>📂 {cat}</h3>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8 }}>
                                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Performance Score</span>
                                    <span style={{ fontWeight: 700, color: data.avg_score_pct >= 60 ? 'var(--accent-green)' : data.avg_score_pct >= 40 ? 'var(--accent-orange)' : 'var(--accent-red)' }}>
                                        {data.avg_score_pct}%
                                    </span>
                                </div>
                                <div style={{ width: '100%', height: 6, background: 'rgba(255,255,255,0.08)', borderRadius: 3, marginTop: 8, overflow: 'hidden' }}>
                                    <div style={{
                                        width: `${data.avg_score_pct}%`, height: '100%', borderRadius: 3,
                                        background: data.avg_score_pct >= 60 ? 'var(--gradient-success)' : data.avg_score_pct >= 40 ? 'var(--gradient-warning)' : 'var(--gradient-danger)',
                                        transition: 'width 1s ease'
                                    }} />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Weak Areas */}
            {factors?.weak_areas?.length > 0 && (
                <div className="result-section fade-in">
                    <h2>⚠️ Areas Needing Improvement</h2>
                    {factors.weak_areas.map((w, i) => (
                        <div key={i} className="glass-card recommendation-card">
                            <h3>🔴 {w.category} — {w.score_pct}%</h3>
                            <p>{w.concern}</p>
                        </div>
                    ))}
                </div>
            )}

            {/* Recommendations */}
            {recommendations && (
                <div className="result-section fade-in">
                    <h2>💡 Personalized Recommendations</h2>

                    <div className="glass-card recommendation-card">
                        <h3>📋 Summary</h3>
                        <p>{recommendations.summary}</p>
                    </div>

                    {recommendations.study_plan && (
                        <div className="glass-card recommendation-card">
                            <h3>📅 Study Plan</h3>
                            <p><strong>Duration:</strong> {recommendations.study_plan.duration}</p>
                            <p><strong>Daily Hours:</strong> {recommendations.study_plan.daily_hours}</p>
                            {recommendations.study_plan.daily_routine && (
                                <ul style={{ marginTop: 12 }}>
                                    {recommendations.study_plan.daily_routine.map((item, i) => <li key={i}>{item}</li>)}
                                </ul>
                            )}
                        </div>
                    )}

                    {recommendations.priority_topics?.length > 0 && (
                        <div className="glass-card recommendation-card">
                            <h3>🎯 Priority Topics</h3>
                            <ul>
                                {recommendations.priority_topics.map((t, i) => (
                                    <li key={i} style={{ marginBottom: 8 }}>
                                        <span style={{ textTransform: 'capitalize', fontWeight: 600 }}>{t.topic}</span>
                                        <span style={{ marginLeft: 8 }} className={`risk-badge risk-${t.priority === 'Critical' ? 'high' : t.priority === 'High' ? 'medium' : 'low'}`}>
                                            {t.priority} Priority
                                        </span>
                                        <span style={{ marginLeft: 8, color: 'var(--text-muted)', fontSize: '0.85rem' }}>Current: {t.current_score}%</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {recommendations.strategies?.length > 0 && (
                        <div className="glass-card recommendation-card">
                            <h3>🧠 Study Strategies</h3>
                            <ul>
                                {recommendations.strategies.map((s, i) => <li key={i}>{s}</li>)}
                            </ul>
                        </div>
                    )}
                </div>
            )}

            <div style={{ textAlign: 'center', marginTop: 32, paddingBottom: 32 }}>
                <button className="btn btn-primary btn-lg" onClick={() => navigate('/student')}>🏠 Back to Dashboard</button>
            </div>
        </div>
    );
}
