import { useState, useEffect } from 'react';
import Sidebar from '../../components/Sidebar';
import API from '../../api';

export default function ManageFields() {
    const [fields, setFields] = useState([]);
    const [newField, setNewField] = useState('');
    const [newDesc, setNewDesc] = useState('');
    const [newSemField, setNewSemField] = useState('');
    const [newSemNum, setNewSemNum] = useState(1);
    const [loading, setLoading] = useState(true);

    const load = () => { API.get('/admin/fields').then(r => setFields(r.data)).catch(() => { }).finally(() => setLoading(false)); };
    useEffect(load, []);

    const addField = async () => {
        if (!newField.trim()) return;
        await API.post('/admin/fields', { name: newField, description: newDesc });
        setNewField(''); setNewDesc(''); load();
    };

    const deleteField = async (id) => { if (confirm('Delete this field and all its semesters/subjects?')) { await API.delete(`/admin/fields/${id}`); load(); } };

    const addSemester = async () => {
        if (!newSemField) return;
        await API.post('/admin/semesters', { field_id: parseInt(newSemField), number: parseInt(newSemNum) });
        setNewSemNum(1); load();
    };

    const deleteSemester = async (id) => { if (confirm('Delete this semester?')) { await API.delete(`/admin/semesters/${id}`); load(); } };

    if (loading) return <div className="page-container"><Sidebar role="admin" /><div className="main-content"><div className="loading-spinner"><div className="spinner" /></div></div></div>;

    return (
        <div className="page-container">
            <Sidebar role="admin" />
            <div className="main-content">
                <div className="page-header">
                    <h1>🏛️ Manage Academic Fields</h1>
                    <p>Create and manage fields of study and their semesters</p>
                </div>

                <div className="grid grid-2" style={{ marginBottom: 32 }}>
                    <div className="glass-card card-3d" style={{ padding: 24 }}>
                        <h3 style={{ marginBottom: 16 }}>➕ Add New Field</h3>
                        <div className="auth-form">
                            <div className="input-group">
                                <label>Field Name</label>
                                <input className="input-field" placeholder="e.g. Computer Science" value={newField} onChange={e => setNewField(e.target.value)} />
                            </div>
                            <div className="input-group">
                                <label>Description</label>
                                <input className="input-field" placeholder="Department of..." value={newDesc} onChange={e => setNewDesc(e.target.value)} />
                            </div>
                            <button className="btn btn-primary" onClick={addField}>Add Field</button>
                        </div>
                    </div>

                    <div className="glass-card card-3d" style={{ padding: 24 }}>
                        <h3 style={{ marginBottom: 16 }}>📅 Add Semester to Field</h3>
                        <div className="auth-form">
                            <div className="input-group">
                                <label>Select Field</label>
                                <select className="input-field" value={newSemField} onChange={e => setNewSemField(e.target.value)}>
                                    <option value="">-- Select --</option>
                                    {fields.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
                                </select>
                            </div>
                            <div className="input-group">
                                <label>Semester Number</label>
                                <select className="input-field" value={newSemNum} onChange={e => setNewSemNum(e.target.value)}>
                                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(n => <option key={n} value={n}>Semester {n}</option>)}
                                </select>
                            </div>
                            <button className="btn btn-primary" onClick={addSemester}>Add Semester</button>
                        </div>
                    </div>
                </div>

                <div className="glass-card fade-in" style={{ padding: 24 }}>
                    <h3 style={{ marginBottom: 16 }}>📋 All Fields & Semesters</h3>
                    {fields.length === 0 ? (
                        <div className="empty-state"><div className="icon">🏛️</div><h3>No fields yet</h3><p>Add your first academic field above</p></div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                            {fields.map(f => (
                                <div key={f.id} className="glass-card" style={{ padding: 20 }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                                        <div>
                                            <span style={{ fontSize: '1.1rem', fontWeight: 700 }}>{f.name}</span>
                                            {f.description && <span style={{ color: 'var(--text-muted)', marginLeft: 8, fontSize: '0.85rem' }}>— {f.description}</span>}
                                        </div>
                                        <button className="btn btn-danger btn-sm" onClick={() => deleteField(f.id)}>🗑️ Delete</button>
                                    </div>
                                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                                        {f.semesters?.sort((a, b) => a.number - b.number).map(s => (
                                            <span key={s.id} className="tag" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '4px 12px' }}>
                                                Sem {s.number}
                                                <button onClick={() => deleteSemester(s.id)} style={{ background: 'none', border: 'none', color: 'var(--accent-red)', cursor: 'pointer', fontSize: '0.7rem' }}>✕</button>
                                            </span>
                                        ))}
                                        {(!f.semesters || f.semesters.length === 0) && <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>No semesters added yet</span>}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
