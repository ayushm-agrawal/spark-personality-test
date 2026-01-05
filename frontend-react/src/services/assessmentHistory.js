import {
  collection,
  doc,
  setDoc,
  getDoc,
  getDocs,
  query,
  orderBy,
  limit,
  serverTimestamp
} from 'firebase/firestore';
import { db } from '../firebase';

/**
 * Save an assessment result to the user's history
 * @param {string} userId - Firebase Auth user ID
 * @param {object} results - Full results object from the backend
 * @returns {Promise<string>} - The assessment document ID
 */
export async function saveAssessment(userId, results) {
  const assessmentRef = doc(collection(db, `users/${userId}/assessments`));

  const assessmentData = {
    sessionId: results.session_id || null,
    mode: results.mode,
    completedAt: serverTimestamp(),
    archetype: results.archetype || null,
    archetypeConfidence: results.archetype_confidence || 0,
    normalizedScores: results.normalized_scores || {},
    traitBreakdown: results.trait_breakdown || {},
    allMatches: results.all_matches || {},
    personalizedProfile: results.personalized_profile || {},
    modeSpecific: results.mode_specific || {}
  };

  await setDoc(assessmentRef, assessmentData);
  return assessmentRef.id;
}

/**
 * Get a user's assessment history
 * @param {string} userId - Firebase Auth user ID
 * @param {number} maxResults - Maximum number of results to return
 * @returns {Promise<Array>} - Array of assessment objects
 */
export async function getUserAssessments(userId, maxResults = 10) {
  const assessmentsRef = collection(db, `users/${userId}/assessments`);
  const q = query(
    assessmentsRef,
    orderBy('completedAt', 'desc'),
    limit(maxResults)
  );

  const snapshot = await getDocs(q);
  return snapshot.docs.map(doc => ({
    id: doc.id,
    ...doc.data(),
    // Convert Firestore timestamp to JS Date
    completedAt: doc.data().completedAt?.toDate() || new Date()
  }));
}

/**
 * Ensure user profile document exists
 * @param {object} user - Firebase Auth user object
 */
export async function ensureUserProfile(user) {
  const userRef = doc(db, 'users', user.uid);
  await setDoc(userRef, {
    displayName: user.displayName || null,
    email: user.email || null,
    photoURL: user.photoURL || null,
    lastActiveAt: serverTimestamp()
  }, { merge: true });
}

/**
 * Check if user has seen their profile page
 * @param {string} userId - Firebase Auth user ID
 * @returns {Promise<boolean>} - True if user has seen profile
 */
export async function getHasSeenProfile(userId) {
  try {
    const userRef = doc(db, 'users', userId);
    const snapshot = await getDoc(userRef);
    if (snapshot.exists()) {
      return snapshot.data().hasSeenProfile === true;
    }
    return false;
  } catch (error) {
    console.error('Error checking hasSeenProfile:', error);
    return false;
  }
}

/**
 * Mark that user has seen their profile page
 * @param {string} userId - Firebase Auth user ID
 */
export async function markProfileAsSeen(userId) {
  try {
    const userRef = doc(db, 'users', userId);
    await setDoc(userRef, {
      hasSeenProfile: true,
      profileSeenAt: serverTimestamp()
    }, { merge: true });
  } catch (error) {
    console.error('Error marking profile as seen:', error);
  }
}

/**
 * Transform stored assessment back to results format for display
 * @param {object} assessment - Stored assessment from Firestore
 * @returns {object} - Results object compatible with Results component
 */
export function assessmentToResults(assessment) {
  return {
    test_complete: true,
    mode: assessment.mode,
    archetype: assessment.archetype,
    archetype_confidence: assessment.archetypeConfidence,
    normalized_scores: assessment.normalizedScores,
    trait_breakdown: assessment.traitBreakdown,
    all_matches: assessment.allMatches,
    personalized_profile: assessment.personalizedProfile,
    mode_specific: assessment.modeSpecific
  };
}
