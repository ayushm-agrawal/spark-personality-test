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

export async function getOrCreateProfile(userId = null, deviceFingerprint = null) {
  const response = await fetch(`${API_BASE}/get-profile/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      device_fingerprint: deviceFingerprint
    }),
  });
  if (!response.ok) throw new Error('Failed to get profile');
  return response.json();
}

export async function updateProfile(profileId, sessionId) {
  const response = await fetch(`${API_BASE}/update-profile/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      profile_id: profileId,
      session_id: sessionId
    }),
  });
  if (!response.ok) throw new Error('Failed to update profile');
  return response.json();
}

export async function getProfileView(profileId) {
  const response = await fetch(`${API_BASE}/profile/${profileId}`);
  if (!response.ok) throw new Error('Failed to get profile view');
  return response.json();
}

// Username API functions
export async function checkUsername(username) {
  const response = await fetch(`${API_BASE}/check-username/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username }),
  });
  if (!response.ok) throw new Error('Failed to check username');
  return response.json();
}

export async function setUsername(profileId, username, displayName = null) {
  const response = await fetch(`${API_BASE}/set-username/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      profile_id: profileId,
      username: username,
      display_name: displayName
    }),
  });
  if (!response.ok) throw new Error('Failed to set username');
  return response.json();
}

export async function generateUsername(displayName) {
  const response = await fetch(`${API_BASE}/generate-username/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ display_name: displayName }),
  });
  if (!response.ok) throw new Error('Failed to generate username');
  return response.json();
}

export async function getPublicProfile(username) {
  const response = await fetch(`${API_BASE}/u/${username}`);
  if (!response.ok) throw new Error('Failed to get public profile');
  return response.json();
}
