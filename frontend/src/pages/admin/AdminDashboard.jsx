import { useState, useEffect } from 'react';
import Sidebar from '../../components/Sidebar';
import API from '../../api';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const COLORS = ['#10b981', '#f59e0b', '#ef4444'];

export default function AdminDashboard() {
    const [analytics, setAnalytics] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        API.get('/admin/analytics').then(r => setAnalytics(r.data)).catch(() => { }).finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="page-container"><Sidebar role="admin" /><div className="main-content"><div className="loading-spinner"><div className="spinner" /></div></div></div>;

    const riskData = analytics ? [
        { name: 'Low Risk', value: analytics.risk_distribution.low },
        { name: 'Medium Risk', value: analytics.risk_distribution.medium },
        { name: 'High Risk', value: analytics.risk_distribution.high },
    ] : [];

    const subjectData = analytics?.subject_risks?.map(s => ({
        name: s.subject_name.length > 15 ? s.subject_name.slice(0, 15) + '…' : s.subject_name,
        risk: s.avg_risk,
        assessments: s.total_assessments,
    })) || [];

    return (
        <div className="page-container">
            <Sidebar role="admin" />
            <div className="main-content">
                <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1>📊 Admin Dashboard</h1>
                        <p>University-wide K.T. risk analytics overview</p>
                    </div>
                    <button 
                        className="btn btn-primary" 
                        onClick={() => window.open('http://localhost:8000/api/admin/export/risk-report', '_blank')}
                        style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                    >
                        <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                        Export CSV Report
                    </button>
                </div>

                <div className="grid grid-4" style={{ marginBottom: 32 }}>
                    {[
                        { icon: '🎓', value: analytics?.total_students || 0, label: 'Total Students', color: '#3b82f6' },
                        { icon: '📝', value: analytics?.total_assessments || 0, label: 'Assessments', color: '#8b5cf6' },
                        { icon: '⚠️', value: analytics?.risk_distribution?.high || 0, label: 'High Risk', color: '#ef4444' },
                        { icon: '✅', value: analytics?.risk_distribution?.low || 0, label: 'Low Risk', color: '#10b981' },
                    ].map((stat, i) => (
                        <div key={i} className={`glass-card card-3d stat-card fade-in stagger-${i + 1}`}>
                            <div className="stat-icon" style={{ background: `${stat.color}20`, color: stat.color }}>{stat.icon}</div>
                            <div className="stat-value" style={{ color: stat.color }}>{stat.value}</div>
                            <div className="stat-label">{stat.label}</div>
                        </div>
                    ))}
                </div>

                <div className="grid grid-2" style={{ marginBottom: 32 }}>
                    <div className="glass-card chart-card fade-in">
                        <h3>🎯 Risk Distribution</h3>
                        {riskData.some(d => d.value > 0) ? (
                            <ResponsiveContainer width="100%" height={280}>
                                <PieChart>
                                    <Pie data={riskData} cx="50%" cy="50%" innerRadius={60} outerRadius={100}
                                        paddingAngle={5} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                                        {riskData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
                                    </Pie>
                                    <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#f1f5f9' }} />
                                    <Legend />
                                </PieChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="empty-state"><div className="icon">📊</div><h3>No data yet</h3><p>Students need to take assessments first</p></div>
                        )}
                    </div>

                    <div className="glass-card chart-card fade-in">
                        <h3>📚 Subject-wise Average Risk Score</h3>
                        {subjectData.length > 0 ? (
                            <ResponsiveContainer width="100%" height={280}>
                                <BarChart data={subjectData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                    <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                                    <YAxis tick={{ fill: '#94a3b8' }} domain={[0, 100]} />
                                    <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#f1f5f9' }} />
                                    <Bar dataKey="risk" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="empty-state"><div className="icon">📚</div><h3>No subject data</h3></div>
                        )}
                    </div>
                </div>

                {analytics?.high_risk_students?.length > 0 && (
                    <div className="glass-card fade-in" style={{ padding: 24 }}>
                        <h3 style={{ marginBottom: 16 }}>🚨 High Risk Students</h3>
                        <table className="data-table">
                            <thead>
                                <tr><th>Student</th><th>Email</th><th>Subject</th><th>Risk Score</th><th>Level</th></tr>
                            </thead>
                            <tbody>
                                {analytics.high_risk_students.map((s, i) => (
                                    <tr key={i}>
                                        <td style={{ fontWeight: 600 }}>{s.student_name}</td>
                                        <td style={{ color: 'var(--text-secondary)' }}>{s.student_email}</td>
                                        <td>{s.subject_name}</td>
                                        <td style={{ fontWeight: 700 }}>{s.risk_score}%</td>
                                        <td><span className={`risk-badge risk-${s.risk_level.toLowerCase()}`}>{s.risk_level}</span></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}
