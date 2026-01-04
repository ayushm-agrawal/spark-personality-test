import { motion } from 'framer-motion';

const modeIcons = {
  quick: '⚡',
  standard: '🎯',
  deep: '🔮'
};

const modeColors = {
  quick: 'from-amber-500 to-orange-600',
  standard: 'from-blue-500 to-purple-600',
  deep: 'from-purple-500 to-pink-600'
};

export default function ModeSelection({ onSelectMode }) {
  const modes = [
    {
      id: 'quick',
      name: 'Quick Mode',
      time: '2 min',
      questions: 6,
      description: 'Perfect for hackathons. Fast, focused assessment on collaboration under pressure.'
    },
    {
      id: 'standard',
      name: 'Standard Mode',
      time: '5 min',
      questions: 10,
      description: 'Balanced assessment with personalized questions based on your interests.'
    },
    {
      id: 'deep',
      name: 'Deep Mode',
      time: '10 min',
      questions: 15,
      description: 'Comprehensive profile with detailed trait analysis and nuanced insights.'
    }
  ];

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center mb-12"
      >
        <h1 className="text-4xl md:text-5xl font-bold mb-4 gradient-text">
          Discover Your Team Archetype
        </h1>
        <p className="text-gray-400 text-lg max-w-xl mx-auto">
          Find out how you collaborate, lead, and thrive in team environments
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3, duration: 0.6 }}
        className="text-center mb-8"
      >
        <h2 className="text-2xl font-semibold text-white mb-2">
          How deep do you want to go?
        </h2>
        <p className="text-gray-500">Choose your assessment depth</p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl w-full">
        {modes.map((mode, index) => (
          <motion.button
            key={mode.id}
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 + index * 0.1, duration: 0.5 }}
            whileHover={{ scale: 1.03, y: -5 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onSelectMode(mode.id)}
            className="glass-card p-6 text-left cursor-pointer group hover:border-purple-500/50 transition-all"
          >
            <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${modeColors[mode.id]} flex items-center justify-center text-2xl mb-4 group-hover:scale-110 transition-transform`}>
              {modeIcons[mode.id]}
            </div>

            <h3 className="text-xl font-semibold text-white mb-1">
              {mode.name}
            </h3>

            <div className="flex items-center gap-3 mb-3 text-sm">
              <span className="px-2 py-1 rounded-full bg-white/10 text-gray-300">
                {mode.time}
              </span>
              <span className="px-2 py-1 rounded-full bg-white/10 text-gray-300">
                {mode.questions} questions
              </span>
            </div>

            <p className="text-gray-400 text-sm leading-relaxed">
              {mode.description}
            </p>

            <div className="mt-4 flex items-center text-purple-400 text-sm font-medium group-hover:text-purple-300">
              Start Assessment
              <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </div>
          </motion.button>
        ))}
      </div>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="mt-12 text-gray-500 text-sm text-center"
      >
        Powered by Big Five personality research
      </motion.p>
    </div>
  );
}
