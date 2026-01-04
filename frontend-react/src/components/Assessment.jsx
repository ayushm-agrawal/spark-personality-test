import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// Analyzing animation shown while calculating personality results
function AnalyzingAnimation() {
  const traits = ['Openness', 'Conscientiousness', 'Extraversion', 'Agreeableness', 'Emotional Stability'];
  const [currentTrait, setCurrentTrait] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTrait((prev) => (prev + 1) % traits.length);
    }, 800);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        className="text-center"
      >
        {/* Animated brain/personality icon */}
        <div className="relative w-32 h-32 mx-auto mb-8">
          <motion.div
            className="absolute inset-0 rounded-full bg-gradient-to-r from-purple-500 to-pink-500"
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.5, 0.8, 0.5],
            }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          <motion.div
            className="absolute inset-4 rounded-full bg-gradient-to-r from-blue-500 to-purple-500"
            animate={{
              scale: [1.1, 1, 1.1],
              opacity: [0.6, 0.9, 0.6],
            }}
            transition={{ duration: 2, repeat: Infinity, delay: 0.3 }}
          />
          <motion.div
            className="absolute inset-8 rounded-full bg-gradient-to-r from-pink-500 to-orange-500"
            animate={{
              scale: [1, 1.15, 1],
              opacity: [0.7, 1, 0.7],
            }}
            transition={{ duration: 2, repeat: Infinity, delay: 0.6 }}
          />
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-4xl">🧠</span>
          </div>
        </div>

        <motion.h2
          className="text-2xl md:text-3xl font-bold text-white mb-4"
          animate={{ opacity: [0.7, 1, 0.7] }}
          transition={{ duration: 1.5, repeat: Infinity }}
        >
          Analyzing Your Personality
        </motion.h2>

        <div className="h-8 mb-6">
          <AnimatePresence mode="wait">
            <motion.p
              key={currentTrait}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="text-purple-400 text-lg"
            >
              Evaluating {traits[currentTrait]}...
            </motion.p>
          </AnimatePresence>
        </div>

        {/* Progress dots */}
        <div className="flex gap-2 justify-center">
          {traits.map((_, i) => (
            <motion.div
              key={i}
              className={`w-3 h-3 rounded-full ${i <= currentTrait ? 'bg-purple-500' : 'bg-gray-700'}`}
              animate={i === currentTrait ? { scale: [1, 1.3, 1] } : {}}
              transition={{ duration: 0.5 }}
            />
          ))}
        </div>

        <p className="text-gray-500 mt-8 text-sm">
          Crafting your unique archetype profile...
        </p>
      </motion.div>
    </div>
  );
}

