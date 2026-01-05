import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Analytics } from '../services/analytics';

// Trait colors for visualization
const traitConfig = [
  { name: 'O', full: 'Openness', color: '#fb923c' },
  { name: 'C', full: 'Conscientiousness', color: '#a78bfa' },
  { name: 'E', full: 'Extraversion', color: '#38bdf8' },
  { name: 'A', full: 'Agreeableness', color: '#4ade80' },
  { name: 'S', full: 'Stability', color: '#f472b6' },
];

// Mode icons for header
const ModeIcon = ({ mode }) => {
  if (mode === 'hackathon') {
    return (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path d="M8 2 L9 7 L14 7 L10 10 L11 15 L8 12 L5 15 L6 10 L2 7 L7 7 Z"
          stroke="#fb923c" strokeWidth="1.5" fill="none" />
      </svg>
    );
  }
  if (mode === 'deep_dive' || mode === 'interest') {
    return (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="8" r="6" stroke="#2dd4bf" strokeWidth="1.5" strokeDasharray="2 2" fill="none" />
        <circle cx="8" cy="8" r="2" fill="#2dd4bf" />
      </svg>
    );
  }
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="8" r="5" stroke="#a78bfa" strokeWidth="1.5" fill="none" />
      <circle cx="8" cy="8" r="2" fill="#a78bfa" />
    </svg>
  );
};

const modeLabels = {
  hackathon: 'Hackathon Mode',
  overall: 'Full Profile',
  deep_dive: 'Deep Dive',
  interest: 'Deep Dive'  // Legacy support
};

const modeColors = {
  hackathon: '#fb923c',
  overall: '#a78bfa',
  deep_dive: '#2dd4bf',
  interest: '#2dd4bf'  // Legacy support
};

// Analyzing animation with improved design
function AnalyzingAnimation() {
  const [currentTrait, setCurrentTrait] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTrait((prev) => (prev + 1) % traitConfig.length);
    }, 800);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#09090b] flex flex-col items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="text-center"
      >
        {/* Spinning loader */}
        <motion.div
          className="w-20 h-20 mx-auto mb-8 rounded-full border-2 border-neutral-700 border-t-violet-400 relative"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        />

        <motion.h2
          className="text-2xl md:text-3xl font-bold text-white mb-4"
          animate={{ opacity: [0.7, 1, 0.7] }}
          transition={{ duration: 1.5, repeat: Infinity }}
        >
          Analyzing your responses...
        </motion.h2>

        <div className="h-8 mb-6">
          <AnimatePresence mode="wait">
            <motion.p
              key={currentTrait}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="text-lg"
              style={{ color: traitConfig[currentTrait].color }}
            >
              Evaluating {traitConfig[currentTrait].full}...
            </motion.p>
          </AnimatePresence>
        </div>

        {/* Trait abbreviation badges */}
        <div className="flex justify-center gap-2">
          {traitConfig.map((trait, i) => (
            <motion.span
              key={trait.name}
              className="text-xs px-2 py-1 rounded border"
              style={{
                borderColor: i <= currentTrait ? trait.color : '#404040',
                color: i <= currentTrait ? trait.color : '#6b7280',
                backgroundColor: i <= currentTrait ? `${trait.color}15` : 'transparent'
              }}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + i * 0.15 }}
            >
              {trait.name}
            </motion.span>
          ))}
        </div>

        <p className="text-neutral-500 mt-8 text-sm">
          Crafting your unique archetype profile...
        </p>
      </motion.div>
    </div>
  );
}


// Typewriter effect component for the header
function TypewriterText({ text, onComplete, className = "" }) {
  const [displayedText, setDisplayedText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (currentIndex < text.length) {
      const timer = setTimeout(() => {
        setDisplayedText(prev => prev + text[currentIndex]);
        setCurrentIndex(prev => prev + 1);
      }, 25); // Speed of typing
      return () => clearTimeout(timer);
    } else if (onComplete) {
      onComplete();
    }
  }, [currentIndex, text, onComplete]);

  useEffect(() => {
    setDisplayedText('');
    setCurrentIndex(0);
  }, [text]);

  return (
    <span className={className}>
      {displayedText}
      {currentIndex < text.length && (
        <motion.span
          animate={{ opacity: [1, 0] }}
          transition={{ duration: 0.5, repeat: Infinity }}
          className="inline-block w-0.5 h-5 bg-violet-400 ml-0.5 align-middle"
        />
      )}
    </span>
  );
}

