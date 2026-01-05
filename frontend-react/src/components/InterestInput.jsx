import { useState } from 'react';
import { motion } from 'framer-motion';

const EXAMPLE_INTERESTS = [
  { label: 'Work', emoji: '💼' },
  { label: 'Relationships', emoji: '💕' },
  { label: 'Creative projects', emoji: '🎨' },
  { label: 'Fitness', emoji: '💪' },
  { label: 'Parenting', emoji: '👶' },
  { label: 'Learning', emoji: '📚' },
];

export default function InterestInput({ onSubmit, isLoading }) {
  const [interest, setInterest] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (interest.trim()) {
      onSubmit(interest.trim());
    }
  };

  const handleExampleClick = (example) => {
    setInterest(example);
  };

  return (
    <div className="min-h-screen bg-[#09090b] flex flex-col items-center justify-center px-6 py-12">
      {/* Background gradient */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-violet-500/10 rounded-full blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 w-full max-w-md"
      >
        {/* Header */}
        <div className="text-center mb-8">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", delay: 0.2 }}
            className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-violet-500/20 to-purple-500/20 flex items-center justify-center"
          >
            <span className="text-4xl">🔍</span>
          </motion.div>

          <h1 className="text-3xl font-bold text-white mb-3">
            What area of your life do you want to explore?
          </h1>
          <p className="text-neutral-400">
            We'll discover how your personality shows up specifically in this context.
          </p>
        </div>

        {/* Input form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <input
              type="text"
              value={interest}
              onChange={(e) => setInterest(e.target.value)}
              placeholder="Enter an area of life..."
              className="w-full px-5 py-4 rounded-xl bg-neutral-900 border border-neutral-700 text-white placeholder-neutral-500 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-colors text-lg"
              autoFocus
            />
          </div>

          {/* Example chips */}
          <div>
            <p className="text-sm text-neutral-500 mb-3">Or pick an example:</p>
            <div className="flex flex-wrap gap-2">
              {EXAMPLE_INTERESTS.map((example) => (
                <button
                  key={example.label}
                  type="button"
                  onClick={() => handleExampleClick(example.label)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    interest === example.label
                      ? 'bg-violet-500 text-white'
                      : 'bg-neutral-800 text-neutral-300 hover:bg-neutral-700'
                  }`}
                >
                  {example.emoji} {example.label}
                </button>
              ))}
            </div>
          </div>

          {/* Submit button */}
          <motion.button
            type="submit"
            disabled={!interest.trim() || isLoading}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="w-full py-4 px-6 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 text-white font-medium text-lg disabled:opacity-50 disabled:cursor-not-allowed hover:from-violet-500 hover:to-purple-500 transition-all"
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-3">
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Starting...
              </span>
            ) : (
              "Continue"
            )}
          </motion.button>
        </form>

        {/* Info note */}
        <p className="text-center text-sm text-neutral-600 mt-8">
          You'll answer 10 questions, all focused on {interest || 'your chosen area'}.
        </p>
      </motion.div>
    </div>
  );
}
