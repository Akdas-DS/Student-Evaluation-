import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../../components/Sidebar';
import API from '../../api';

function riskReason(row) {
    const factors = row.factors?.main_risk_factors || [];
    return factors[0]?.message || 'No major risk factor detected yet.';
}

export default function StudentDashboard() {
    const [fields, setFields] = useState([]);
    const [selectedField, setSelectedField] = useState('');
    const [selectedSem, setSelectedSem] = useState('');
    const [subjects, setSubjects] = useState([]);
    const [profile, setProfile] = useState(null);
    const [riskRows, setRiskRows] = useState([]);
    const [interventions, setInterventions] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        Promise.all([
            API.get('/student/fields').then(r => setFields(r.data)),
            API.get('/student/profile').then(r => setProfile(r.data)),
            API.get('/student/risk').then(r => setRiskRows(r.data)).catch(() => { }),
            API.get('/student/interventions').then(r => setInterventions(r.data)).catch(() => { }),
        ]).catch(() => { }).finally(() => setLoading(false));
    }, []);

    useEffect(() => {
        if (selectedSem) API.get(`/student/subjects/${selectedSem}`).then(r => setSubjects(r.data));
        else setSubjects([]);
    }, [selectedSem]);

    const semesters = fields.find(f => f.id === parseInt(selectedField))?.semesters || [];
    const openInterventions = interventions.filter(i => i.status !== 'completed' && i.status !== 'cancelled');

    if (loading) {
        return <div className="page-container"><Sidebar role="student" /><div className="main-content"><div className="loading-spinner"><div className="spinner" /></div></div></div>;
    }

    return (
        <div className="page-container">
            <Sidebar role="student" />
            <div className="main-content">
                <div className="page-header">
                    <h1>Student Dashboard</h1>
                    <p>Welcome back, {profile?.user?.name}. Track your risk and what to improve next.</p>
                </div>

                {profile && (
                    <div className="glass-card card-3d fade-in" style={{ padding: 24, marginBottom: 32 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
                            <div>
                                <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: 4 }}>{profile.user.name}</h3>
                                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                                    {profile.user.email} {profile.user.student_id && ` - ${profile.user.student_id}`}
                                    {profile.field_name && ` - ${profile.field_name}`}
                                </p>
                            </div>
                            <div style={{ display: 'flex', gap: 20 }}>
                                <div style={{ textAlign: 'center' }}>
                                    <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-blue)' }}>{profile.total_assessments}</div>
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Assessments</div>
                                </div>
                                <div style={{ textAlign: 'center' }}>
                                    <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>{openInterventions.length}</div>
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Open Tasks</div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {riskRows.length > 0 && (
                    <div className="result-section fade-in">
                        <h2>Academic Risk Overview</h2>
                        <div className="grid grid-2">
                            {riskRows.map((row, i) => {
                                const narrative = row.factors?.narrative || [];
                                const archLabel = row.factors?.archetype_label || '';
                                const momLabel = row.factors?.momentum_label || '';
                                const trends = row.factors?.trends || {};
                                const trendEntries = Object.entries(trends).filter(([, v]) => v && v !== '');
                                return (
                                <div key={`${row.subject_id}-${i}`} className="glass-card recommendation-card">
                                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start' }}>
                                        <div>
                                            <h3>{row.subject_name}</h3>
                                            {archLabel && (
                                                <span className="tag" style={{ marginBottom: 8, display: 'inline-block', fontSize: '0.75rem' }}>
                                                    {archLabel}
                                                </span>
                                            )}
                                        </div>
                                        <div style={{ textAlign: 'right' }}>
                                            <div style={{ fontSize: '1.4rem', fontWeight: 800 }}>{row.risk_score}%</div>
                                            <span className={`risk-badge risk-${row.risk_level.toLowerCase()}`}>{row.risk_level}</span>
                                            {momLabel && (
                                                <div style={{
                                                    fontSize: '0.75rem', marginTop: 4, fontWeight: 600,
                                                    color: momLabel.includes('mproving') ? '#22c55e' : momLabel.includes('eclin') ? '#ef4444' : 'var(--text-muted)'
                                                }}>
                                                    {momLabel.includes('mproving') ? '↑' : momLabel.includes('eclin') || momLabel.includes('ropping') ? '↓' : '→'} {momLabel}
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {narrative.length > 0 && (
                                        <div style={{
                                            marginTop: 14, padding: '14px 16px',
                                            background: 'rgba(255,255,255,0.03)', borderRadius: 10,
                                            borderLeft: '3px solid var(--accent-blue)',
                                            fontSize: '0.88rem', lineHeight: 1.7, color: 'var(--text-secondary)',
                                        }}>
                                            {narrative.map((line, idx) => <p key={idx} style={{ marginBottom: idx < narrative.length - 1 ? 8 : 0 }}>{line}</p>)}
                                        </div>
                                    )}

                                    {trendEntries.length > 0 && (
                                        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 12 }}>
                                            {trendEntries.map(([key, val]) => (
                                                <span key={key} style={{
                                                    fontSize: '0.72rem', padding: '3px 10px', borderRadius: 20,
                                                    background: val.includes('improving') ? 'rgba(34,197,94,0.12)' : val.includes('declin') || val.includes('dropping') ? 'rgba(239,68,68,0.12)' : 'rgba(255,255,255,0.05)',
                                                    color: val.includes('improving') ? '#22c55e' : val.includes('declin') || val.includes('dropping') ? '#ef4444' : 'var(--text-muted)',
                                                    fontWeight: 500, textTransform: 'capitalize',
                                                }}>
                                                    {key}: {val}
                                                </span>
                                            ))}
                                        </div>
                                    )}

                                    <div style={{ marginTop: 10, color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                                        Confidence: {row.confidence} · Data completeness: {row.data_completeness}%
                                    </div>
                                    {row.recommendations?.student_actions?.length > 0 && (
                                        <ul style={{ marginTop: 12 }}>
                                            {row.recommendations.student_actions.slice(0, 3).map((action, idx) => <li key={idx}>{action}</li>)}
                                        </ul>
                                    )}
                                </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {openInterventions.length > 0 && (
                    <div className="result-section fade-in">
                        <h2>Teacher Assigned Improvement Work</h2>
                        {openInterventions.map(task => (
                            <div key={task.id} className="glass-card recommendation-card">
                                <h3>{task.title}</h3>
                                {task.description && <p>{task.description}</p>}
                                <span className="tag">{task.status}</span>
                            </div>
                        ))}
                    </div>
                )}

                <div className="glass-card fade-in" style={{ padding: 24, marginBottom: 24 }}>
                    <h3 style={{ marginBottom: 16 }}>Take a Self-Assessment</h3>
                    <p style={{ color: 'var(--text-secondary)', marginBottom: 20, fontSize: '0.9rem' }}>
                        Self-assessments are now one signal in the larger academic-risk model. Real attendance,
                        internal marks, assignments, and teacher interventions matter more.
                    </p>

                    <div className="grid grid-2" style={{ marginBottom: 24 }}>
                        <div className="input-group">
                            <label>Field of Study</label>
                            <select className="input-field" value={selectedField} onChange={e => { setSelectedField(e.target.value); setSelectedSem(''); setSubjects([]); }}>
                                <option value="">-- Choose your field --</option>
                                {fields.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
                            </select>
                        </div>
                        <div className="input-group">
                            <label>Semester</label>
                            <select className="input-field" value={selectedSem} onChange={e => setSelectedSem(e.target.value)} disabled={!selectedField}>
                                <option value="">-- Choose semester --</option>
                                {semesters.sort((a, b) => a.number - b.number).map(s => <option key={s.id} value={s.id}>Semester {s.number}</option>)}
                            </select>
                        </div>
                    </div>

                    {subjects.length > 0 && (
                        <div className="grid grid-2">
                            {subjects.map((s, i) => (
                                <div key={s.id} className={`glass-card card-3d fade-in stagger-${(i % 4) + 1}`}
                                    style={{ padding: 24, cursor: 'pointer' }}
                                    onClick={() => navigate(`/student/assess/${s.id}`)}>
                                    <h4 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: 4 }}>{s.name}</h4>
                                    {s.code && <span className="tag">{s.code}</span>}
                                    <p style={{ color: 'var(--accent-blue)', fontSize: '0.85rem', marginTop: 12, fontWeight: 500 }}>
                                        Start assessment
                                    </p>
                                </div>
                            ))}
                        </div>
                    )}

                    {selectedSem && subjects.length === 0 && (
                        <div className="empty-state">
                            <h3>No subjects available</h3>
                            <p>No subjects or questions have been configured for this semester yet.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
