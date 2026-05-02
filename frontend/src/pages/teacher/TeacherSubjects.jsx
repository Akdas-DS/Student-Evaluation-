import { useState, useEffect } from 'react';
import Sidebar from '../../components/Sidebar';
import API from '../../api';

export default function TeacherSubjects() {
    const [fields, setFields] = useState([]);
    const [selectedField, setSelectedField] = useState('');
    const [selectedSem, setSelectedSem] = useState('');
    const [subjects, setSubjects] = useState([]);
    const [newName, setNewName] = useState('');
    const [newCode, setNewCode] = useState('');
    const [questionModal, setQuestionModal] = useState(null);
    const [qForm, setQForm] = useState({ text: '', category: 'programming', weight: 1.0 });

    useEffect(() => { API.get('/teacher/fields').then(r => setFields(r.data)); }, []);

    useEffect(() => {
        if (selectedSem) API.get(`/teacher/subjects/${selectedSem}`).then(r => setSubjects(r.data));
        else setSubjects([]);
    }, [selectedSem]);

    const semesters = fields.find(f => f.id === parseInt(selectedField))?.semesters || [];

    const addSubject = async () => {
        if (!newName.trim() || !selectedSem) return;
        await API.post('/teacher/subjects', { name: newName, code: newCode, semester_id: parseInt(selectedSem) });
        setNewName(''); setNewCode('');
        API.get(`/teacher/subjects/${selectedSem}`).then(r => setSubjects(r.data));
    };

    const addQuestion = async () => {
        if (!qForm.text.trim()) return;
        await API.post('/teacher/questions', {
            subject_id: questionModal.id, text: qForm.text, category: qForm.category,
            weight: parseFloat(qForm.weight), min_val: 0, max_val: 10, order_index: questionModal.questions?.length || 0,
        });
        setQForm({ text: '', category: 'programming', weight: 1.0 });
        API.get(`/teacher/subjects/${selectedSem}`).then(r => { setSubjects(r.data); setQuestionModal(r.data.find(s => s.id === questionModal.id)); });
    };

    const deleteQuestion = async (qId) => {
        await API.delete(`/teacher/questions/${qId}`);
        API.get(`/teacher/subjects/${selectedSem}`).then(r => { setSubjects(r.data); setQuestionModal(r.data.find(s => s.id === questionModal.id)); });
    };

    return (
        <div className="page-container">
            <Sidebar role="teacher" />
            <div className="main-content">
                <div className="page-header">
                    <h1>📚 Manage Subjects & Questions</h1>
                    <p>Add subjects and configure assessment questions for your courses</p>
                </div>

                <div className="grid grid-2" style={{ marginBottom: 24 }}>
                    <div className="input-group">
                        <label>Select Field</label>
                        <select className="input-field" value={selectedField} onChange={e => { setSelectedField(e.target.value); setSelectedSem(''); }}>
                            <option value="">-- Choose Field --</option>
                            {fields.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
                        </select>
                    </div>
                    <div className="input-group">
                        <label>Select Semester</label>
                        <select className="input-field" value={selectedSem} onChange={e => setSelectedSem(e.target.value)}>
                            <option value="">-- Choose Semester --</option>
                            {semesters.sort((a, b) => a.number - b.number).map(s => <option key={s.id} value={s.id}>Semester {s.number}</option>)}
                        </select>
                    </div>
                </div>

                {selectedSem && (
                    <div className="glass-card card-3d" style={{ padding: 24, marginBottom: 24 }}>
                        <h3 style={{ marginBottom: 16 }}>➕ Add Subject</h3>
                        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                            <input className="input-field" placeholder="Subject Name" value={newName} onChange={e => setNewName(e.target.value)} style={{ flex: 2, minWidth: 200 }} />
                            <input className="input-field" placeholder="Code" value={newCode} onChange={e => setNewCode(e.target.value)} style={{ flex: 1, minWidth: 100 }} />
                            <button className="btn btn-primary" onClick={addSubject}>Add</button>
                        </div>
                    </div>
                )}

                {subjects.map(s => (
                    <div key={s.id} className="glass-card fade-in" style={{ padding: 20, marginBottom: 16 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <span style={{ fontWeight: 700, fontSize: '1.05rem' }}>{s.name}</span>
                                {s.code && <span className="tag" style={{ marginLeft: 10 }}>{s.code}</span>}
                            </div>
                            <button className="btn btn-outline btn-sm" onClick={() => setQuestionModal(s)}>❓ Questions ({s.questions?.length || 0})</button>
                        </div>
                    </div>
                ))}

                {questionModal && (
                    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && setQuestionModal(null)}>
                        <div className="modal-content glass-card">
                            <button className="modal-close" onClick={() => setQuestionModal(null)}>✕</button>
                            <h2>❓ Questions for {questionModal.name}</h2>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 20 }}>
                                <input className="input-field" placeholder="Question text..." value={qForm.text} onChange={e => setQForm({ ...qForm, text: e.target.value })} />
                                <div style={{ display: 'flex', gap: 10 }}>
                                    <select className="input-field" value={qForm.category} onChange={e => setQForm({ ...qForm, category: e.target.value })} style={{ flex: 1 }}>
                                        {['programming', 'theory', 'mathematics', 'practical'].map(c => <option key={c} value={c}>{c}</option>)}
                                    </select>
                                    <input className="input-field" type="number" placeholder="Weight" value={qForm.weight} onChange={e => setQForm({ ...qForm, weight: e.target.value })} style={{ width: 80 }} step="0.1" />
                                </div>
                                <button className="btn btn-primary btn-sm" onClick={addQuestion}>Add Question</button>
                            </div>

                            {questionModal.questions?.map((q, i) => (
                                <div key={q.id} style={{ padding: '10px 0', borderBottom: '1px solid var(--border-glass)', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10 }}>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ fontSize: '0.9rem', marginBottom: 4 }}><strong>{i + 1}.</strong> {q.text}</div>
                                        <div style={{ display: 'flex', gap: 8 }}><span className="tag">{q.category}</span><span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>weight: {q.weight}</span></div>
                                    </div>
                                    <button className="btn btn-danger btn-sm btn-icon" onClick={() => deleteQuestion(q.id)}>✕</button>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
