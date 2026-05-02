import { useState, useEffect } from 'react';
import Sidebar from '../../components/Sidebar';
import API from '../../api';

export default function ManageUsers() {
    const [users, setUsers] = useState([]);
    const [subjects, setSubjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [accessMessage, setAccessMessage] = useState('');
    const [form, setForm] = useState({
        name: '',
        email: '',
        password: '',
        role: 'student',
        student_id: '',
        department: '',
        semester: 1,
    });
    const [teacherSubject, setTeacherSubject] = useState({ teacher_id: '', subject_id: '' });
    const [enrollment, setEnrollment] = useState({ student_id: '', subject_id: '' });
    const [enrollMode, setEnrollMode] = useState('manual');
    const [csvFile, setCsvFile] = useState(null);
    const [bulkSubject, setBulkSubject] = useState('');

    const load = () => {
        Promise.all([
            API.get('/admin/users').then(r => setUsers(r.data)),
            API.get('/admin/subjects').then(r => setSubjects(r.data)).catch(() => { }),
        ]).catch(() => { }).finally(() => setLoading(false));
    };
    useEffect(load, []);

    const set = (key, value) => setForm({ ...form, [key]: value });

    const createUser = async (e) => {
        e.preventDefault();
        setError('');
        try {
            const payload = {
                ...form,
                semester: form.role === 'student' ? parseInt(form.semester) : null,
            };
            if (form.role !== 'student') {
                payload.student_id = null;
                payload.department = null;
                payload.semester = null;
            }
            await API.post('/admin/users', payload);
            setForm({ name: '', email: '', password: '', role: 'student', student_id: '', department: '', semester: 1 });
            load();
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to create user');
        }
    };

    const deleteUser = async (id) => {
        if (confirm('Delete this user?')) {
            await API.delete(`/admin/users/${id}`);
            load();
        }
    };

    const assignTeacher = async (e) => {
        e.preventDefault();
        setAccessMessage('');
        try {
            await API.post('/admin/teacher-subjects', {
                teacher_id: parseInt(teacherSubject.teacher_id),
                subject_id: parseInt(teacherSubject.subject_id),
            });
            setTeacherSubject({ teacher_id: '', subject_id: '' });
            setAccessMessage('Teacher assigned to subject.');
        } catch (err) {
            setAccessMessage(err.response?.data?.detail || 'Could not assign teacher.');
        }
    };

    const enrollStudent = async (e) => {
        e.preventDefault();
        setAccessMessage('');
        try {
            await API.post('/admin/enrollments', {
                student_id: parseInt(enrollment.student_id),
                subject_id: parseInt(enrollment.subject_id),
                status: 'active',
            });
            setEnrollment({ student_id: '', subject_id: '' });
            setAccessMessage('Student enrolled in subject.');
        } catch (err) {
            setAccessMessage(err.response?.data?.detail || 'Could not enroll student.');
        }
    };

    const enrollBulk = async (e) => {
        e.preventDefault();
        setAccessMessage('');
        if (!bulkSubject) return setAccessMessage('Select a subject.');
        if (!csvFile) return setAccessMessage('Select a CSV file.');

        const formData = new FormData();
        formData.append('subject_id', bulkSubject);
        formData.append('file', csvFile);

        try {
            const res = await API.post('/admin/enrollments/bulk', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setAccessMessage(res.data.message);
            setCsvFile(null);
            if (res.data.success_count > 0) load();
        } catch (err) {
            setAccessMessage(err.response?.data?.detail || 'Bulk enrollment failed.');
        }
    };

    const roleColors = { admin: 'var(--accent-purple)', teacher: 'var(--accent-cyan)', student: 'var(--accent-green)' };
    const teachers = users.filter(u => u.role === 'teacher');
    const students = users.filter(u => u.role === 'student');

    if (loading) {
        return <div className="page-container"><Sidebar role="admin" /><div className="main-content"><div className="loading-spinner"><div className="spinner" /></div></div></div>;
    }

    return (
        <div className="page-container">
            <Sidebar role="admin" />
            <div className="main-content">
                <div className="page-header">
                    <h1>Manage Users</h1>
                    <p>Create approved admin, teacher, and student accounts.</p>
                </div>

                <div className="grid grid-3" style={{ marginBottom: 24 }}>
                    {['admin', 'teacher', 'student'].map(role => (
                        <div key={role} className="glass-card card-3d stat-card">
                            <div className="stat-value" style={{ color: roleColors[role] }}>{users.filter(u => u.role === role).length}</div>
                            <div className="stat-label">{role.charAt(0).toUpperCase() + role.slice(1)}s</div>
                        </div>
                    ))}
                </div>

                <div className="glass-card fade-in" style={{ padding: 24, marginBottom: 24 }}>
                    <h3 style={{ marginBottom: 16 }}>Create Approved User</h3>
                    {error && <div className="error-msg" style={{ marginBottom: 16 }}>{error}</div>}
                    <form onSubmit={createUser} className="auth-form">
                        <div className="grid grid-3">
                            <div className="input-group">
                                <label>Name</label>
                                <input className="input-field" value={form.name} onChange={e => set('name', e.target.value)} required />
                            </div>
                            <div className="input-group">
                                <label>Email</label>
                                <input className="input-field" type="email" value={form.email} onChange={e => set('email', e.target.value)} required />
                            </div>
                            <div className="input-group">
                                <label>Password</label>
                                <input className="input-field" type="password" value={form.password} onChange={e => set('password', e.target.value)} minLength={8} required />
                            </div>
                        </div>
                        <div className="grid grid-4">
                            <div className="input-group">
                                <label>Role</label>
                                <select className="input-field" value={form.role} onChange={e => set('role', e.target.value)}>
                                    <option value="student">Student</option>
                                    <option value="teacher">Teacher</option>
                                    <option value="admin">Admin</option>
                                </select>
                            </div>
                            {form.role === 'student' && (
                                <>
                                    <div className="input-group">
                                        <label>Student ID</label>
                                        <input className="input-field" value={form.student_id} onChange={e => set('student_id', e.target.value)} />
                                    </div>
                                    <div className="input-group">
                                        <label>Department</label>
                                        <input className="input-field" value={form.department} onChange={e => set('department', e.target.value)} />
                                    </div>
                                    <div className="input-group">
                                        <label>Semester</label>
                                        <select className="input-field" value={form.semester} onChange={e => set('semester', e.target.value)}>
                                            {[1, 2, 3, 4, 5, 6, 7, 8].map(n => <option key={n} value={n}>Semester {n}</option>)}
                                        </select>
                                    </div>
                                </>
                            )}
                        </div>
                        <button className="btn btn-primary" type="submit">Create User</button>
                    </form>
                </div>

                <div className="glass-card fade-in" style={{ padding: 24, marginBottom: 24 }}>
                    <h3 style={{ marginBottom: 16 }}>Subject Access & Enrollment</h3>
                    {accessMessage && <div className="info-banner">{accessMessage}</div>}
                    <div className="grid grid-2">
                        <form onSubmit={assignTeacher} className="auth-form">
                            <h4>Assign Teacher To Subject</h4>
                            <div className="input-group">
                                <label>Teacher</label>
                                <select className="input-field" value={teacherSubject.teacher_id} onChange={e => setTeacherSubject({ ...teacherSubject, teacher_id: e.target.value })} required>
                                    <option value="">-- Select teacher --</option>
                                    {teachers.map(t => <option key={t.id} value={t.id}>{t.name} - {t.email}</option>)}
                                </select>
                            </div>
                            <div className="input-group">
                                <label>Subject</label>
                                <select className="input-field" value={teacherSubject.subject_id} onChange={e => setTeacherSubject({ ...teacherSubject, subject_id: e.target.value })} required>
                                    <option value="">-- Select subject --</option>
                                    {subjects.map(s => <option key={s.id} value={s.id}>{s.name} {s.code ? `(${s.code})` : ''}</option>)}
                                </select>
                            </div>
                            <button className="btn btn-primary" type="submit">Assign Teacher</button>
                        </form>

                        <div className="auth-form" style={{ position: 'relative' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <h4>Enroll Student In Subject</h4>
                                <div style={{ display: 'flex', gap: 5 }}>
                                    <button className={`btn ${enrollMode === 'manual' ? 'btn-primary' : 'btn-outline'}`} onClick={() => setEnrollMode('manual')} style={{ padding: '4px 8px', fontSize: '0.75rem' }} type="button">Manual</button>
                                    <button className={`btn ${enrollMode === 'bulk' ? 'btn-primary' : 'btn-outline'}`} onClick={() => setEnrollMode('bulk')} style={{ padding: '4px 8px', fontSize: '0.75rem' }} type="button">Bulk CSV</button>
                                </div>
                            </div>
                            
                            {enrollMode === 'manual' ? (
                                <form onSubmit={enrollStudent}>
                                    <div className="input-group">
                                        <label>Student</label>
                                        <select className="input-field" value={enrollment.student_id} onChange={e => setEnrollment({ ...enrollment, student_id: e.target.value })} required>
                                            <option value="">-- Select student --</option>
                                            {students.map(s => <option key={s.id} value={s.id}>{s.name} - {s.email}</option>)}
                                        </select>
                                    </div>
                                    <div className="input-group">
                                        <label>Subject</label>
                                        <select className="input-field" value={enrollment.subject_id} onChange={e => setEnrollment({ ...enrollment, subject_id: e.target.value })} required>
                                            <option value="">-- Select subject --</option>
                                            {subjects.map(s => <option key={s.id} value={s.id}>{s.name} {s.code ? `(${s.code})` : ''}</option>)}
                                        </select>
                                    </div>
                                    <button className="btn btn-primary" type="submit" style={{ marginTop: 12 }}>Enroll Student</button>
                                </form>
                            ) : (
                                <form onSubmit={enrollBulk} style={{ background: 'rgba(0,0,0,0.1)', padding: 16, borderRadius: 8 }}>
                                    <div className="input-group">
                                        <label>Subject</label>
                                        <select className="input-field" value={bulkSubject} onChange={e => setBulkSubject(e.target.value)} required>
                                            <option value="">-- Select subject --</option>
                                            {subjects.map(s => <option key={s.id} value={s.id}>{s.name} {s.code ? `(${s.code})` : ''}</option>)}
                                        </select>
                                    </div>
                                    <div className="input-group">
                                        <label>Upload CSV File</label>
                                        <input type="file" accept=".csv" className="input-field" onChange={e => setCsvFile(e.target.files[0])} required style={{ padding: '6px' }} />
                                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4 }}>
                                            Req: <strong>name, email, student_id</strong>. Missing accounts will be auto-created.
                                        </div>
                                    </div>
                                    <button className="btn btn-primary" type="submit" style={{ marginTop: 12 }}>Upload & Enroll</button>
                                </form>
                            )}
                        </div>
                    </div>
                </div>

                <div className="glass-card fade-in" style={{ padding: 24 }}>
                    <table className="data-table">
                        <thead>
                            <tr><th>Name</th><th>Email</th><th>Role</th><th>Student ID</th><th>Department</th><th>Actions</th></tr>
                        </thead>
                        <tbody>
                            {users.map(u => (
                                <tr key={u.id}>
                                    <td style={{ fontWeight: 600 }}>{u.name}</td>
                                    <td style={{ color: 'var(--text-secondary)' }}>{u.email}</td>
                                    <td>
                                        <span style={{
                                            padding: '2px 10px', borderRadius: 12, fontSize: '0.8rem', fontWeight: 600,
                                            background: `${roleColors[u.role]}15`, color: roleColors[u.role]
                                        }}>
                                            {u.role}
                                        </span>
                                    </td>
                                    <td>{u.student_id || '-'}</td>
                                    <td>{u.department || '-'}</td>
                                    <td>
                                        <button className="btn btn-danger btn-sm" onClick={() => deleteUser(u.id)}>Delete</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
