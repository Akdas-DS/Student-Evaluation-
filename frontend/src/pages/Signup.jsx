import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import API from '../api';

export default function Signup() {
    const [form, setForm] = useState({
        name: '',
        email: '',
        password: '',
        role: 'student',
        student_id: '',
        department: '',
        semester: 1,
        field_id: '',
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        const apiRoot = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api').replace('/api', '');
        fetch(`${apiRoot}/api/health`).catch(() => { });
    }, []);

    const set = (key, val) => setForm({ ...form, [key]: val });

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            const payload = {
                ...form,
                role: 'student',
                field_id: form.field_id ? parseInt(form.field_id) : null,
                semester: parseInt(form.semester),
            };
            const { data } = await API.post('/auth/signup', payload);
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            navigate('/student');
        } catch (err) {
            setError(err.response?.data?.detail || 'Signup failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-card glass-card card-3d" style={{ maxWidth: 480 }}>
                <h1>Create Student Account</h1>
                <p className="subtitle">Join the K.T. early-warning system</p>

                {error && <div className="error-msg">{error}</div>}
                <div className="info-banner">
                    Student self-signup only. Teacher and admin accounts are created by an administrator.
                </div>

                <form className="auth-form" onSubmit={handleSubmit}>
                    <div className="input-group">
                        <label>Full Name</label>
                        <input className="input-field" placeholder="John Doe" value={form.name}
                            onChange={(e) => set('name', e.target.value)} required />
                    </div>

                    <div className="input-group">
                        <label>Email Address</label>
                        <input className="input-field" type="email" placeholder="you@university.edu"
                            value={form.email} onChange={(e) => set('email', e.target.value)} required />
                    </div>

                    <div className="input-group">
                        <label>Password</label>
                        <input className="input-field" type="password" placeholder="Min. 6 characters"
                            value={form.password} onChange={(e) => set('password', e.target.value)} required minLength={6} />
                    </div>

                    <div className="input-group">
                        <label>Student ID</label>
                        <input className="input-field" placeholder="e.g. STU2024001"
                            value={form.student_id} onChange={(e) => set('student_id', e.target.value)} />
                    </div>

                    <div className="input-group">
                        <label>Department</label>
                        <input className="input-field" placeholder="e.g. Computer Science"
                            value={form.department} onChange={(e) => set('department', e.target.value)} />
                    </div>

                    <div className="input-group">
                        <label>Current Semester</label>
                        <select className="input-field" value={form.semester} onChange={(e) => set('semester', e.target.value)}>
                            {[1, 2, 3, 4, 5, 6, 7, 8].map(n => <option key={n} value={n}>Semester {n}</option>)}
                        </select>
                    </div>

                    <button className="btn btn-primary btn-lg" type="submit" disabled={loading}>
                        {loading ? 'Creating...' : 'Create Account'}
                    </button>
                </form>

                <p className="auth-switch">
                    Already have an account? <Link to="/login">Sign in</Link>
                </p>
            </div>
        </div>
    );
}
