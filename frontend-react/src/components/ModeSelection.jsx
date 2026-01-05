import { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Analytics } from '../services/analytics';
import YourArchetypes from './YourArchetypes';

// Custom Mode Icons (SVG) - replaces emojis for better accessibility
const ModeIcons = {
  hackathon: ({ size = 48, color = "#fb923c" }) => (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none">
      <motion.path
        d="M24 8 L26 20 L38 20 L28 28 L32 40 L24 32 L16 40 L20 28 L10 20 L22 20 Z"
        stroke={color}
        strokeWidth="2"
        fill={`${color}20`}
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={{ duration: 0.8 }}
      />
      <motion.circle
        cx="24" cy="24" r="4"
        fill={color}
        initial={{ scale: 0 }}
        animate={{ scale: [0, 1.3, 1] }}
        transition={{ delay: 0.6, duration: 0.4 }}
      />
    </svg>
  ),

  overall: ({ size = 48, color = "#a78bfa" }) => (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none">
      <motion.circle
        cx="24" cy="24" r="16"
        stroke={color}
        strokeWidth="2"
        fill="none"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1 }}
      />
      <motion.circle
        cx="24" cy="24" r="10"
        stroke={color}
        strokeWidth="1.5"
        fill="none"
        opacity="0.6"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 0.8, delay: 0.3 }}
      />
      <motion.circle
        cx="24" cy="24" r="4"
        fill={color}
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.8 }}
      />
    </svg>
  ),

  deep_dive: ({ size = 48, color = "#2dd4bf" }) => (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none">
      <motion.circle
        cx="24" cy="24" r="18"
        stroke={color}
        strokeWidth="1.5"
        strokeDasharray="4 4"
        fill="none"
        initial={{ rotate: 0 }}
        animate={{ rotate: 360 }}
        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
      />
      <motion.path
        d="M24 10 L24 24 L34 30"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        fill="none"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 0.6 }}
      />
      <motion.circle
        cx="24" cy="24" r="3"
        fill={color}
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.5 }}
      />
    </svg>
  )
};

const modes = [
  {
    id: 'hackathon',
    title: 'Team Crunch',
    subtitle: 'How you collaborate under pressure',
    duration: '2 min',
    questions: 6,
    description: 'When deadlines hit and stakes are high, who are you? Perfect for hackathons, startup sprints, and group projects.',
    colors: {
      primary: '#fb923c',
      text: '#fdba74',
      glow: 'rgba(251, 146, 60, 0.15)',
      border: 'rgba(251, 146, 60, 0.3)'
    },
    tagline: 'Pressure reveals character.'
  },
  {
    id: 'overall',
    title: 'Full Profile',
    subtitle: 'Complete Picture',
    duration: '5 min',
    questions: 10,
    description: 'Your personality across all dimensions. The full you.',
    colors: {
      primary: '#a78bfa',
      text: '#c4b5fd',
      glow: 'rgba(167, 139, 250, 0.15)',
      border: 'rgba(167, 139, 250, 0.3)'
    },
    tagline: 'Know thyself.',
    recommended: true
  },
  {
    id: 'deep_dive',
    title: 'Deep Dive',
    subtitle: 'Context Lens',
    duration: '5 min',
    questions: 10,
    description: 'Pick one area of life—work, relationships, anything—and discover how you show up there.',
    colors: {
      primary: '#2dd4bf',
      text: '#5eead4',
      glow: 'rgba(45, 212, 191, 0.15)',
      border: 'rgba(45, 212, 191, 0.3)'
    },
    tagline: 'Same person, different context.'
  }
];

// Mode display labels mapping (internal -> user-facing)
const modeDisplayLabels = {
  hackathon: 'Team Crunch',
  overall: 'Full Profile',
  deep_dive: 'Deep Dive'
};

// Helper to get display label for a mode
const getModeDisplayLabel = (mode, interest = null) => {
  if (mode === 'deep_dive' && interest) {
    // Capitalize first letter of interest
    const capitalizedInterest = interest.charAt(0).toUpperCase() + interest.slice(1);
    return capitalizedInterest;
  }
  return modeDisplayLabels[mode] || mode;
};

