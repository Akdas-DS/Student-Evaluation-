import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import API from '../../api';

export default function Assessment() {
    const { subjectId } = useParams();
    const navigate = useNavigate();
    const [questions, setQuestions] = useState([]);
    const [answers, setAnswers] = useState({});
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        API.get(`/student/questions/${subjectId}`)
            .then(r => {
                setQuestions(r.data);
                const defaults = {};
                r.data.forEach(q => { defaults[q.id] = 5; });
                setAnswers(defaults);
            })
            .catch(err => setError(err.response?.data?.detail || 'Failed to load questions'))
            .finally(() => setLoading(false));
    }, [subjectId]);

    const setAnswer = (qId, val) => setAnswers({ ...answers, [qId]: parseFloat(val) });

    const submit = async () => {
        setSubmitting(true);
        setError('');
        try {
            const payload = {
                subject_id: parseInt(subjectId),
                answers: Object.entries(answers).map(([qId, val]) => ({ question_id: parseInt(qId), answer_value: val })),
            };
            const { data } = await API.post('/student/assess', payload);
            navigate(`/student/results/${data.id}`, { state: { result: data } });
        } catch (err) {
            setError(err.response?.data?.detail || 'Assessment failed');
        } finally {
            setSubmitting(false);
        }
    };

    const answered = Object.keys(answers).length;
    const progress = questions.length > 0 ? (answered / questions.length) * 100 : 0;

    if (loading) return (
        <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div className="spinner" />
        </div>
    );

    if (error && questions.length === 0) return (
        <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 16 }}>
            <div className="error-msg">{error}</div>
            <button className="btn btn-outline" onClick={() => navigate('/student')}>← Back to Dashboard</button>
        </div>
    );

    return (
        <div style={{ minHeight: '100vh', padding: '32px', maxWidth: 800, margin: '0 auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <button className="btn btn-outline btn-sm" onClick={() => navigate('/student')}>← Back</button>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{questions.length} questions</span>
            </div>

            <div className="progress-bar-container">
                <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
            </div>

            <div className="glass-card" style={{ padding: 32, marginBottom: 24 }}>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: 8, background: 'var(--gradient-primary)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                    📝 K.T. Risk Assessment
                </h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: 24 }}>
                    Rate yourself honestly on each parameter. Slide the bar from 0 (lowest) to 10 (highest).
                </p>

                {questions.map((q, i) => (
                    <div key={q.id} className={`slider-container glass-card fade-in stagger-${(i % 4) + 1}`}>
                        <div className="slider-header">
                            <span className="slider-question">
                                <strong style={{ color: 'var(--accent-blue)' }}>{i + 1}.</strong> {q.text}
                            </span>
                            <span className="slider-value">{answers[q.id] || 5}</span>
                        </div>
                        <div className="slider-category">📂 {q.category} • weight: {q.weight}x</div>
                        <input
                            type="range"
                            min={q.min_val}
                            max={q.max_val}
                            step={1}
                            value={answers[q.id] || 5}
                            onChange={e => setAnswer(q.id, e.target.value)}
                        />
                        <div className="slider-labels">
                            <span>{q.min_val} (Lowest)</span>
                            <span>{q.max_val} (Highest)</span>
                        </div>
                    </div>
                ))}

                {error && <div className="error-msg" style={{ marginBottom: 16 }}>{error}</div>}

                <button className="btn btn-primary btn-lg" onClick={submit} disabled={submitting} style={{ width: '100%', marginTop: 16 }}>
                    {submitting ? '🔄 Analyzing your risk...' : '🎯 Get My K.T. Risk Prediction'}
                </button>
            </div>
        </div>
    );
}
