import { useState, useEffect } from 'react';
import Sidebar from '../../components/Sidebar';
import API from '../../api';

function firstReason(row) {
    const factors = row.factors?.main_risk_factors || [];
    return factors[0]?.message || 'No major risk factor detected yet.';
}

export default function TeacherDashboard() {
    const [students, setStudents] = useState([]);
    const [subjects, setSubjects] = useState([]);
    const [interventions, setInterventions] = useState([]);
    const [selectedSubject, setSelectedSubject] = useState('');
    const [selectedStudent, setSelectedStudent] = useState('');
    const [recordType, setRecordType] = useState('attendance');
    const [recordForm, setRecordForm] = useState({
        attended_classes: '',
        total_classes: '',
        title: '',
        exam_name: 'Internal 1',
        score: '',
        max_score: '20',
        submitted: true,
    });
    const [formMessage, setFormMessage] = useState('');
    const [entryMode, setEntryMode] = useState('manual');
    const [csvFile, setCsvFile] = useState(null);
    const [bulkMessage, setBulkMessage] = useState('');
    const [loading, setLoading] = useState(true);

    const loadData = () => {
        Promise.all([
            API.get('/teacher/students').then(r => setStudents(r.data)),
            API.get('/teacher/assigned-subjects').then(r => setSubjects(r.data)).catch(() => { }),
            API.get('/teacher/interventions').then(r => setInterventions(r.data)).catch(() => { }),
        ]).catch(() => { }).finally(() => setLoading(false));
    };

    useEffect(() => {
        loadData();
    }, []);

    if (loading) {
        return <div className="page-container"><Sidebar role="teacher" /><div className="main-content"><div className="loading-spinner"><div className="spinner" /></div></div></div>;
    }

    const highRisk = students.filter(s => s.risk_level === 'High').length;
    const medRisk = students.filter(s => s.risk_level === 'Medium').length;
    const lowRisk = students.filter(s => s.risk_level === 'Low').length;
    const openInterventions = interventions.filter(i => i.status !== 'completed' && i.status !== 'cancelled').length;
    const subjectOptions = subjects.length > 0
        ? subjects
        : Array.from(new Map(students.map(s => [s.subject_id, { id: s.subject_id, name: s.subject_name }])).values());
    const studentOptions = students.filter(s => !selectedSubject || s.subject_id === parseInt(selectedSubject));

    const setRecord = (key, value) => setRecordForm({ ...recordForm, [key]: value });

    const submitRecord = async (e) => {
        e.preventDefault();
        setFormMessage('');
        if (!selectedSubject || !selectedStudent) {
            setFormMessage('Choose a subject and student first.');
            return;
        }

        const base = { subject_id: parseInt(selectedSubject), student_id: parseInt(selectedStudent) };
        const scorePayload = {
            ...base,
            score: parseFloat(recordForm.score),
            max_score: parseFloat(recordForm.max_score),
            notes: null,
        };

        try {
            if (recordType === 'attendance') {
                await API.post('/teacher/performance/attendance', {
                    ...base,
                    attended_classes: parseInt(recordForm.attended_classes),
                    total_classes: parseInt(recordForm.total_classes),
                });
            } else if (recordType === 'assignment') {
                await API.post('/teacher/performance/assignments', {
                    ...base,
                    title: recordForm.title || 'Assignment',
                    submitted: recordForm.submitted,
                    score: recordForm.submitted ? parseFloat(recordForm.score) : null,
                    max_score: parseFloat(recordForm.max_score),
                });
            } else if (recordType === 'internal') {
                await API.post('/teacher/performance/internals', {
                    ...scorePayload,
                    exam_name: recordForm.exam_name || 'Internal',
                });
            } else {
                await API.post('/teacher/performance/practicals', {
                    ...scorePayload,
                    title: recordForm.title || 'Practical',
                });
            }
            setFormMessage('Record saved and risk refreshed.');
            setRecordForm({ attended_classes: '', total_classes: '', title: '', exam_name: 'Internal 1', score: '', max_score: '20', submitted: true });
            loadData();
        } catch (err) {
            setFormMessage(err.response?.data?.detail || 'Could not save record.');
        }
    };

    const submitBulk = async (e) => {
        e.preventDefault();
        setBulkMessage('');
        if (!selectedSubject) return setBulkMessage('Choose a subject first.');
        if (!csvFile) return setBulkMessage('Please select a CSV file to upload.');

        const formData = new FormData();
        formData.append('subject_id', selectedSubject);
        formData.append('record_type', recordType);
        formData.append('file', csvFile);

        if (recordType === 'attendance') {
            formData.append('total_classes', recordForm.total_classes);
        } else {
            formData.append('max_score', recordForm.max_score);
            if (recordType === 'internal') formData.append('exam_name', recordForm.exam_name);
            if (recordType === 'assignment' || recordType === 'practical') formData.append('title', recordForm.title);
        }

        try {
            const res = await API.post('/teacher/performance/bulk-import', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setBulkMessage(res.data.message);
            if (res.data.success_count > 0) {
                loadData();
            }
        } catch (err) {
            setBulkMessage(err.response?.data?.detail || 'Bulk upload failed.');
        }
    };

    return (
        <div className="page-container">
            <Sidebar role="teacher" />
            <div className="main-content">
                <div className="page-header">
                    <h1>Teacher Dashboard</h1>
                    <p>Monitor student risk, reasons, and follow-up work for your assigned subjects.</p>
                </div>

                <div className="grid grid-4" style={{ marginBottom: 32 }}>
                    {[
                        { value: students.length, label: 'Students Monitored', color: '#3b82f6' },
                        { value: highRisk, label: 'High Risk', color: '#ef4444' },
                        { value: medRisk, label: 'Medium Risk', color: '#f59e0b' },
                        { value: openInterventions, label: 'Open Interventions', color: '#06b6d4' },
                    ].map((stat, i) => (
                        <div key={i} className="glass-card card-3d stat-card fade-in">
                            <div className="stat-value" style={{ color: stat.color }}>{stat.value}</div>
                            <div className="stat-label">{stat.label}</div>
                        </div>
                    ))}
                </div>

                <div className="glass-card fade-in" style={{ padding: 24, marginBottom: 24 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                        <h3 style={{ margin: 0 }}>Record Academic Evidence</h3>
                        <div style={{ display: 'flex', gap: 10 }}>
                            <button className={`btn ${entryMode === 'manual' ? 'btn-primary' : 'btn-outline'}`} onClick={() => setEntryMode('manual')} style={{ padding: '6px 12px', fontSize: '0.85rem' }}>Manual Entry</button>
                            <button className={`btn ${entryMode === 'bulk' ? 'btn-primary' : 'btn-outline'}`} onClick={() => setEntryMode('bulk')} style={{ padding: '6px 12px', fontSize: '0.85rem' }}>Bulk CSV Import</button>
                        </div>
                    </div>
                    
                    <div className="grid grid-3" style={{ marginBottom: 20 }}>
                        <div className="input-group">
                            <label>Subject</label>
                            <select className="input-field" value={selectedSubject} onChange={e => { setSelectedSubject(e.target.value); setSelectedStudent(''); }}>
                                <option value="">-- Select subject --</option>
                                {subjectOptions.map(subject => <option key={subject.id} value={subject.id}>{subject.name}</option>)}
                            </select>
                        </div>
                        <div className="input-group">
                            <label>Record Type</label>
                            <select className="input-field" value={recordType} onChange={e => setRecordType(e.target.value)}>
                                <option value="attendance">Attendance</option>
                                <option value="internal">Internal Exam</option>
                                <option value="assignment">Assignment</option>
                                <option value="practical">Practical/Lab</option>
                            </select>
                        </div>
                        {entryMode === 'manual' && (
                            <div className="input-group">
                                <label>Student</label>
                                <select className="input-field" value={selectedStudent} onChange={e => setSelectedStudent(e.target.value)} disabled={!selectedSubject}>
                                    <option value="">-- Select student --</option>
                                    {studentOptions.map(student => (
                                        <option key={`${student.student_id}-${student.subject_id}`} value={student.student_id}>
                                            {student.student_name} - {student.subject_name}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        )}
                    </div>

                    {entryMode === 'manual' ? (
                        <form onSubmit={submitRecord} className="auth-form">
                            {recordType === 'attendance' ? (
                                <div className="grid grid-2">
                                    <div className="input-group">
                                        <label>Attended Classes</label>
                                        <input className="input-field" type="number" min="0" value={recordForm.attended_classes} onChange={e => setRecord('attended_classes', e.target.value)} required />
                                    </div>
                                    <div className="input-group">
                                        <label>Total Classes</label>
                                        <input className="input-field" type="number" min="1" value={recordForm.total_classes} onChange={e => setRecord('total_classes', e.target.value)} required />
                                    </div>
                                </div>
                            ) : (
                                <div className="grid grid-4">
                                    {(recordType === 'assignment' || recordType === 'practical') && (
                                        <div className="input-group">
                                            <label>Title</label>
                                            <input className="input-field" value={recordForm.title} onChange={e => setRecord('title', e.target.value)} placeholder={recordType === 'assignment' ? 'Assignment 1' : 'Lab 1'} />
                                        </div>
                                    )}
                                    {recordType === 'internal' && (
                                        <div className="input-group">
                                            <label>Exam Name</label>
                                            <input className="input-field" value={recordForm.exam_name} onChange={e => setRecord('exam_name', e.target.value)} />
                                        </div>
                                    )}
                                    {recordType === 'assignment' && (
                                        <div className="input-group">
                                            <label>Submitted</label>
                                            <select className="input-field" value={recordForm.submitted ? 'yes' : 'no'} onChange={e => setRecord('submitted', e.target.value === 'yes')}>
                                                <option value="yes">Yes</option>
                                                <option value="no">No</option>
                                            </select>
                                        </div>
                                    )}
                                    <div className="input-group">
                                        <label>Score</label>
                                        <input className="input-field" type="number" min="0" step="0.1" value={recordForm.score} onChange={e => setRecord('score', e.target.value)} disabled={recordType === 'assignment' && !recordForm.submitted} required={recordType !== 'assignment' || recordForm.submitted} />
                                    </div>
                                    <div className="input-group">
                                        <label>Max Score</label>
                                        <input className="input-field" type="number" min="1" step="0.1" value={recordForm.max_score} onChange={e => setRecord('max_score', e.target.value)} required />
                                    </div>
                                </div>
                            )}

                            {formMessage && <div className="info-banner" style={{ marginTop: 16 }}>{formMessage}</div>}
                            <button className="btn btn-primary" type="submit" style={{ marginTop: 16 }}>Save Record</button>
                        </form>
                    ) : (
                        <form onSubmit={submitBulk} className="auth-form" style={{ background: 'rgba(0,0,0,0.1)', padding: 20, borderRadius: 12 }}>
                            <div className="grid grid-3">
                                {recordType === 'attendance' ? (
                                    <div className="input-group">
                                        <label>Total Classes (for all students)</label>
                                        <input className="input-field" type="number" min="1" value={recordForm.total_classes} onChange={e => setRecord('total_classes', e.target.value)} required />
                                    </div>
                                ) : (
                                    <>
                                        <div className="input-group">
                                            <label>{recordType === 'internal' ? 'Exam Name' : 'Title'}</label>
                                            <input className="input-field" value={recordType === 'internal' ? recordForm.exam_name : recordForm.title} onChange={e => setRecord(recordType === 'internal' ? 'exam_name' : 'title', e.target.value)} required />
                                        </div>
                                        <div className="input-group">
                                            <label>Max Score</label>
                                            <input className="input-field" type="number" min="1" step="0.1" value={recordForm.max_score} onChange={e => setRecord('max_score', e.target.value)} required />
                                        </div>
                                    </>
                                )}
                                <div className="input-group" style={{ gridColumn: 'span 3' }}>
                                    <label>Upload CSV File</label>
                                    <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                                        <input type="file" accept=".csv" className="input-field" onChange={e => setCsvFile(e.target.files[0])} required style={{ padding: '8px' }} />
                                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                            <strong>Required columns:</strong><br/>
                                            student_id, {recordType === 'attendance' ? 'attended_classes' : 'score'}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            {bulkMessage && <div className="info-banner" style={{ marginTop: 16 }}>{bulkMessage}</div>}
                            <button className="btn btn-primary" type="submit" style={{ marginTop: 16 }}>Upload Bulk Data</button>
                        </form>
                    )}
                </div>

                <div className="glass-card fade-in" style={{ padding: 24 }}>
                    <h3 style={{ marginBottom: 16 }}>Student Risk Overview</h3>
                    {students.length === 0 ? (
                        <div className="empty-state">
                            <h3>No enrolled students yet</h3>
                            <p>Ask the admin to enroll students and assign you to subjects.</p>
                        </div>
                    ) : (
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Student</th>
                                    <th>Subject</th>
                                    <th>Risk</th>
                                    <th>Pattern</th>
                                    <th>Confidence</th>
                                    <th style={{ minWidth: 300 }}>Mentor Insight</th>
                                </tr>
                            </thead>
                            <tbody>
                                {students.map((s, i) => {
                                    const narrative = s.factors?.narrative || [];
                                    const archLabel = s.factors?.archetype_label || '';
                                    const momLabel = s.factors?.momentum_label || 'Stable';
                                    const momColor = momLabel.includes('mproving') ? '#22c55e' : momLabel.includes('eclin') || momLabel.includes('ropping') ? '#ef4444' : 'var(--text-muted)';
                                    const momArrow = momLabel.includes('mproving') ? '↑' : momLabel.includes('eclin') || momLabel.includes('ropping') ? '↓' : '→';
                                    return (
                                    <tr key={`${s.student_id}-${s.subject_id}-${i}`}>
                                        <td>
                                            <div style={{ fontWeight: 600 }}>{s.student_name}</div>
                                            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{s.student_email}</div>
                                        </td>
                                        <td>{s.subject_name}</td>
                                        <td>
                                            <div style={{ fontWeight: 800 }}>{s.risk_score}%</div>
                                            <span className={`risk-badge risk-${s.risk_level.toLowerCase()}`}>{s.risk_level}</span>
                                        </td>
                                        <td>
                                            {archLabel && <div style={{ fontSize: '0.78rem', fontWeight: 500, marginBottom: 4 }}>{archLabel}</div>}
                                            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: momColor }}>{momArrow} {momLabel}</div>
                                        </td>
                                        <td>
                                            <div>{s.confidence || 'Low'}</div>
                                            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{s.data_completeness || 0}% data</div>
                                        </td>
                                        <td style={{ maxWidth: 400, color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: 1.5 }}>
                                            {narrative.length > 0 ? narrative[0] : firstReason(s)}
                                        </td>
                                    </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    )}
                </div>

                {lowRisk + medRisk + highRisk > 0 && (
                    <div className="glass-card fade-in" style={{ padding: 24, marginTop: 24 }}>
                        <h3 style={{ marginBottom: 12 }}>How To Use This</h3>
                        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                            High-risk students should get a specific intervention: recovery assignment, remedial test,
                            attendance follow-up, or lab revision. The goal is to reduce the risk before final exams,
                            not just label the student.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
