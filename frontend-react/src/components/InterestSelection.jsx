import { useState } from 'react';
import { motion } from 'framer-motion';

const defaultInterests = [
  { id: 'fantasy', label: 'Fantasy', emoji: '🧙‍♂️', description: 'Magical quests & worlds' },
  { id: 'scifi', label: 'Sci-Fi', emoji: '🚀', description: 'Futuristic adventures' },
  { id: 'gaming', label: 'Gaming', emoji: '🎮', description: 'Video games & esports' },
  { id: 'tech', label: 'Technology', emoji: '💻', description: 'Innovation & coding' },
  { id: 'business', label: 'Business', emoji: '📈', description: 'Entrepreneurship' },
  { id: 'art', label: 'Art & Design', emoji: '🎨', description: 'Creative expression' },
  { id: 'music', label: 'Music', emoji: '🎵', description: 'Rhythm & melody' },
  { id: 'sports', label: 'Sports', emoji: '⚽', description: 'Athletic pursuits' },
  { id: 'travel', label: 'Travel', emoji: '✈️', description: 'Exploration & culture' },
  { id: 'popculture', label: 'Pop Culture', emoji: '🎬', description: 'Movies, TV & anime' },
];

export default function InterestSelection({ onSubmit, isLoading }) {
  const [selected, setSelected] = useState([]);
  const [customInterest, setCustomInterest] = useState('');

  const toggleInterest = (id) => {
    if (selected.includes(id)) {
      setSelected(selected.filter(i => i !== id));
    } else if (selected.length < 3) {
      setSelected([...selected, id]);
    }
  };

  const handleSubmit = () => {
    const interests = selected.map(id => {
      const interest = defaultInterests.find(i => i.id === id);
      return interest ? `${interest.label} (${interest.description})` : id;
    });

    if (customInterest.trim()) {
      interests.push(customInterest.trim());
    }

    if (interests.length > 0) {
      onSubmit(interests);
    }
  };

  const canSubmit = selected.length > 0 || customInterest.trim();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <h1 className="text-3xl md:text-4xl font-bold mb-3 text-white">
          What are you into?
        </h1>
        <p className="text-gray-400 max-w-md mx-auto">
          Pick up to 3 interests. We'll personalize your questions around what you love.
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-2 md:grid-cols-5 gap-3 max-w-3xl w-full mb-8"
      >
        {defaultInterests.map((interest, index) => {
          const isSelected = selected.includes(interest.id);
          const isDisabled = !isSelected && selected.length >= 3;

          return (
            <motion.button
              key={interest.id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 + index * 0.03 }}
              whileHover={!isDisabled ? { scale: 1.05 } : {}}
              whileTap={!isDisabled ? { scale: 0.95 } : {}}
              onClick={() => !isDisabled && toggleInterest(interest.id)}
              disabled={isDisabled}
              className={`
                p-4 rounded-xl border-2 transition-all text-center
                ${isSelected
                  ? 'border-purple-500 bg-purple-500/20 text-white'
                  : isDisabled
                    ? 'border-gray-700 bg-gray-800/50 text-gray-600 cursor-not-allowed'
                    : 'border-gray-700 bg-gray-800/30 text-gray-300 hover:border-purple-400/50'
                }
              `}
            >
              <span className="text-2xl block mb-1">{interest.emoji}</span>
              <span className="text-sm font-medium">{interest.label}</span>
            </motion.button>
          );
        })}
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="w-full max-w-md mb-8"
      >
        <label className="block text-gray-400 text-sm mb-2">
          Or add something specific:
        </label>
        <input
          type="text"
          value={customInterest}
          onChange={(e) => setCustomInterest(e.target.value)}
          placeholder="e.g., I love building AI products"
          className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
        />
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="flex flex-col items-center gap-4"
      >
        <button
          onClick={handleSubmit}
          disabled={!canSubmit || isLoading}
          className={`
            px-8 py-4 rounded-xl font-semibold text-lg transition-all
            ${canSubmit && !isLoading
              ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-500 hover:to-pink-500 hover:scale-105'
              : 'bg-gray-700 text-gray-500 cursor-not-allowed'
            }
          `}
        >
          {isLoading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Loading...
            </span>
          ) : (
            'Continue'
          )}
        </button>

        {selected.length > 0 && (
          <p className="text-gray-500 text-sm">
            {3 - selected.length} selection{3 - selected.length !== 1 ? 's' : ''} remaining
          </p>
        )}
      </motion.div>
    </div>
  );
}
