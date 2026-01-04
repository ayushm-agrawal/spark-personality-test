import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';

// Fallback life contexts if backend doesn't provide them
const fallbackLifeContexts = [
  { id: 'work_career', label: 'Work & Career', icon: '💼', description: 'Deadlines, feedback, and ambition' },
  { id: 'creative_projects', label: 'Creative Projects', icon: '🎨', description: 'Creating, iterating, and criticism' },
  { id: 'learning_growth', label: 'Learning & Growth', icon: '📚', description: 'New skills and knowledge' },
  { id: 'relationships', label: 'Relationships & Social', icon: '👥', description: 'Connecting and conflict' },
  { id: 'challenges_adversity', label: 'Challenges & Adversity', icon: '🔥', description: 'When things go wrong' },
  { id: 'personal_time', label: 'Personal Time & Energy', icon: '🌙', description: 'Recharging and boundaries' },
];

export default function InterestSelection({ onSubmit, isLoading, mode, config }) {
  const [selected, setSelected] = useState([]);
  const [customInterest, setCustomInterest] = useState('');

  // Determine which options to show and limits based on config from backend
  const isOptional = config?.optional || mode === 'overall';
  const minRequired = config?.min || 2;
  const maxAllowed = config?.max || 4;

  // Convert backend categories to array format for rendering
  const options = useMemo(() => {
    if (config?.categories) {
      // Backend returns categories as object: { id: { label, description, icon } }
      return Object.entries(config.categories).map(([id, data]) => ({
        id,
        label: data.label,
        icon: data.icon,
        description: data.description,
        color: '#a78bfa' // default purple
      }));
    }
    return fallbackLifeContexts;
  }, [config?.categories]);

  const toggleInterest = (id) => {
    if (selected.includes(id)) {
      setSelected(selected.filter(i => i !== id));
    } else if (selected.length < maxAllowed) {
      setSelected([...selected, id]);
    }
  };

  const handleSubmit = () => {
    const selectedContexts = selected.map(id => {
      const option = options.find(i => i.id === id);
      return option ? option.label : id;
    });

    if (customInterest.trim()) {
      selectedContexts.push(customInterest.trim());
    }

    onSubmit(selectedContexts);
  };

  const handleSkip = () => {
    onSubmit([]);
  };

  const canSubmit = isOptional || selected.length >= minRequired || customInterest.trim();
  const showCustomInput = mode === 'deep_dive'; // Only show custom input for deep_dive mode

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <h1 className="text-3xl md:text-4xl font-bold mb-3 text-white">
          What should we explore?
        </h1>
        <p className="text-gray-400 max-w-md mx-auto">
          {isOptional
            ? `Pick ${minRequired}-${maxAllowed} life contexts for a focused assessment, or skip for a balanced view.`
            : `Pick ${minRequired}-${maxAllowed} life contexts. Your archetype will reflect how you show up in these areas.`
          }
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-2 md:grid-cols-3 gap-3 max-w-3xl w-full mb-8"
      >
        {options.map((option, index) => {
          const isSelected = selected.includes(option.id);
          const isDisabled = !isSelected && selected.length >= maxAllowed;

          return (
            <motion.button
              key={option.id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 + index * 0.03 }}
              whileHover={!isDisabled ? { scale: 1.05 } : {}}
              whileTap={!isDisabled ? { scale: 0.95 } : {}}
              onClick={() => !isDisabled && toggleInterest(option.id)}
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
              style={isSelected ? { borderColor: option.color, backgroundColor: `${option.color}20` } : {}}
            >
              <span className="text-2xl block mb-1">{option.icon}</span>
              <span className="text-sm font-medium block">{option.label}</span>
              {option.examples && (
                <span className="text-xs text-gray-500 block mt-1">
                  {option.examples.slice(0, 2).join(', ')}
                </span>
              )}
              {option.description && (
                <span className="text-xs text-gray-500 block mt-1">
                  {option.description}
                </span>
              )}
            </motion.button>
          );
        })}
      </motion.div>

      {showCustomInput && (
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
            placeholder="e.g., I'm really into building AI products"
            className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
          />
        </motion.div>
      )}

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

        {isOptional && (
          <button
            onClick={handleSkip}
            disabled={isLoading}
            className="text-gray-400 hover:text-white transition-colors text-sm"
          >
            Skip - assess me across all areas →
          </button>
        )}

        {!isOptional && selected.length > 0 && selected.length < minRequired && (
          <p className="text-gray-500 text-sm">
            Select {minRequired - selected.length} more context{minRequired - selected.length !== 1 ? 's' : ''}
          </p>
        )}

        {selected.length >= minRequired && selected.length < maxAllowed && (
          <p className="text-gray-500 text-sm">
            {maxAllowed - selected.length} selection{maxAllowed - selected.length !== 1 ? 's' : ''} remaining
          </p>
        )}
      </motion.div>
    </div>
  );
}
