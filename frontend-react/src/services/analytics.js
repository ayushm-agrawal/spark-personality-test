import { analytics } from '../firebase';
import { logEvent, setUserProperties } from 'firebase/analytics';

// Helper to safely log events (handles analytics not being initialized)
const trackEvent = (eventName, params = {}) => {
  if (analytics) {
    logEvent(analytics, eventName, {
      ...params,
      timestamp: Date.now()
    });
  }
};

// Analytics tracking functions
export const Analytics = {
  // Page/Screen views
  screenView: (screenName) => trackEvent('screen_view', { screen_name: screenName }),

  // Test flow events
  modeSelected: (mode, questionCount) => trackEvent('mode_selected', {
    mode,
    question_count: questionCount
  }),

  interestsSelected: (interests, count) => trackEvent('interests_selected', {
    interests: interests.join(','),
    interest_count: count
  }),

  interestsSkipped: () => trackEvent('interests_skipped'),

  // Question events
  questionAnswered: (questionNumber, totalQuestions, trait, answerKey, responseTimeMs) =>
    trackEvent('question_answered', {
      question_number: questionNumber,
      total_questions: totalQuestions,
      trait,
      answer_key: answerKey,
      response_time_ms: responseTimeMs
    }),

  // Completion events
  testCompleted: (mode, archetype, confidence, scores, durationMs) =>
    trackEvent('test_completed', {
      mode,
      archetype,
      confidence: Math.round(confidence),
      openness: Math.round(scores?.Openness || 0),
      conscientiousness: Math.round(scores?.Conscientiousness || 0),
      extraversion: Math.round(scores?.Extraversion || 0),
      agreeableness: Math.round(scores?.Agreeableness || 0),
      emotional_stability: Math.round(scores?.Emotional_Stability || 0),
      duration_seconds: Math.round(durationMs / 1000)
    }),

  // Engagement events
  feedbackSubmitted: (rating, archetype) => trackEvent('feedback_submitted', {
    rating,
    archetype
  }),

  shareClicked: (method) => trackEvent('share_clicked', { method }),
  shareCompleted: (method) => trackEvent('share_completed', { method }),

  archetypeGalleryViewed: () => trackEvent('archetype_gallery_viewed'),
  historyResultViewed: (archetype) => trackEvent('history_result_viewed', { archetype }),

  // Auth events
  signInStarted: () => trackEvent('sign_in_started'),
  signInCompleted: () => trackEvent('sign_in_completed'),
  signedOut: () => trackEvent('signed_out'),

  // Abandonment tracking
  testAbandoned: (step, questionNumber) => trackEvent('test_abandoned', {
    step,
    question_number: questionNumber
  }),

  // Tutorial events
  tutorialStarted: () => trackEvent('tutorial_started'),
  tutorialSlideViewed: (slideIndex, slideId) => trackEvent('tutorial_slide_viewed', {
    slide_index: slideIndex,
    slide_id: slideId
  }),
  tutorialCompleted: () => trackEvent('tutorial_completed'),
  tutorialSkipped: (slideIndex) => trackEvent('tutorial_skipped', {
    skip_slide: slideIndex
  }),

  // Set user properties (for segmentation in Firebase)
  setUserArchetype: (archetype) => {
    if (analytics) {
      setUserProperties(analytics, { last_archetype: archetype });
    }
  }
};