export default function Assessment({
  question,
  questionNumber,
  totalQuestions,
  onAnswer,
  isLoading,
  isAnalyzing = false
}) {
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [textAnswer, setTextAnswer] = useState('');

  const isMultipleChoice = question?.type === 'multiple-choice';
  const options = isMultipleChoice ? Object.entries(question?.options || {}) : [];

  // Handle keyboard shortcuts for options (A, B, C, etc.)
  const handleKeyDown = useCallback((e) => {
    if (isLoading || isAnalyzing || !isMultipleChoice) return;

    const key = e.key.toLowerCase();
    const optionKeys = options.map(([k]) => k.toLowerCase());

    if (optionKeys.includes(key)) {
      e.preventDefault();
      setSelectedAnswer(key);
    }

    // Enter to submit
    if (e.key === 'Enter' && selectedAnswer) {
      e.preventDefault();
      onAnswer(selectedAnswer);
    }
  }, [isLoading, isAnalyzing, isMultipleChoice, options, selectedAnswer, onAnswer]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Reset selection when question changes
  useEffect(() => {
    setSelectedAnswer(null);
    setTextAnswer('');
  }, [question?.id]);

  // Show analyzing animation when calculating results
  if (isAnalyzing) {
    return <AnalyzingAnimation />;
  }

  if (!question) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-12 w-12 border-4 border-purple-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  const progress = (questionNumber / totalQuestions) * 100;

  const handleSubmit = () => {
    if (isMultipleChoice && selectedAnswer) {
      onAnswer(selectedAnswer);
    } else if (!isMultipleChoice && textAnswer.trim()) {
      onAnswer(textAnswer.trim());
    }
  };

  const canSubmit = isMultipleChoice
    ? selectedAnswer !== null
    : textAnswer.trim().length > 0;

  return (
    <div className="min-h-screen flex flex-col px-4 py-8">
      {/* Progress bar */}
      <div className="fixed top-0 left-0 right-0 h-1 bg-gray-800 z-50">
        <motion.div
          className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>

      {/* Question counter */}
      <div className="text-center mb-4 pt-4">
        <span className="text-gray-500 text-sm">
          Question {questionNumber} of {totalQuestions}
        </span>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center max-w-2xl mx-auto w-full">
        <AnimatePresence mode="wait">
          <motion.div
            key={question.id}
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.3 }}
            className="w-full"
          >
            {/* Header/Reaction */}
            {question.header && (
              <motion.p
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="text-amber-400 text-center text-sm md:text-base italic mb-6"
              >
                {question.header}
              </motion.p>
            )}

            {/* Question text */}
            <motion.h2
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="text-2xl md:text-3xl font-semibold text-white text-center mb-8 leading-relaxed"
            >
              {question.text}
            </motion.h2>

            {/* Answer options */}
            {isMultipleChoice ? (
              <div className="space-y-3">
                {options.map(([key, option], index) => (
                  <motion.button
                    key={key}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 + index * 0.1 }}
                    onClick={() => setSelectedAnswer(key)}
                    disabled={isLoading}
                    className={`
                      w-full p-4 md:p-5 rounded-xl text-left transition-all
                      ${selectedAnswer === key
                        ? 'bg-purple-600 border-2 border-purple-400 text-white'
                        : 'glass-card hover:border-purple-500/50 text-gray-200'
                      }
                      ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                    `}
                  >
                    <div className="flex items-center gap-4">
                      <span className={`
                        w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                        ${selectedAnswer === key
                          ? 'bg-white text-purple-600'
                          : 'bg-gray-700 text-gray-300'
                        }
                      `}>
                        {key.toUpperCase()}
                      </span>
                      <span className="flex-1 text-base md:text-lg">
                        {option.text}
                      </span>
                    </div>
                  </motion.button>
                ))}
              </div>
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                <textarea
                  value={textAnswer}
                  onChange={(e) => setTextAnswer(e.target.value)}
                  placeholder={question.placeholder || 'Share your thoughts...'}
                  disabled={isLoading}
                  className="w-full p-4 bg-gray-800/50 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors min-h-32 resize-none"
                />
              </motion.div>
            )}

            {/* Submit button */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6 }}
              className="mt-8 flex justify-center"
            >
              <button
                onClick={handleSubmit}
                disabled={!canSubmit || isLoading}
                className={`
                  px-8 py-4 rounded-xl font-semibold text-lg transition-all flex items-center gap-2
                  ${canSubmit && !isLoading
                    ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-500 hover:to-pink-500 hover:scale-105'
                    : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                  }
                `}
              >
                {isLoading ? (
                  <>
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Thinking...
                  </>
                ) : (
                  <>
                    Next
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </>
                )}
              </button>
            </motion.div>

            {/* Keyboard hints */}
            {isMultipleChoice && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.8 }}
                className="text-center text-gray-600 text-xs mt-6"
              >
                Press <kbd className="px-1.5 py-0.5 bg-gray-800 rounded text-gray-400">A</kbd>{' '}
                <kbd className="px-1.5 py-0.5 bg-gray-800 rounded text-gray-400">B</kbd>{' '}
                <kbd className="px-1.5 py-0.5 bg-gray-800 rounded text-gray-400">C</kbd> to select •{' '}
                <kbd className="px-1.5 py-0.5 bg-gray-800 rounded text-gray-400">Enter</kbd> to continue
              </motion.p>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
