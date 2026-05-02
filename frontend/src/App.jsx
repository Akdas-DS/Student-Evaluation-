import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Signup from './pages/Signup';
import AdminDashboard from './pages/admin/AdminDashboard';
import ManageFields from './pages/admin/ManageFields';
import ManageSubjects from './pages/admin/ManageSubjects';
import ManageUsers from './pages/admin/ManageUsers';
import TeacherDashboard from './pages/teacher/TeacherDashboard';
import TeacherSubjects from './pages/teacher/TeacherSubjects';
import StudentDashboard from './pages/student/StudentDashboard';
import Assessment from './pages/student/Assessment';
import Results from './pages/student/Results';
import History from './pages/student/History';
import './index.css';

function ProtectedRoute({ children, roles }) {
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    const token = localStorage.getItem('token');
    if (!token || !user) return <Navigate to="/login" />;
    if (roles && !roles.includes(user.role)) return <Navigate to="/login" />;
    return children;
}

export default function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/signup" element={<Signup />} />

                {/* Admin Routes */}
                <Route path="/admin" element={<ProtectedRoute roles={['admin']}><AdminDashboard /></ProtectedRoute>} />
                <Route path="/admin/fields" element={<ProtectedRoute roles={['admin']}><ManageFields /></ProtectedRoute>} />
                <Route path="/admin/subjects" element={<ProtectedRoute roles={['admin']}><ManageSubjects /></ProtectedRoute>} />
                <Route path="/admin/users" element={<ProtectedRoute roles={['admin']}><ManageUsers /></ProtectedRoute>} />

                {/* Teacher Routes */}
                <Route path="/teacher" element={<ProtectedRoute roles={['teacher']}><TeacherDashboard /></ProtectedRoute>} />
                <Route path="/teacher/subjects" element={<ProtectedRoute roles={['teacher']}><TeacherSubjects /></ProtectedRoute>} />

                {/* Student Routes */}
                <Route path="/student" element={<ProtectedRoute roles={['student']}><StudentDashboard /></ProtectedRoute>} />
                <Route path="/student/assess/:subjectId" element={<ProtectedRoute roles={['student']}><Assessment /></ProtectedRoute>} />
                <Route path="/student/results/:assessmentId" element={<ProtectedRoute roles={['student']}><Results /></ProtectedRoute>} />
                <Route path="/student/history" element={<ProtectedRoute roles={['student']}><History /></ProtectedRoute>} />

                <Route path="*" element={<Navigate to="/login" />} />
            </Routes>
        </BrowserRouter>
    );
}
