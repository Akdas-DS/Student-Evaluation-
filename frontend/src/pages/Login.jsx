import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import API from '../api';

export default function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [message, setMessage] = useState('');
    const [loading, setLoading] = useState(false);
    const [resetMode, setResetMode] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setMessage('');
        setLoading(true);

        try {
            if (resetMode) {
                await API.post('/auth/reset-password', { email, new_password: password });
                setMessage('Password reset successful. You can now login.');
                setResetMode(false);
                setPassword('');
            } else {
                const { data } = await API.post('/auth/login', { email, password });
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('user', JSON.stringify(data.user));
                const routes = { admin: '/admin', teacher: '/teacher', student: '/student' };
                navigate(routes[data.user.role] || '/login');
            }
        } catch (err) {
            setError(err.response?.data?.detail || (resetMode ? 'Password reset failed' : 'Login failed'));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-card glass-card card-3d">
                <h1>K.T. Early Warning</h1>
                <p className="subtitle">{resetMode ? 'Reset your password' : 'Sign in to your university account'}</p>

                {error && <div className="error-msg">{error}</div>}
                {message && <div className="info-banner" style={{marginBottom: 16}}>{message}</div>}

                <form className="auth-form" onSubmit={handleSubmit}>
                    <div className="input-group">
                        <label>Email Address</label>
                        <input className="input-field" type="email" placeholder="you@university.edu"
                            value={email} onChange={(e) => setEmail(e.target.value)} required />
                    </div>

                    <div className="input-group">
                        <label>{resetMode ? 'New Password' : 'Password'}</label>
                        <input className="input-field" type="password" placeholder={resetMode ? "Min 8 characters" : "Password"}
                            value={password} onChange={(e) => setPassword(e.target.value)} minLength={resetMode ? 8 : 1} required />
                    </div>

                    {!resetMode && (
                        <div style={{ textAlign: 'right', marginBottom: '16px' }}>
                            <button type="button" onClick={() => {setResetMode(true); setError(''); setMessage('');}} style={{ background: 'none', border: 'none', color: 'var(--accent-cyan)', cursor: 'pointer', fontSize: '0.85rem' }}>Forgot password?</button>
                        </div>
                    )}

                    <button className="btn btn-primary btn-lg" type="submit" disabled={loading}>
                        {loading ? 'Processing...' : (resetMode ? 'Reset Password' : 'Sign In')}
                    </button>
                    
                    {resetMode && (
                        <button type="button" className="btn btn-outline btn-lg" onClick={() => {setResetMode(false); setError(''); setMessage('');}} style={{ marginTop: '12px' }}>
                            Back to Login
                        </button>
                    )}
                </form>

                {!resetMode && (
                    <p className="auth-switch">
                        Student account? <Link to="/signup">Create one</Link>
                    </p>
                )}
            </div>
        </div>
    );
}
