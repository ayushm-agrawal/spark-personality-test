// Use environment variable for API URL, fallback to /api for proxy setup
const API_BASE = import.meta.env.VITE_API_URL || '/api';

export async function getAssessmentModes() {
  const response = await fetch(`${API_BASE}/assessment-modes/`);
  if (!response.ok) throw new Error('Failed to fetch assessment modes');
  return response.json();
}

export async function getInterestCategories() {
  const response = await fetch(`${API_BASE}/interest-categories/`);
  if (!response.ok) throw new Error('Failed to fetch interest categories');
  return response.json();
}

export async function getLifeContexts() {
  const response = await fetch(`${API_BASE}/life-contexts/`);
  if (!response.ok) throw new Error('Failed to fetch life contexts');
  return response.json();
}

export async function getArchetypes() {
  const response = await fetch(`${API_BASE}/archetypes/`);
  if (!response.ok) throw new Error('Failed to fetch archetypes');
  return response.json();
}

export async function startTest(mode = 'overall', interest = null) {
  const body = { mode };
  if (interest) {
    body.interest = interest;
  }
  const response = await fetch(`${API_BASE}/start-test/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error('Failed to start test');
  return response.json();
}

export async function selectInterests(sessionId, interests) {
  const response = await fetch(`${API_BASE}/select-interests/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, interests }),
  });
  if (!response.ok) throw new Error('Failed to select interests');
  return response.json();
}

export async function submitResponse(sessionId, questionId, answer) {
  const response = await fetch(`${API_BASE}/submit-response/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      question_id: questionId,
      answer: answer
    }),
  });
  if (!response.ok) throw new Error('Failed to submit response');
  return response.json();
}

export async function getResults(sessionId) {
  const response = await fetch(`${API_BASE}/get-results/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!response.ok) throw new Error('Failed to get results');
  return response.json();
}

export async function submitFeedback(sessionId, rating, archetype) {
  const response = await fetch(`${API_BASE}/collect-feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      rating,
      timestamp: Date.now() / 1000,
      archetype
    }),
  });
  if (!response.ok) throw new Error('Failed to submit feedback');
  return response.json();
}

export async function checkExtension(sessionId) {
  const response = await fetch(`${API_BASE}/check-extension/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!response.ok) throw new Error('Failed to check extension');
  return response.json();
}

export async function acceptExtension(sessionId) {
  const response = await fetch(`${API_BASE}/accept-extension/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!response.ok) throw new Error('Failed to accept extension');
  return response.json();
}
