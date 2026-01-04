import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ModeSelection from './components/ModeSelection';
import InterestSelection from './components/InterestSelection';
import Assessment from './components/Assessment';
import Results from './components/Results';
import * as api from './api';

const STEPS = {
  MODE: 'mode',
  INTERESTS: 'interests',
  ASSESSMENT: 'assessment',
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
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.startTest(selectedMode);
      setSessionId(response.session_id);
      setMode(selectedMode);
      setModeConfig(response.mode_config);
      setInterestConfig(response.interest_config || null);

      // Handle UI flow based on backend response
      const uiFlow = response.ui_flow || {};

      if (uiFlow.proceed_directly_to_questions && response.next_question) {
        // Hackathon mode - skip interests, go directly to questions
        setCurrentQuestion(response.next_question);
        setQuestionNumber(1);
        setStep(STEPS.ASSESSMENT);

        saveSession({
          sessionId: response.session_id,
          mode: selectedMode,
          modeConfig: response.mode_config,
          interestConfig: null,
          step: STEPS.ASSESSMENT,
          questionNumber: 1
        });
      } else if (uiFlow.show_interest_selection) {
        // Show life context selection (overall or deep_dive mode)
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

  const handleInterestsSubmit = async (interests) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.selectInterests(sessionId, interests);
      if (response.next_question) {
        setCurrentQuestion(response.next_question);
        setQuestionNumber(1);
        setStep(STEPS.ASSESSMENT);

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
        // Test is complete, show results
        setIsAnalyzing(false);
        setResults(response);
        setStep(STEPS.RESULTS);
        localStorage.removeItem('ception_session');
      } else if (response.next_question) {
        // Move to next question
        setCurrentQuestion(response.next_question);
        setQuestionNumber(prev => prev + 1);

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
      try {
        await api.submitFeedback(sessionId, rating, archetype);
      } catch (err) {
        console.error('Failed to submit feedback:', err);
      }
    }
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
  };

  return (
    <div className="min-h-screen">
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
            <ModeSelection onSelectMode={handleModeSelect} />
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
              onFeedback={handleFeedback}
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
    </div>
  );
}

export default App;
