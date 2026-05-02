import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../../components/Sidebar';
import API from '../../api';

export default function History() {
    const [assessments, setAssessments] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        API.get('/student/history').then(r => setAssessments(r.data)).catch(() => { }).finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="page-container"><Sidebar role="student" /><div className="main-content"><div className="loading-spinner"><div className="spinner" /></div></div></div>;

    return (
        <div className="page-container">
            <Sidebar role="student" />
            <div className="main-content">
                <div className="page-header">
                    <h1>📋 Assessment History</h1>
                    <p>View your past K.T. risk predictions and recommendations</p>
                </div>

                {assessments.length === 0 ? (
                    <div className="glass-card">
                        <div className="empty-state">
                            <div className="icon">📋</div>
                            <h3>No assessments yet</h3>
                            <p>Take your first assessment from the dashboard!</p>
                            <button className="btn btn-primary" onClick={() => navigate('/student')} style={{ marginTop: 16 }}>Go to Dashboard</button>
                        </div>
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                        {assessments.map((a, i) => (
                            <div key={a.id} className={`glass-card card-3d fade-in stagger-${(i % 4) + 1}`}
                                style={{ padding: 24, cursor: 'pointer' }}
                                onClick={() => navigate(`/student/results/${a.id}`, { state: { result: a } })}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
                                    <div>
                                        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 4 }}>{a.subject_name}</h3>
                                        <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                                            {a.created_at ? new Date(a.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}
                                        </div>
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                                        <div style={{ textAlign: 'right' }}>
                                            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: a.risk_level === 'High' ? 'var(--accent-red)' : a.risk_level === 'Medium' ? 'var(--accent-orange)' : 'var(--accent-green)' }}>
                                                {a.risk_score}%
                                            </div>
                                        </div>
                                        <span className={`risk-badge risk-${a.risk_level.toLowerCase()}`}>{a.risk_level}</span>
                                        <span style={{ color: 'var(--accent-blue)', fontSize: '0.85rem', fontWeight: 500 }}>View →</span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
