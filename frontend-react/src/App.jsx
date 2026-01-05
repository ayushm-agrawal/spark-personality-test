import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ModeSelection from './components/ModeSelection';
import InterestSelection from './components/InterestSelection';
import InterestInput from './components/InterestInput';
import Assessment from './components/Assessment';
import Results from './components/Results';
import GoogleSignInButton from './components/GoogleSignInButton';
import ArchetypeGallery from './components/ArchetypeGallery';
import ProfilePage from './components/ProfilePage';
import { useAuth } from './contexts/AuthContext';
import { saveAssessment, getUserAssessments, ensureUserProfile, assessmentToResults, getHasSeenProfile, markProfileAsSeen } from './services/assessmentHistory';
import { Analytics } from './services/analytics';
import * as api from './api';

const STEPS = {
  MODE: 'mode',
  INTEREST_INPUT: 'interest_input',  // Single interest input for deep_dive
  INTERESTS: 'interests',
  ASSESSMENT: 'assessment',
  EXTENSION_OFFER: 'extension_offer',
  RESULTS: 'results'
};

function App() {
  const [step, setStep] = useState(STEPS.MODE);
  const [sessionId, setSessionId] = useState(null);
  const [mode, setMode] = useState(null);
  const [modeConfig, setModeConfig] = useState(null);
  const [interestConfig, setInterestConfig] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [questionNumber, setQuestionNumber] = useState(0);
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  // Auth state
  const { user, isAuthenticated } = useAuth();
  const [userHistory, setUserHistory] = useState([]);
  const [isViewingHistory, setIsViewingHistory] = useState(false);
  const resultsSavedRef = useRef(false);

  // Holistic profile state
  const [profileId, setProfileId] = useState(null);
  const [holisticProfile, setHolisticProfile] = useState(null);

  // Gallery state
  const [showGallery, setShowGallery] = useState(false);

  // Profile page state
  const [showProfile, setShowProfile] = useState(false);
  const [hasSeenProfile, setHasSeenProfile] = useState(true); // Default true to not show badge initially

  // Extension offer state
  const [extensionOffer, setExtensionOffer] = useState(null);
  const [pendingResults, setPendingResults] = useState(null);

  // Deep dive interest state
  const [deepDiveInterest, setDeepDiveInterest] = useState(null);

  // Timing refs for analytics
  const testStartTimeRef = useRef(null);
  const questionStartTimeRef = useRef(null);

  // Load user history and profile when authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      // Ensure user profile exists
      ensureUserProfile(user).catch(console.error);

      // Load assessment history and check if should show profile badge
      getUserAssessments(user.uid)
        .then(assessments => {
          setUserHistory(assessments);
          // If user has at least 1 assessment, check if they've seen profile
          if (assessments.length > 0) {
            getHasSeenProfile(user.uid)
              .then(seen => setHasSeenProfile(seen))
              .catch(() => setHasSeenProfile(true));
          }
        })
        .catch(console.error);

      // Get or create holistic profile
      api.getOrCreateProfile(user.uid, null)
        .then(profile => {
          if (profile && profile.profile_id) {
            setProfileId(profile.profile_id);
          }
        })
        .catch(console.error);
    } else {
      setUserHistory([]);
      setProfileId(null);
      setHolisticProfile(null);
      setHasSeenProfile(true); // Reset to hide badge when logged out
    }
  }, [isAuthenticated, user]);

  // Auto-save results when test completes (if signed in)
  useEffect(() => {
    if (results?.test_complete && isAuthenticated && user && !resultsSavedRef.current && !isViewingHistory) {
      resultsSavedRef.current = true;
      saveAssessment(user.uid, results)
        .then(() => getUserAssessments(user.uid))
        .then(setUserHistory)
        .catch(console.error);

      // Update holistic profile if we have a profile ID and session ID
      if (profileId && sessionId) {
        api.updateProfile(profileId, sessionId)
          .then(profileData => {
            setHolisticProfile(profileData);
          })
          .catch(console.error);
      }
    }
  }, [results, isAuthenticated, user, isViewingHistory, profileId, sessionId]);

  // Reset saved ref when starting new test
  useEffect(() => {
    if (step === STEPS.MODE) {
      resultsSavedRef.current = false;
      setIsViewingHistory(false);
      setHolisticProfile(null);
    }
  }, [step]);

  // Handle viewing historical result
  const handleViewHistory = (assessment) => {
    setIsViewingHistory(true);
    setResults(assessmentToResults(assessment));
    setMode(assessment.mode);
    setStep(STEPS.RESULTS);
    // Track history view
    Analytics.historyResultViewed(assessment.archetype?.name || 'unknown');
  };

  // Handle viewing archetype gallery
  const handleViewGallery = () => {
    setShowGallery(true);
    Analytics.archetypeGalleryViewed();
  };

  const handleCloseGallery = () => {
    setShowGallery(false);
  };

  // Handle viewing profile page
  const handleViewProfile = () => {
    setShowProfile(true);
    // Mark profile as seen to hide the badge
    if (user && !hasSeenProfile) {
      markProfileAsSeen(user.uid)
        .then(() => setHasSeenProfile(true))
        .catch(console.error);
    }
  };

  const handleCloseProfile = () => {
    setShowProfile(false);
  };

  // Try to restore session from localStorage
  useEffect(() => {
    const savedSession = localStorage.getItem('ception_session');
    if (savedSession) {
      try {
        const session = JSON.parse(savedSession);
        // Only restore if session is less than 1 hour old
        if (Date.now() - session.timestamp < 3600000) {
          setSessionId(session.sessionId);
          setMode(session.mode);
          setModeConfig(session.modeConfig);
          setInterestConfig(session.interestConfig);
          setStep(session.step || STEPS.INTERESTS);
          setQuestionNumber(session.questionNumber || 0);
        } else {
          localStorage.removeItem('ception_session');
        }
      } catch (e) {
        localStorage.removeItem('ception_session');
      }
    }
  }, []);

  // Save session to localStorage
  const saveSession = (data) => {
    localStorage.setItem('ception_session', JSON.stringify({
      ...data,
      timestamp: Date.now()
    }));
  };

  const handleModeSelect = async (selectedMode) => {
    // Deep dive mode shows interest input first (before starting test)
    if (selectedMode === 'deep_dive') {
      setMode(selectedMode);
      setStep(STEPS.INTEREST_INPUT);
      testStartTimeRef.current = Date.now();
      return;
    }

    setIsLoading(true);
    setError(null);
    testStartTimeRef.current = Date.now();

    try {
      const response = await api.startTest(selectedMode);
      setSessionId(response.session_id);
      setMode(selectedMode);
      setModeConfig(response.mode_config);
      setInterestConfig(response.interest_config || null);

      // Track mode selection
      Analytics.modeSelected(selectedMode, response.mode_config?.question_count || 10);

      // Handle UI flow based on backend response
      const uiFlow = response.ui_flow || {};

      if (uiFlow.proceed_directly_to_questions && response.next_question) {
        // Hackathon mode - skip interests, go directly to questions
        setCurrentQuestion(response.next_question);
        setQuestionNumber(1);
        setStep(STEPS.ASSESSMENT);
        questionStartTimeRef.current = Date.now();

        saveSession({
          sessionId: response.session_id,
          mode: selectedMode,
          modeConfig: response.mode_config,
          interestConfig: null,
          step: STEPS.ASSESSMENT,
          questionNumber: 1
        });
      } else if (uiFlow.show_interest_selection) {
        // Show life context selection (overall mode)
        setStep(STEPS.INTERESTS);

        saveSession({
          sessionId: response.session_id,
          mode: selectedMode,
          modeConfig: response.mode_config,
          interestConfig: response.interest_config,
          step: STEPS.INTERESTS,
          questionNumber: 0
        });
      } else {
        // Fallback - go to interests
        setStep(STEPS.INTERESTS);
      }
    } catch (err) {
      setError('Failed to start test. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  // Handler for single interest input (deep_dive mode)
  const handleInterestInputSubmit = async (interest) => {
    setIsLoading(true);
    setError(null);
    setDeepDiveInterest(interest);

    // Track interest selection
    Analytics.interestsSelected([interest], 1);

    try {
      // Start test with the interest parameter
      const response = await api.startTest('deep_dive', interest);
      setSessionId(response.session_id);
      setModeConfig(response.mode_config);

      if (response.next_question) {
        setCurrentQuestion(response.next_question);
        setQuestionNumber(1);
        setStep(STEPS.ASSESSMENT);
        questionStartTimeRef.current = Date.now();

        saveSession({
          sessionId: response.session_id,
          mode: 'deep_dive',
          modeConfig: response.mode_config,
          interestConfig: null,
          step: STEPS.ASSESSMENT,
          questionNumber: 1
        });
      }
    } catch (err) {
      setError('Failed to start test. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInterestsSubmit = async (interests) => {
    setIsLoading(true);
    setError(null);

    // Track interests selection
    if (interests && interests.length > 0) {
      Analytics.interestsSelected(interests, interests.length);
    } else {
      Analytics.interestsSkipped();
    }

    try {
      const response = await api.selectInterests(sessionId, interests);
      if (response.next_question) {
        setCurrentQuestion(response.next_question);
        setQuestionNumber(1);
        setStep(STEPS.ASSESSMENT);
        questionStartTimeRef.current = Date.now();

        saveSession({
          sessionId,
          mode,
          modeConfig,
          interestConfig,
          step: STEPS.ASSESSMENT,
          questionNumber: 1
        });
      }
    } catch (err) {
      setError('Failed to save interests. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnswer = async (answer) => {
    // Calculate response time for this question
    const responseTimeMs = questionStartTimeRef.current
      ? Date.now() - questionStartTimeRef.current
      : 0;

    // Track question answered
    Analytics.questionAnswered(
      questionNumber,
      modeConfig?.question_count || 10,
      currentQuestion?.trait || currentQuestion?.trait_targets?.[0] || 'unknown',
      answer,
      responseTimeMs
    );

    // Show analyzing animation if this is the last question
    const isLastQuestion = questionNumber >= (modeConfig?.question_count || 10);
    if (isLastQuestion) {
      setIsAnalyzing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);

    try {
      const response = await api.submitResponse(
        sessionId,
        currentQuestion.id,
        answer
      );

      if (response.test_complete) {
        // Check if extension is available before showing results
        try {
          const extensionCheck = await api.checkExtension(sessionId);
          if (extensionCheck.offer_extension) {
            // Store results for later and show extension offer
            setIsAnalyzing(false);
            setPendingResults(response);
            setExtensionOffer(extensionCheck);
            setStep(STEPS.EXTENSION_OFFER);
            return;
          }
        } catch (err) {
          console.error('Failed to check extension:', err);
          // Continue to show results even if extension check fails
        }

        // No extension offered, show results
        setIsAnalyzing(false);
        setResults(response);
        setStep(STEPS.RESULTS);
        localStorage.removeItem('ception_session');

        // Track test completion
        const testDuration = testStartTimeRef.current
          ? Date.now() - testStartTimeRef.current
          : 0;
        Analytics.testCompleted(
          mode,
          response.archetype?.name || response.suggested_archetype || 'unknown',
          response.archetype?.confidence || response.archetype_confidence || 0,
          response.scores || {},
          testDuration
        );
        Analytics.setUserArchetype(response.archetype?.name || response.suggested_archetype);
      } else if (response.next_question) {
        // Move to next question
        setCurrentQuestion(response.next_question);
        setQuestionNumber(prev => prev + 1);
        questionStartTimeRef.current = Date.now();

        saveSession({
          sessionId,
          mode,
          modeConfig,
          interestConfig,
          step: STEPS.ASSESSMENT,
          questionNumber: questionNumber + 1
        });
      } else if (response.test_paused) {
        // Handle paused state - get results
        const resultsResponse = await api.getResults(sessionId);
        setResults(resultsResponse);
        setStep(STEPS.RESULTS);
        localStorage.removeItem('ception_session');
      }
    } catch (err) {
      setError('Failed to submit answer. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
      setIsAnalyzing(false);
    }
  };

  const handleFeedback = async (rating) => {
    const archetype = results?.archetype?.name || results?.suggested_archetype;
    if (sessionId && archetype) {
      // Track feedback submission
      Analytics.feedbackSubmitted(rating, archetype);
      try {
        await api.submitFeedback(sessionId, rating, archetype);
      } catch (err) {
        console.error('Failed to submit feedback:', err);
      }
    }
  };

  // Handle accepting the extension offer
  const handleAcceptExtension = async () => {
    setIsLoading(true);
    try {
      const response = await api.acceptExtension(sessionId);
      if (response.next_question) {
        // Update question count and continue assessment
        setModeConfig(prev => ({
          ...prev,
          question_count: response.new_question_count
        }));
        setCurrentQuestion(response.next_question);
        setQuestionNumber(prev => prev + 1);
        questionStartTimeRef.current = Date.now();
        setExtensionOffer(null);
        setPendingResults(null);
        setStep(STEPS.ASSESSMENT);

        // Track extension accepted
        Analytics.trackEvent?.('extension_accepted', {
          focus_traits: response.focus_traits?.join(',')
        });
      }
    } catch (err) {
      console.error('Failed to accept extension:', err);
      // Fall back to showing pending results
      handleDeclineExtension();
    } finally {
      setIsLoading(false);
    }
  };

  // Handle declining the extension offer
  const handleDeclineExtension = () => {
    if (pendingResults) {
      setResults(pendingResults);
      setStep(STEPS.RESULTS);
      localStorage.removeItem('ception_session');

      // Track test completion
      const testDuration = testStartTimeRef.current
        ? Date.now() - testStartTimeRef.current
        : 0;
      Analytics.testCompleted(
        mode,
        pendingResults.archetype?.name || pendingResults.suggested_archetype || 'unknown',
        pendingResults.archetype?.confidence || pendingResults.archetype_confidence || 0,
        pendingResults.scores || {},
        testDuration
      );
      Analytics.setUserArchetype(pendingResults.archetype?.name || pendingResults.suggested_archetype);
    }
    setExtensionOffer(null);
    setPendingResults(null);
  };

  const resetTest = () => {
    localStorage.removeItem('ception_session');
    setStep(STEPS.MODE);
    setSessionId(null);
    setMode(null);
    setModeConfig(null);
    setInterestConfig(null);
    setCurrentQuestion(null);
    setQuestionNumber(0);
    setResults(null);
    setError(null);
    setIsAnalyzing(false);
    setExtensionOffer(null);
    setPendingResults(null);
    setDeepDiveInterest(null);
    setHolisticProfile(null);
  };

  return (
    <div className="min-h-screen">
      {/* Google Sign In Button - only on MODE and RESULTS screens */}
      {(step === STEPS.MODE || step === STEPS.RESULTS) && (
        <div className="fixed top-4 right-4 z-50">
          <GoogleSignInButton
            onViewProfile={handleViewProfile}
            showProfileBadge={isAuthenticated && userHistory.length > 0 && !hasSeenProfile}
          />
        </div>
      )}

      {/* Error toast */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -50 }}
            className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 px-6 py-3 bg-red-500/90 text-white rounded-lg shadow-lg"
          >
            {error}
            <button
              onClick={() => setError(null)}
              className="ml-4 text-white/80 hover:text-white"
            >
              ✕
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Reset button */}
      {step !== STEPS.MODE && step !== STEPS.RESULTS && (
        <button
          onClick={resetTest}
          className="fixed top-4 left-4 z-40 px-3 py-2 text-sm text-gray-400 hover:text-white transition-colors"
        >
          ← Start Over
        </button>
      )}

      {/* Loading overlay */}
      <AnimatePresence>
        {isLoading && step === STEPS.MODE && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          >
            <div className="glass-card p-8 text-center">
              <div className="animate-spin h-12 w-12 border-4 border-purple-500 border-t-transparent rounded-full mx-auto mb-4" />
              <p className="text-gray-300">Starting your assessment...</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main content */}
      <AnimatePresence mode="wait">
        {step === STEPS.MODE && (
          <motion.div
            key="mode"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, x: -100 }}
          >
            <ModeSelection
              onSelectMode={handleModeSelect}
              userHistory={userHistory}
              onViewHistory={handleViewHistory}
              onViewGallery={handleViewGallery}
            />
          </motion.div>
        )}

        {step === STEPS.INTEREST_INPUT && (
          <motion.div
            key="interest-input"
            initial={{ opacity: 0, x: 100 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -100 }}
          >
            <InterestInput
              onSubmit={handleInterestInputSubmit}
              isLoading={isLoading}
            />
          </motion.div>
        )}

        {step === STEPS.INTERESTS && (
          <motion.div
            key="interests"
            initial={{ opacity: 0, x: 100 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -100 }}
          >
            <InterestSelection
              onSubmit={handleInterestsSubmit}
              isLoading={isLoading}
              mode={mode}
              config={interestConfig}
            />
          </motion.div>
        )}

        {step === STEPS.ASSESSMENT && (
          <motion.div
            key="assessment"
            initial={{ opacity: 0, x: 100 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -100 }}
          >
            <Assessment
              question={currentQuestion}
              questionNumber={questionNumber}
              totalQuestions={modeConfig?.question_count || 10}
              onAnswer={handleAnswer}
              isLoading={isLoading}
              isAnalyzing={isAnalyzing}
              mode={mode}
            />
          </motion.div>
        )}

        {step === STEPS.EXTENSION_OFFER && extensionOffer && (
          <motion.div
            key="extension"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="min-h-screen bg-[#09090b] flex items-center justify-center px-6"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="max-w-md w-full text-center"
            >
              {/* Fuzzy icon */}
              <motion.div
                className="w-24 h-24 mx-auto mb-6 rounded-full bg-gradient-to-br from-violet-500/20 to-purple-500/20 flex items-center justify-center"
                animate={{ scale: [1, 1.05, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                <span className="text-4xl">🔍</span>
              </motion.div>

              <h2 className="text-2xl font-bold text-white mb-3">
                We're getting a picture, but it's a bit fuzzy
              </h2>

              <p className="text-neutral-400 mb-8">
                {extensionOffer.message || "Want sharper results? Just 2 more questions."}
              </p>

              <div className="flex flex-col gap-3">
                <button
                  onClick={handleAcceptExtension}
                  disabled={isLoading}
                  className="w-full py-4 px-6 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 text-white font-medium hover:from-violet-500 hover:to-purple-500 transition-all disabled:opacity-50"
                >
                  {isLoading ? (
                    <span className="flex items-center justify-center gap-2">
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Loading...
                    </span>
                  ) : (
                    "Yes, let's go"
                  )}
                </button>

                <button
                  onClick={handleDeclineExtension}
                  disabled={isLoading}
                  className="w-full py-4 px-6 rounded-xl border border-neutral-700 text-neutral-300 hover:bg-neutral-800 transition-colors disabled:opacity-50"
                >
                  Show me what you have
                </button>
              </div>

              {extensionOffer.focus_traits && (
                <p className="text-xs text-neutral-600 mt-6">
                  Focus areas: {extensionOffer.focus_traits.map(t => t.replace('_', ' ')).join(', ')}
                </p>
              )}
            </motion.div>
          </motion.div>
        )}

        {step === STEPS.RESULTS && (
          <motion.div
            key="results"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-[#09090b]"
          >
            <Results
              results={results}
              mode={mode}
              interest={deepDiveInterest}
              onFeedback={handleFeedback}
              showSavePrompt={!isAuthenticated && !isViewingHistory}
              onViewGallery={handleViewGallery}
              holisticProfile={holisticProfile}
            />
            <div className="text-center pb-12 bg-[#09090b]">
              <button
                onClick={resetTest}
                className="px-6 py-3 rounded-xl bg-neutral-800 border border-neutral-700 text-neutral-300 hover:bg-neutral-700 hover:text-white transition-colors"
              >
                Take Another Test
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Archetype Gallery Modal */}
      <AnimatePresence>
        {showGallery && (
          <ArchetypeGallery
            onClose={handleCloseGallery}
            userArchetype={results?.archetype?.name || userHistory[0]?.archetype?.name}
          />
        )}
      </AnimatePresence>

      {/* Profile Page Modal */}
      <AnimatePresence>
        {showProfile && (
          <ProfilePage
            onClose={handleCloseProfile}
            onStartTest={resetTest}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;