// Progress indicator component
function ProgressIndicator({ mode, testsCount, stability, deepDiveInterests = 0 }) {
  const isDeepDive = mode === 'deep_dive';

  if (isDeepDive) {
    if (deepDiveInterests === 0) {
      return <span className="text-neutral-500">Not started</span>;
    }
    return (
      <span className="text-teal-400">
        {deepDiveInterests} area{deepDiveInterests !== 1 ? 's' : ''} explored
      </span>
    );
  }

  if (testsCount === 0) {
    return <span className="text-neutral-500">Not started</span>;
  }

  if (stability === 'stable') {
    return <span className="text-green-400">Stable profile</span>;
  }

  if (stability === 'inconsistent') {
    return <span className="text-orange-400">Results vary</span>;
  }

  if (testsCount >= 3) {
    return <span className="text-green-400">Stable profile</span>;
  }

  if (testsCount === 1) {
    return <span className="text-yellow-400">1 test - take another to confirm</span>;
  }

  if (testsCount === 2) {
    return <span className="text-yellow-400">2 tests - one more for stable profile</span>;
  }

  return <span className="text-neutral-500">{testsCount} tests</span>;
}

export default function ModeSelection({ onSelectMode, userHistory = [], onViewHistory, onViewGallery, holisticProfile = null, userName = null }) {
  const [hoveredMode, setHoveredMode] = useState(null);

  // Determine if this is a returning user
  const isReturningUser = userHistory.length > 0;

  // Calculate test counts per mode from history
  const modeStats = useMemo(() => {
    const stats = {
      hackathon: { count: 0, stability: null },
      overall: { count: 0, stability: null },
      deep_dive: { count: 0, interests: new Set() }
    };

    userHistory.forEach(assessment => {
      const mode = assessment.mode;
      if (stats[mode]) {
        stats[mode].count++;
        if (mode === 'deep_dive' && assessment.modeSpecific?.interest) {
          stats[mode].interests.add(assessment.modeSpecific.interest);
        }
      }
    });

    // Override with holistic profile data if available
    if (holisticProfile?.mode_profiles) {
      Object.entries(holisticProfile.mode_profiles).forEach(([mode, data]) => {
        if (stats[mode]) {
          stats[mode].count = data.tests_included || stats[mode].count;
          stats[mode].stability = data.stability;
        }
      });
    }

    if (holisticProfile?.deep_dive_profiles) {
      stats.deep_dive.interests = new Set(Object.keys(holisticProfile.deep_dive_profiles));
    }

    return stats;
  }, [userHistory, holisticProfile]);

  // Track screen view on mount
  useEffect(() => {
    Analytics.screenView('mode_selection');
  }, []);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === '1') onSelectMode('hackathon');
      if (e.key === '2') onSelectMode('overall');
      if (e.key === '3') onSelectMode('deep_dive');
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onSelectMode]);

  const IconComponent = (id) => {
    const mode = modes.find(m => m.id === id);
    const Icon = ModeIcons[id];
    // Use smaller icons on mobile via CSS classes on the container
    return Icon ? (
      <div className="w-10 h-10 md:w-14 md:h-14 flex items-center justify-center">
        <Icon size={40} color={mode.colors.primary} />
      </div>
    ) : null;
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-white overflow-hidden relative">
      {/* Animated background */}
      <div className="absolute inset-0 overflow-hidden">
        <motion.div
          className="absolute top-1/4 -left-1/4 w-[500px] h-[500px] rounded-full opacity-30"
          style={{ background: 'radial-gradient(circle, rgba(167,139,250,0.2) 0%, transparent 70%)' }}
          animate={{ x: [0, 50, 0], y: [0, 30, 0] }}
          transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute bottom-1/4 -right-1/4 w-[400px] h-[400px] rounded-full opacity-30"
          style={{ background: 'radial-gradient(circle, rgba(251,146,60,0.15) 0%, transparent 70%)' }}
          animate={{ x: [0, -40, 0], y: [0, -40, 0] }}
          transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }}
        />
      </div>

      <div className="relative z-10 max-w-6xl mx-auto px-4 md:px-6 py-4 md:py-12 min-h-screen flex flex-col">
        {/* Header - compact on mobile, different for returning users */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className={`text-center ${isReturningUser ? 'mb-4 md:mb-8' : 'mb-4 md:mb-16'}`}
        >
          {/* Logo - smaller on mobile */}
          <motion.div
            className="inline-flex items-center justify-center w-10 h-10 md:w-16 md:h-16 rounded-xl md:rounded-2xl mb-3 md:mb-6"
            style={{ background: 'linear-gradient(135deg, rgba(167,139,250,0.2) 0%, rgba(251,146,60,0.2) 100%)' }}
            animate={{ rotate: [0, 5, -5, 0] }}
            transition={{ duration: 6, repeat: Infinity }}
          >
            <svg className="w-5 h-5 md:w-8 md:h-8" viewBox="0 0 32 32" fill="none">
              <path d="M16 4 L28 12 L28 24 L16 28 L4 24 L4 12 Z" stroke="#fafafa" strokeWidth="1.5" fill="none" />
              <circle cx="16" cy="16" r="4" fill="#a78bfa" />
            </svg>
          </motion.div>

          {isReturningUser ? (
            <>
              <h1 className="text-2xl md:text-4xl font-bold mb-2 tracking-tight">
                <span className="text-neutral-100">Welcome back</span>
                {userName && (
                  <span className="bg-gradient-to-r from-violet-300 to-purple-300 bg-clip-text text-transparent">
                    , {userName.split(' ')[0]}
                  </span>
                )}
              </h1>
              <p className="text-neutral-400 text-sm md:text-base max-w-xl mx-auto">
                Continue building your profile or explore new areas
              </p>
            </>
          ) : (
            <>
              <h1 className="text-2xl md:text-4xl lg:text-6xl font-bold mb-2 md:mb-4 tracking-tight">
                <span className="text-neutral-100">Who are you when</span>
                <br />
                <span className="bg-gradient-to-r from-orange-300 via-pink-300 to-violet-300 bg-clip-text text-transparent">
                  no one's watching?
                </span>
              </h1>
              <p className="text-neutral-400 text-sm md:text-lg max-w-xl mx-auto">
                Not a survey. Not a quiz. A mirror.
              </p>
            </>
          )}
        </motion.div>

        {/* Main content - different layout for returning users */}
        {isReturningUser ? (
          // Returning user layout: Archetypes first, then compact mode cards
          <div className="flex-1 flex flex-col gap-8 max-w-5xl mx-auto w-full">
            {/* Your Archetypes section */}
            <YourArchetypes
              holisticProfile={holisticProfile}
              userHistory={userHistory}
              onViewArchetype={onViewHistory}
              onViewGallery={onViewGallery}
            />

            {/* Explore More section - compact mode cards */}
            <div>
              <h3 className="text-neutral-400 text-xs md:text-sm uppercase tracking-wider mb-4">
                Explore More
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {modes.map((mode, index) => (
                  <motion.button
                    key={mode.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 + index * 0.05, duration: 0.4 }}
                    onClick={() => onSelectMode(mode.id)}
                    className="relative text-left group focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-[#09090b] rounded-xl"
                    style={{ '--ring-color': mode.colors.primary }}
                  >
                    <motion.div
                      className="relative rounded-xl p-4 overflow-hidden border transition-colors duration-300"
                      style={{
                        background: 'rgba(255,255,255,0.03)',
                        borderColor: 'rgba(255,255,255,0.08)'
                      }}
                      whileHover={{ scale: 1.02, borderColor: mode.colors.border }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <div className="flex items-center gap-3">
                        {/* Icon */}
                        <div className="flex-shrink-0">
                          {IconComponent(mode.id)}
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                          <h2
                            className="text-base font-semibold"
                            style={{ color: mode.colors.text }}
                          >
                            {mode.title}
                          </h2>
                          <div className="text-xs mt-1">
                            <ProgressIndicator
                              mode={mode.id}
                              testsCount={modeStats[mode.id]?.count || 0}
                              stability={modeStats[mode.id]?.stability}
                              deepDiveInterests={modeStats[mode.id]?.interests?.size || 0}
                            />
                          </div>
                        </div>

                        {/* Arrow */}
                        <svg
                          className="w-4 h-4 flex-shrink-0"
                          style={{ color: mode.colors.primary }}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    </motion.div>
                  </motion.button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          // New user layout: Full mode cards
          <div className="flex-1 flex items-start md:items-center justify-center">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-6 w-full max-w-5xl">
              {modes.map((mode, index) => (
                <motion.button
                  key={mode.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 + index * 0.05, duration: 0.4 }}
                  onHoverStart={() => setHoveredMode(mode.id)}
                  onHoverEnd={() => setHoveredMode(null)}
                  onClick={() => onSelectMode(mode.id)}
                  className="relative text-left group focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-[#09090b] rounded-xl md:rounded-3xl"
                  style={{ '--ring-color': mode.colors.primary }}
                >
                  {/* Recommended badge */}
                  {mode.recommended && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.3 }}
                      className="absolute -top-2 md:-top-3 left-1/2 -translate-x-1/2 z-10 px-2 md:px-3 py-0.5 md:py-1 rounded-full text-[10px] md:text-xs font-medium text-white"
                      style={{ background: `linear-gradient(135deg, ${mode.colors.primary}, ${mode.colors.text})` }}
                    >
                      Recommended
                    </motion.div>
                  )}

                  {/* Glow effect - desktop only */}
                  <motion.div
                    className="hidden md:block absolute inset-0 rounded-3xl blur-xl transition-opacity duration-500"
                    style={{ background: mode.colors.glow }}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: hoveredMode === mode.id ? 1 : 0 }}
                  />

                  {/* Card */}
                  <motion.div
                    className="relative rounded-xl md:rounded-3xl p-4 md:p-8 h-full overflow-hidden border transition-colors duration-300"
                    style={{
                      background: 'rgba(255,255,255,0.03)',
                      borderColor: hoveredMode === mode.id ? mode.colors.border : 'rgba(255,255,255,0.08)'
                    }}
                    whileHover={{ scale: 1.02, y: -8 }}
                    whileTap={{ scale: 0.98 }}
                    transition={{ type: "spring", stiffness: 400 }}
                  >
                    <div className="relative z-10 flex md:block items-center gap-3 md:gap-0">
                      {/* Icon - inline on mobile */}
                      <motion.div
                        className="flex-shrink-0 md:mb-6"
                        animate={hoveredMode === mode.id ? { scale: [1, 1.1, 1] } : {}}
                        transition={{ duration: 0.4 }}
                      >
                        {IconComponent(mode.id)}
                      </motion.div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        {/* Title row - mobile */}
                        <div className="flex items-center justify-between md:block">
                          <div>
                            <h2
                              className="text-lg md:text-2xl font-bold"
                              style={{ color: mode.colors.text }}
                            >
                              {mode.title}
                            </h2>
                            <p className="text-neutral-500 text-xs md:text-sm md:mb-4">{mode.subtitle}</p>
                          </div>
                          {/* Meta info - inline on mobile */}
                          <div className="flex md:hidden items-center gap-2 text-[10px] text-neutral-500">
                            <span>{mode.duration}</span>
                            <span>•</span>
                            <span>{mode.questions}q</span>
                          </div>
                        </div>

                        {/* Description - hidden on mobile */}
                        <p className="hidden md:block text-neutral-300 text-sm mb-6 leading-relaxed">
                          {mode.description}
                        </p>

                        {/* Tagline - hidden on mobile */}
                        <p className="hidden md:block text-neutral-400 text-xs italic mb-6">"{mode.tagline}"</p>

                        {/* Meta info - desktop */}
                        <div className="hidden md:flex items-center gap-4 text-xs text-neutral-500">
                          <span className="flex items-center gap-1.5">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            {mode.duration}
                          </span>
                          <span className="flex items-center gap-1.5">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            {mode.questions} questions
                          </span>
                        </div>
                      </div>

                      {/* Arrow - always visible on mobile, hover on desktop */}
                      <motion.div
                        className="flex-shrink-0 md:absolute md:bottom-8 md:right-8"
                        style={{ color: mode.colors.primary }}
                        initial={{ opacity: 1 }}
                        animate={{
                          opacity: 1,
                          x: 0
                        }}
                      >
                        <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </motion.div>
                    </div>
                  </motion.div>
                </motion.button>
              ))}
            </div>
          </div>
        )}

        {/* Footer - hidden on mobile */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="hidden md:block text-center mt-6 md:mt-12"
        >
          <p className="text-neutral-600 text-sm">
            Powered by Big Five personality research
          </p>
        </motion.div>
      </div>

      {/* Keyboard hints - hidden on mobile */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1 }}
        className="hidden md:flex fixed bottom-6 left-1/2 -translate-x-1/2 items-center gap-2 text-neutral-500 text-xs"
      >
        <kbd className="px-2 py-1 bg-neutral-800 rounded border border-neutral-700 text-neutral-400">1</kbd>
        <kbd className="px-2 py-1 bg-neutral-800 rounded border border-neutral-700 text-neutral-400">2</kbd>
        <kbd className="px-2 py-1 bg-neutral-800 rounded border border-neutral-700 text-neutral-400">3</kbd>
        <span className="ml-2">to select</span>
      </motion.div>
    </div>
  );
}
