import { NavLink, useNavigate } from 'react-router-dom';

export default function Sidebar({ role }) {
    const navigate = useNavigate();
    const user = JSON.parse(localStorage.getItem('user') || '{}');

    const logout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        navigate('/login');
    };

    const links = {
        admin: [
            { to: '/admin', icon: '📊', label: 'Dashboard' },
            { to: '/admin/fields', icon: '🏛️', label: 'Manage Fields' },
            { to: '/admin/subjects', icon: '📚', label: 'Manage Subjects' },
            { to: '/admin/users', icon: '👥', label: 'Manage Users' },
        ],
        teacher: [
            { to: '/teacher', icon: '📊', label: 'Dashboard' },
            { to: '/teacher/subjects', icon: '📚', label: 'Subjects & Questions' },
        ],
        student: [
            { to: '/student', icon: '🏠', label: 'Dashboard' },
            { to: '/student/history', icon: '📋', label: 'My History' },
        ],
    };

    return (
        <div className="sidebar">
            <div className="sidebar-logo">🎓 K.T. Risk Predictor</div>
            <nav className="sidebar-nav">
                {(links[role] || []).map((link) => (
                    <NavLink key={link.to} to={link.to} end
                        className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
                        <span className="icon">{link.icon}</span>
                        {link.label}
                    </NavLink>
                ))}
            </nav>
            <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '16px', marginTop: '16px' }}>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>{user.name}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '12px' }}>{user.email}</div>
                <button className="sidebar-link" onClick={logout} style={{ color: 'var(--accent-red)' }}>
                    <span className="icon">🚪</span> Logout
                </button>
            </div>
        </div>
    );
}
