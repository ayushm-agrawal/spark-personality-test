import { doc, getDoc, updateDoc, setDoc } from 'firebase/firestore';
import { db } from '../firebase';

const STORAGE_KEY = 'ception_tutorial_completed';

/**
 * Check if tutorial has been completed (checks localStorage first, then Firestore)
 * @param {string|null} userId - Firebase user ID if signed in
 * @returns {Promise<boolean>} Whether tutorial has been completed
 */
export async function isTutorialCompleted(userId = null) {
  // First check localStorage (fastest)
  const localValue = localStorage.getItem(STORAGE_KEY);
  if (localValue === 'true') {
    return true;
  }

  // If user is signed in, check Firestore
  if (userId) {
    try {
      const userDoc = await getDoc(doc(db, 'users', userId));
      if (userDoc.exists()) {
        const tutorialCompleted = userDoc.data()?.tutorial_completed;
        if (tutorialCompleted) {
          // Sync to localStorage for future checks
          localStorage.setItem(STORAGE_KEY, 'true');
          return true;
        }
      }
    } catch (error) {
      console.error('Error checking tutorial status in Firestore:', error);
    }
  }

  return false;
}

/**
 * Mark tutorial as completed
 * @param {string|null} userId - Firebase user ID if signed in
 * @param {boolean} skipped - Whether user skipped vs completed
 * @param {number} skipSlide - Slide number where user skipped (if skipped)
 */
export async function markTutorialCompleted(userId = null, skipped = false, skipSlide = null) {
  // Always save to localStorage
  localStorage.setItem(STORAGE_KEY, 'true');

  // If user is signed in, also save to Firestore
  if (userId) {
    try {
      const userRef = doc(db, 'users', userId);
      const userDoc = await getDoc(userRef);

      const tutorialData = {
        tutorial_completed: true,
        tutorial_completed_at: new Date().toISOString(),
        tutorial_skipped: skipped,
        ...(skipped && skipSlide !== null && { tutorial_skip_slide: skipSlide }),
      };

      if (userDoc.exists()) {
        await updateDoc(userRef, tutorialData);
      } else {
        await setDoc(userRef, tutorialData, { merge: true });
      }
    } catch (error) {
      console.error('Error saving tutorial status to Firestore:', error);
    }
  }
}

/**
 * Sync local tutorial completion to Firestore (call on sign-in)
 * @param {string} userId - Firebase user ID
 */
export async function syncTutorialStatusOnSignIn(userId) {
  const localValue = localStorage.getItem(STORAGE_KEY);

  if (localValue === 'true') {
    // User completed tutorial while anonymous, sync to Firestore
    try {
      const userRef = doc(db, 'users', userId);
      const userDoc = await getDoc(userRef);

      // Only update if not already marked as completed in Firestore
      if (!userDoc.exists() || !userDoc.data()?.tutorial_completed) {
        await setDoc(userRef, {
          tutorial_completed: true,
          tutorial_completed_at: new Date().toISOString(),
          tutorial_synced_on_signin: true,
        }, { merge: true });
      }
    } catch (error) {
      console.error('Error syncing tutorial status to Firestore:', error);
    }
  }
}

/**
 * Reset tutorial status (for replay feature)
 * Note: This only affects the current session, doesn't permanently reset
 */
export function resetTutorialForReplay() {
  localStorage.removeItem(STORAGE_KEY);
}