// View states for clean state machine
const VIEW = {
  QUESTION: 'question',
  TRANSITION: 'transition'
};

export default function Assessment({
  question,
  questionNumber,
  totalQuestions,
  onAnswer,
  isLoading,
  isAnalyzing = false,
  mode = 'overall'
}) {
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [textAnswer, setTextAnswer] = useState('');
  const [submittedAnswerText, setSubmittedAnswerText] = useState('');
  const [view, setView] = useState(VIEW.QUESTION);
  const [lastQuestionId, setLastQuestionId] = useState(null);
  const [headerTyped, setHeaderTyped] = useState(false);

  const isMultipleChoice = question?.type === 'multiple-choice';
  const options = isMultipleChoice ? Object.entries(question?.options || {}) : [];
  const isInTransition = view === VIEW.TRANSITION;

  // Track screen view on mount
  useEffect(() => {
    Analytics.screenView('assessment');
  }, []);

  // Handle keyboard shortcuts
  const handleKeyDown = useCallback((e) => {
    if (isLoading || isAnalyzing || isInTransition || !isMultipleChoice) return;

    const key = e.key.toLowerCase();
    const optionKeys = options.map(([k]) => k.toLowerCase());

    if (optionKeys.includes(key)) {
      e.preventDefault();
      setSelectedAnswer(key);
    }

    if (e.key === 'Enter' && selectedAnswer) {
      e.preventDefault();
      handleSubmit();
    }
  }, [isLoading, isAnalyzing, isInTransition, isMultipleChoice, options, selectedAnswer]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Handle question transitions
  useEffect(() => {
    if (!question?.id) return;

    // New question arrived
    if (question.id !== lastQuestionId) {
      // Reset answer states for new question
      setSelectedAnswer(null);
      setTextAnswer('');
      setHeaderTyped(false);

      // If we're in transition, handle the animation flow
      if (view === VIEW.TRANSITION) {
        // If question has header, wait for typewriter
        // If no header, show question after brief delay
        if (!question.header) {
          const timer = setTimeout(() => {
            setLastQuestionId(question.id);
            setView(VIEW.QUESTION);
          }, 800);
          return () => clearTimeout(timer);
        }
        // With header: typewriter callback will handle transition
      } else {
        // First load - show question immediately
        setLastQuestionId(question.id);
      }
    }
  }, [question?.id, question?.header, lastQuestionId, view]);

  if (isAnalyzing) {
    return <AnalyzingAnimation />;
  }

  if (!question || !question.text) {
    return (
      <div className="min-h-screen bg-[#09090b] flex items-center justify-center px-4">
        <div className="text-center">
          <div className="animate-spin h-12 w-12 border-4 border-violet-500 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-neutral-400 text-sm">Loading question...</p>
        </div>
      </div>
    );
  }

  const progress = (questionNumber / totalQuestions) * 100;

  const handleSubmit = () => {
    if (isMultipleChoice && selectedAnswer) {
      // Store the selected answer text for the transition screen
      const selectedOption = question?.options?.[selectedAnswer];
      setSubmittedAnswerText(selectedOption?.text || '');
      setView(VIEW.TRANSITION);
      onAnswer(selectedAnswer);
    } else if (!isMultipleChoice && textAnswer.trim()) {
      setSubmittedAnswerText(textAnswer.trim());
      setView(VIEW.TRANSITION);
      onAnswer(textAnswer.trim());
    }
  };

  // Handle transition from typewriter to question
  const handleHeaderTypingComplete = () => {
    setHeaderTyped(true);
    // Short pause after typing, then show full question
    setTimeout(() => {
      setLastQuestionId(question?.id);
      setView(VIEW.QUESTION);
    }, 500);
  };

  const canSubmit = isMultipleChoice ? selectedAnswer !== null : textAnswer.trim().length > 0;

  return (
    <div className="min-h-screen bg-[#09090b] text-white overflow-hidden relative flex flex-col">
      {/* Subtle background gradient */}
      <div className="absolute inset-0">
        <div
          className="absolute inset-0 opacity-40"
          style={{
            background: `radial-gradient(ellipse at 30% 20%, ${modeColors[mode]}20 0%, transparent 50%)`
          }}
        />
      </div>

      {/* Progress bar */}
      <div className="relative z-20 w-full h-1.5 bg-neutral-800">
        <motion.div
          className="h-full rounded-r-full"
          style={{ background: 'linear-gradient(90deg, #fb923c, #ec4899, #a78bfa)' }}
          initial={{ width: `${((questionNumber - 1) / totalQuestions) * 100}%` }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>

      {/* Header - mode info hidden on mobile to avoid Start Over button overlap */}
      <div className="relative z-10 px-4 md:px-6 py-3 md:py-4 flex items-center justify-end border-b border-neutral-800/50">
        <div className="flex items-center gap-2 md:gap-3">
          {/* Mode info - hidden on mobile */}
          <div
            className="hidden md:flex w-8 h-8 rounded-lg items-center justify-center"
            style={{ backgroundColor: `${modeColors[mode]}20` }}
          >
            <ModeIcon mode={mode} />
          </div>
          <span className="hidden md:inline text-neutral-400 text-sm font-medium">{modeLabels[mode]}</span>
          <span className="hidden md:inline text-neutral-600 mx-2">•</span>
          {/* Question counter - always visible */}
          <span className="text-white font-semibold">{Math.min(questionNumber, totalQuestions)}</span>
          <span className="text-neutral-500">/</span>
          <span className="text-neutral-400">{totalQuestions}</span>
        </div>
      </div>

      {/* Main content */}
      <div className="relative z-10 flex-1 flex flex-col items-center justify-center px-4 md:px-6 py-4 md:py-8">
        <AnimatePresence mode="wait">
          {/* TRANSITION SCREEN - Shows answer + typewriter header */}
          {isInTransition ? (
            <motion.div
              key="transition"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0, y: -30 }}
              transition={{ duration: 0.4 }}
              className="w-full max-w-2xl text-center"
            >
              {/* "Interesting choice" label */}
              <motion.p
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-neutral-500 text-sm md:text-base mb-4"
              >
                Interesting choice.
              </motion.p>

              {/* User's selected answer */}
              <motion.p
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="text-lg md:text-xl lg:text-2xl text-white font-medium mb-8 leading-relaxed"
              >
                "{submittedAnswerText}"
              </motion.p>

              {/* Typewriter header - appears when new question arrives */}
              {question?.header && question.id !== lastQuestionId ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.2 }}
                  className="min-h-[60px]"
                >
                  <span className="text-neutral-400 text-base md:text-lg italic">
                    <TypewriterText
                      text={question.header}
                      onComplete={handleHeaderTypingComplete}
                    />
                  </span>
                </motion.div>
              ) : (
                /* Loading dots while waiting for API */
                <motion.div
                  className="flex justify-center items-center gap-2 min-h-[60px]"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.3 }}
                >
                  {[0, 1, 2].map((i) => (
                    <motion.div
                      key={i}
                      className="w-2 h-2 bg-violet-400/60 rounded-full"
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
                    />
                  ))}
                </motion.div>
              )}
            </motion.div>
          ) : (
            /* FULL QUESTION VIEW */
            <motion.div
              key={`question-${question.id}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4 }}
              className="w-full max-w-2xl"
            >
              {/* Reaction header badge */}
              {question.header && (
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="mb-4 md:mb-6 mt-2 md:mt-0"
                >
                  <span className="inline-block px-3 py-1.5 md:px-4 md:py-2 bg-neutral-800/80 border border-neutral-700 rounded-full text-xs md:text-sm text-neutral-300">
                    {question.header}
                  </span>
                </motion.div>
              )}

              {/* Question text */}
              <motion.h1
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="text-xl md:text-2xl lg:text-3xl font-bold leading-tight mb-6 md:mb-12 text-white"
              >
                {question.text}
              </motion.h1>

              {/* Answer options */}
              {isMultipleChoice ? (
                <div className="space-y-3 md:space-y-4" role="listbox" aria-label="Answer options">
                  {options.map(([key, option], index) => (
                    <motion.button
                      key={key}
                      initial={{ opacity: 0, x: -30 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.4 + index * 0.1 }}
                      onClick={() => setSelectedAnswer(key)}
                      disabled={isLoading}
                      role="option"
                      aria-selected={selectedAnswer === key}
                      className={`
                        w-full group relative text-left p-4 md:p-5 rounded-xl md:rounded-2xl border transition-all duration-200
                        focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-400 focus-visible:ring-offset-2 focus-visible:ring-offset-[#09090b]
                        ${selectedAnswer === key
                          ? 'bg-violet-500/15 border-violet-400/50'
                          : 'bg-neutral-800/50 border-neutral-700 hover:bg-neutral-800 hover:border-neutral-600'
                        }
                        ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                      `}
                    >
                      <div className="flex items-center gap-3 md:gap-4">
                        {/* Key indicator */}
                        <div className={`
                          w-8 h-8 md:w-10 md:h-10 rounded-lg md:rounded-xl flex items-center justify-center text-xs md:text-sm font-bold transition-colors flex-shrink-0
                          ${selectedAnswer === key
                            ? 'bg-violet-500 text-white'
                            : 'bg-neutral-700 text-neutral-300 group-hover:bg-neutral-600'
                          }
                        `}>
                          {key.toUpperCase()}
                        </div>

                        {/* Option text */}
                        <span className={`
                          flex-1 text-sm md:text-lg transition-colors leading-snug
                          ${selectedAnswer === key
                            ? 'text-white'
                            : 'text-neutral-200 group-hover:text-white'
                          }
                        `}>
                          {option.text}
                        </span>

                        {/* Selection indicator - hidden on mobile */}
                        <div
                          className="hidden md:flex w-6 h-6 rounded-full border-2 items-center justify-center transition-colors flex-shrink-0"
                          style={{
                            borderColor: selectedAnswer === key ? '#a78bfa' : '#525252',
                            background: selectedAnswer === key ? '#a78bfa' : 'transparent'
                          }}
                        >
                          {selectedAnswer === key && (
                            <motion.svg
                              width="12" height="12" viewBox="0 0 12 12" fill="none"
                              initial={{ scale: 0 }}
                              animate={{ scale: 1 }}
                            >
                              <path d="M2 6 L5 9 L10 3" stroke="white" strokeWidth="2" strokeLinecap="round" />
                            </motion.svg>
                          )}
                        </div>
                      </div>
                    </motion.button>
                  ))}
                </div>
              ) : !isMultipleChoice ? (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className="w-full"
                >
                  <textarea
                    value={textAnswer}
                    onChange={(e) => setTextAnswer(e.target.value)}
                    placeholder={question.placeholder || 'Share your thoughts...'}
                    disabled={isLoading}
                    className="w-full p-4 md:p-5 bg-neutral-800/50 border border-neutral-700 rounded-xl md:rounded-2xl text-white placeholder-neutral-500 focus:outline-none focus:border-violet-500 transition-colors min-h-28 md:min-h-32 resize-none text-base md:text-lg"
                  />
                </motion.div>
              ) : null}

              {/* Submit button */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
                className="mt-6 md:mt-8 flex justify-center w-full"
              >
                <motion.button
                  onClick={handleSubmit}
                  disabled={!canSubmit || isLoading}
                  whileHover={canSubmit && !isLoading ? { scale: 1.03 } : {}}
                  whileTap={canSubmit && !isLoading ? { scale: 0.97 } : {}}
                  className={`
                    w-full md:w-auto px-6 md:px-8 py-3 md:py-4 rounded-xl font-medium text-base md:text-lg transition-all flex items-center justify-center gap-2
                    focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-400 focus-visible:ring-offset-2 focus-visible:ring-offset-[#09090b]
                    ${canSubmit && !isLoading
                      ? 'bg-gradient-to-r from-violet-500 to-pink-500 text-white shadow-lg'
                      : 'bg-neutral-700 text-neutral-500 cursor-not-allowed'
                    }
                  `}
                >
                  {isLoading ? (
                    <>
                      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Next question...
                    </>
                  ) : (
                    <>
                      Continue
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                    </>
                  )}
                </motion.button>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>


      {/* Keyboard shortcuts - only on large screens */}
      {isMultipleChoice && !isInTransition && (
        <div className="hidden lg:flex fixed bottom-3 right-4 items-center gap-1.5 text-neutral-500 text-[10px]">
          <kbd className="px-1.5 py-0.5 bg-neutral-800 rounded border border-neutral-700 text-neutral-400 font-mono text-[10px]">A</kbd>
          <kbd className="px-1.5 py-0.5 bg-neutral-800 rounded border border-neutral-700 text-neutral-400 font-mono text-[10px]">B</kbd>
          <kbd className="px-1.5 py-0.5 bg-neutral-800 rounded border border-neutral-700 text-neutral-400 font-mono text-[10px]">C</kbd>
          <span className="ml-0.5">to answer</span>
        </div>
      )}
    </div>
  );
}
