import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const SLIDES = [
  {
    id: 'welcome',
    icon: '👋',
    headline: 'Welcome to Ception',
    description: 'Discover how your personality shows up in teams. Quick assessments, real insights, better collaboration.',
    buttonText: 'Show me how',
  },
  {
    id: 'modes',
    icon: '🎯',
    headline: 'Three ways to explore',
    description: null, // Custom content for this slide
    buttonText: 'Next',
  },
  {
    id: 'profile',
    icon: '📈',
    headline: 'Your profile grows with you',
    description: 'Each test refines your archetype. Take 2-3 tests to get a stable, reliable profile. Your results combine into one holistic view.',
    buttonText: 'Next',
  },
  {
    id: 'signin',
    icon: '☁️',
    headline: 'Sign in to keep your progress',
    description: "Without signing in, your profile lives on this device only. Sign in to sync across devices and never lose your insights.",
    buttonText: 'Next',
  },
  {
    id: 'navigation',
    icon: '👆',
    headline: 'Your profile lives here',
    description: 'See the highlighted button above? Tap it anytime to view your archetypes, earned badges, and deep insights.',
    buttonText: 'Get Started',
  },
];

// Mode icons for slide 2
const ModesList = () => (
  <div className="space-y-3 text-left">
    <div className="flex items-start gap-3">
      <span className="text-xl">⚡</span>
      <div>
        <span className="text-white font-medium">Under Pressure</span>
        <span className="text-neutral-400 text-sm ml-2">2 min</span>
        <p className="text-neutral-400 text-sm">How you collaborate when stakes are high</p>
      </div>
    </div>
    <div className="flex items-start gap-3">
      <span className="text-xl">📊</span>
      <div>
        <span className="text-white font-medium">Full Profile</span>
        <span className="text-neutral-400 text-sm ml-2">4 min</span>
        <p className="text-neutral-400 text-sm">Your complete personality across all traits</p>
      </div>
    </div>
    <div className="flex items-start gap-3">
      <span className="text-xl">🔍</span>
      <div>
        <span className="text-white font-medium">Deep Dive</span>
        <span className="text-neutral-400 text-sm ml-2">3 min</span>
        <p className="text-neutral-400 text-sm">How you show up in specific areas</p>
      </div>
    </div>
  </div>
);

export default function TutorialModal({ onComplete, onSlideView }) {
  const [currentSlide, setCurrentSlide] = useState(0);
  const modalRef = useRef(null);
  const firstFocusableRef = useRef(null);

  // Track slide views
  useEffect(() => {
    if (onSlideView) {
      onSlideView(currentSlide, SLIDES[currentSlide].id);
    }
  }, [currentSlide, onSlideView]);

  // Trap focus in modal
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        handleSkip();
      }

      // Focus trap
      if (e.key === 'Tab' && modalRef.current) {
        const focusableElements = modalRef.current.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (e.shiftKey && document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    // Focus first element on mount
    if (firstFocusableRef.current) {
      firstFocusableRef.current.focus();
    }

    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleNext = () => {
    if (currentSlide < SLIDES.length - 1) {
      setCurrentSlide(currentSlide + 1);
    } else {
      onComplete(false); // completed = false means they finished all slides
    }
  };

  const handleSkip = () => {
    onComplete(true, currentSlide); // skipped = true, include slide number
  };

  const slide = SLIDES[currentSlide];
  const isLastSlide = currentSlide === SLIDES.length - 1;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="tutorial-title"
    >
      <motion.div
        ref={modalRef}
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className="relative w-full max-w-md bg-neutral-900 rounded-2xl border border-neutral-800 shadow-2xl overflow-hidden"
      >
        {/* Skip button */}
        <button
          ref={firstFocusableRef}
          onClick={handleSkip}
          className="absolute top-4 right-4 text-neutral-400 hover:text-white text-sm transition-colors z-10"
        >
          Skip
        </button>

        {/* Slide content */}
        <div className="px-8 pt-12 pb-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentSlide}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
              className="text-center"
            >
              {/* Icon */}
              <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-violet-500/20 to-purple-500/20 flex items-center justify-center">
                <span className="text-4xl">{slide.icon}</span>
              </div>

              {/* Headline */}
              <h2 id="tutorial-title" className="text-xl font-bold text-white mb-3">
                {slide.headline}
              </h2>

              {/* Description */}
              {slide.id === 'modes' ? (
                <ModesList />
              ) : (
                <p className="text-neutral-400 text-sm leading-relaxed">
                  {slide.description}
                </p>
              )}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Progress dots and button */}
        <div className="px-8 pb-8">
          {/* Progress dots */}
          <div className="flex justify-center gap-1 mb-6" role="tablist" aria-label="Tutorial progress">
            {SLIDES.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentSlide(index)}
                className="p-2 -m-1"
                role="tab"
                aria-selected={index === currentSlide}
                aria-label={`Step ${index + 1} of ${SLIDES.length}`}
              >
                <div
                  className={`h-2 rounded-full transition-all ${
                    index === currentSlide
                      ? 'bg-violet-500 w-6'
                      : index < currentSlide
                      ? 'bg-violet-500/50 w-2'
                      : 'bg-neutral-500 w-2'
                  }`}
                />
              </button>
            ))}
          </div>

          {/* Action button */}
          <button
            onClick={handleNext}
            className="w-full py-3 px-6 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 text-white font-medium hover:from-violet-500 hover:to-purple-500 transition-all"
          >
            {slide.buttonText}
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}
