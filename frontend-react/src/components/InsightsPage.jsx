import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import * as api from '../api';

// Badge icons mapping
const badgeIcons = {
  compass: '🧭', mirror: '🪞', hourglass: '⏳', owl: '🦉',
  sparkles: '✨', scuba: '🤿', cat: '🐱', footprints: '👣',
  refresh: '🔄', lightbulb: '💡', magnifier: '🔍', seedling: '🌱',
  unicorn: '🦄', palette: '🎨', star: '⭐', masks: '🎭',
  users: '👥', bridge: '🌉', cards: '🃏'
};

// Rarity colors
const rarityColors = {
  common: '#a3a3a3',
  uncommon: '#22c55e',
  rare: '#3b82f6',
  legendary: '#f59e0b'
};

// Archetype display names for dream team
const archetypeDisplayNames = {
  architect: 'The Architect',
  catalyst: 'The Catalyst',
  strategist: 'The Strategist',
  guide: 'The Guide',
  alchemist: 'The Alchemist',
  gardener: 'The Gardener',
  luminary: 'The Luminary',
  sentinel: 'The Sentinel'
};

// Mode context labels
const modeContextLabels = {
  pressure: 'Your archetype under pressure',
  hackathon: 'Your archetype under pressure',
  relationships: 'Your archetype in relationships',
  overall: 'Your overall archetype',
  deep_dive: 'Your deep dive archetype'
};

// Section component with expand/collapse
function InsightSection({ title, icon, children, defaultExpanded = false, onView, sectionId }) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const contentRef = useRef(null);
  const viewTracked = useRef(false);

  useEffect(() => {
    if (isExpanded && onView && !viewTracked.current) {
      onView(sectionId);
      viewTracked.current = true;
    }
  }, [isExpanded, onView, sectionId]);

  const handleToggle = () => setIsExpanded(!isExpanded);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleToggle();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-neutral-900/60 border border-neutral-800 rounded-2xl overflow-hidden"
    >
      <button
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        aria-expanded={isExpanded}
        aria-controls={`section-content-${sectionId}`}
        className="w-full px-5 py-4 flex items-center justify-between text-left hover:bg-neutral-800/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl" aria-hidden="true">{icon}</span>
          <h3 className="text-lg font-semibold text-white">{title}</h3>
        </div>
        <motion.span
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="text-neutral-300"
          aria-hidden="true"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </motion.span>
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            id={`section-content-${sectionId}`}
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            ref={contentRef}
            role="region"
            aria-labelledby={`section-${sectionId}`}
          >
            <div className="px-5 pb-5 pt-2 border-t border-neutral-800/50">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// Toggle switch for concise/deep mode
function ModeToggle({ mode, onChange }) {
  return (
    <div className="flex items-center gap-3 bg-neutral-900 rounded-full p-1" role="group" aria-label="Insight detail level">
      <button
        onClick={() => onChange('concise')}
        aria-pressed={mode === 'concise'}
        aria-label="Switch to concise mode - shows key highlights"
        className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
          mode === 'concise'
            ? 'bg-violet-600 text-white'
            : 'text-neutral-300 hover:text-white'
        }`}
      >
        Concise
      </button>
      <button
        onClick={() => onChange('deep')}
        aria-pressed={mode === 'deep'}
        aria-label="Switch to deep dive mode - shows all details"
        className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
          mode === 'deep'
            ? 'bg-violet-600 text-white'
            : 'text-neutral-300 hover:text-white'
        }`}
      >
        Deep Dive
      </button>
    </div>
  );
}

// Quick Insights Cards - always visible punchy cards
function QuickInsightsCards({ quickInsights, color }) {
  if (!quickInsights) return null;

  const cards = [
    { key: 'zone_of_genius', label: 'Zone of Genius', icon: '🎯', value: quickInsights.zone_of_genius },
    { key: 'deepest_aspiration', label: 'Deepest Aspiration', icon: '💫', value: quickInsights.deepest_aspiration },
    { key: 'growth_edge', label: 'Growth Edge', icon: '🌱', value: quickInsights.growth_edge }
  ].filter(card => card.value);

  if (cards.length === 0) return null;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
      {cards.map((card, idx) => (
        <motion.div
          key={card.key}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: idx * 0.1 }}
          className="p-4 rounded-2xl border"
          style={{
            backgroundColor: `${color}10`,
            borderColor: `${color}30`
          }}
        >
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xl">{card.icon}</span>
            <span className="text-xs font-medium uppercase tracking-wider text-neutral-400">
              {card.label}
            </span>
          </div>
          <p className="text-sm text-neutral-200 leading-relaxed">{card.value}</p>
        </motion.div>
      ))}
    </div>
  );
}

// Stability Badge with tooltip
function StabilityBadge({ stability, showTooltip = false }) {
  const [tooltipVisible, setTooltipVisible] = useState(false);

  const config = {
    stable: {
      label: 'Stable',
      color: '#22c55e',
      icon: '✓',
      tooltip: 'Your results are consistent across multiple assessments. This is reliably you.'
    },
    converging: {
      label: 'Emerging',
      color: '#eab308',
      icon: '→',
      tooltip: "We're seeing a pattern form. One more test will give you a stable profile."
    },
    inconsistent: {
      label: 'Variable',
      color: '#f97316',
      icon: '~',
      tooltip: 'Your results vary between assessments. This could mean you\'re adaptable, or try answering more carefully.'
    },
    new: {
      label: 'New',
      color: '#a78bfa',
      icon: '★',
      tooltip: 'Take more tests to confirm your archetype and build a stable profile.'
    },
  };

  const { label, color, icon, tooltip } = config[stability] || config.new;

  return (
    <div className="relative inline-block">
      <div
        className="inline-flex items-center gap-1.5 rounded-full font-medium cursor-help text-sm px-3 py-1"
        style={{ backgroundColor: `${color}20`, color }}
        onMouseEnter={() => showTooltip && setTooltipVisible(true)}
        onMouseLeave={() => showTooltip && setTooltipVisible(false)}
        onClick={() => showTooltip && setTooltipVisible(!tooltipVisible)}
      >
        <span>{icon}</span>
        <span>{label}</span>
        {showTooltip && (
          <svg className="w-3.5 h-3.5 opacity-60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )}
      </div>

      <AnimatePresence>
        {showTooltip && tooltipVisible && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 5 }}
            className="absolute z-50 top-full mt-2 left-1/2 -translate-x-1/2 w-64 p-3 bg-neutral-800 border border-neutral-700 rounded-xl shadow-lg text-sm text-neutral-300"
          >
            <div className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-3 h-3 rotate-45 bg-neutral-800 border-l border-t border-neutral-700" />
            {tooltip}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Stability Guidance component for non-stable profiles
function StabilityGuidance({ stability, testsCompleted = 0, testsForStable = 3, onRetake, assessmentMode }) {
  if (stability === 'stable') return null;

  const modeLabel = assessmentMode === 'hackathon' ? 'Under Pressure' : assessmentMode;

  const config = {
    new: {
      icon: '🌱',
      title: 'New Profile',
      message: `This is your first assessment${modeLabel ? ` for ${modeLabel}` : ''}. Take ${testsForStable - testsCompleted} more to build a reliable profile.`,
      cta: 'Take Another Test'
    },
    converging: {
      icon: '🌿',
      title: 'Emerging Profile',
      message: "We're seeing a pattern! One more consistent test will confirm your archetype.",
      cta: 'Confirm Your Profile'
    },
    inconsistent: {
      icon: '🔄',
      title: 'Variable Profile',
      message: "Your results vary between assessments. This is okay — it might mean you're adaptable, or that some tests were rushed.",
      cta: 'Retake Assessment'
    }
  };

  const { icon, title, message, cta } = config[stability] || config.new;
  const progress = Math.min((testsCompleted / testsForStable) * 100, 100);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-8 p-5 bg-neutral-900/60 border border-neutral-800 rounded-2xl"
    >
      <div className="flex items-start gap-4">
        <span className="text-3xl">{icon}</span>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-white mb-1">{title}</h3>
          <p className="text-sm text-neutral-400 mb-4">{message}</p>

          {stability !== 'inconsistent' && (
            <div className="mb-4">
              <div className="flex justify-between text-xs text-neutral-500 mb-1">
                <span>Progress</span>
                <span>{testsCompleted}/{testsForStable} tests</span>
              </div>
              <div className="h-2 bg-neutral-800 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  className="h-full bg-gradient-to-r from-violet-500 to-purple-500 rounded-full"
                />
              </div>
            </div>
          )}

          {stability === 'inconsistent' && (
            <div className="text-sm text-neutral-500 mb-4">
              <p className="mb-2">For a clearer profile:</p>
              <ul className="space-y-1 ml-4">
                <li>• Take another test when you have 5 quiet minutes</li>
                <li>• Answer based on your typical behavior, not today's mood</li>
                <li>• If results keep varying, you might genuinely be context-dependent</li>
              </ul>
            </div>
          )}

          {onRetake && (
            <button
              onClick={() => onRetake(assessmentMode)}
              className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-xl transition-colors"
            >
              {cta}
            </button>
          )}
        </div>
      </div>
    </motion.div>
  );
}

// Team Context section
function TeamContext({ teamContext, color, navigate }) {
  if (!teamContext) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-8 p-6 bg-neutral-900/60 border border-neutral-800 rounded-2xl"
    >
      <h3 className="text-lg font-semibold text-white mb-4">Your Team Role</h3>

      {/* Role Card */}
      {teamContext.role_title && (
        <div
          className="p-4 rounded-xl mb-4"
          style={{ backgroundColor: `${color}15`, borderLeft: `3px solid ${color}` }}
        >
          <h4 className="font-semibold text-white text-lg">{teamContext.role_title}</h4>
          {teamContext.role_description && (
            <p className="text-sm text-neutral-300 mt-1">{teamContext.role_description}</p>
          )}
        </div>
      )}

      {/* Dream Team */}
      {teamContext.dream_team?.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-neutral-400 uppercase tracking-wider mb-3">
            Dream Team
          </h4>
          <div className="flex flex-wrap gap-2">
            {teamContext.dream_team.map((archetypeId) => (
              <button
                key={archetypeId}
                onClick={() => navigate(`/insights/${archetypeId}`)}
                className="px-3 py-1.5 bg-neutral-800 hover:bg-neutral-700 rounded-lg text-sm text-white transition-colors"
              >
                {archetypeDisplayNames[archetypeId] || archetypeId}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Creative Partner */}
      {teamContext.creative_partner && (
        <div>
          <h4 className="text-sm font-medium text-neutral-400 uppercase tracking-wider mb-3">
            Ideal Creative Partner
          </h4>
          <button
            onClick={() => navigate(`/insights/${teamContext.creative_partner}`)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl transition-colors"
            style={{ backgroundColor: `${color}20`, color }}
          >
            <span className="text-lg">✨</span>
            <span className="font-medium">
              {archetypeDisplayNames[teamContext.creative_partner] || teamContext.creative_partner}
            </span>
          </button>
        </div>
      )}
    </motion.div>
  );
}

// Trait bar component
function TraitBar({ trait, score, color }) {
  return (
    <div className="mb-3">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-neutral-300">{trait}</span>
        <span className="text-neutral-400">{score}%</span>
      </div>
      <div className="h-2 bg-neutral-800 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
        />
      </div>
    </div>
  );
}

// Reading progress indicator
function ReadingProgress({ sectionsRead, totalSections }) {
  const progress = (sectionsRead / totalSections) * 100;

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-[#09090b]/90 backdrop-blur-sm border-b border-neutral-800">
      <div
        className="h-1 bg-neutral-800"
        role="progressbar"
        aria-valuenow={Math.round(progress)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Reading progress: ${sectionsRead} of ${totalSections} sections read`}
      >
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          className="h-full bg-gradient-to-r from-violet-500 to-purple-500"
        />
      </div>
      <div className="max-w-3xl mx-auto px-4 py-2 flex items-center justify-between text-sm">
        <span className="text-neutral-300">
          {sectionsRead} of {totalSections} sections read
        </span>
        {progress === 100 && (
          <span className="text-green-400 flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Complete!
          </span>
        )}
      </div>
    </div>
  );
}

export default function InsightsPage() {
  const { archetypeId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  // Get mode context from URL params (e.g., ?mode=pressure)
  const modeContext = searchParams.get('mode');

  const [insights, setInsights] = useState(null);
  const [mode, setMode] = useState('concise');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [profileId, setProfileId] = useState(null);
  const [badges, setBadges] = useState(null);
  const [sectionsViewed, setSectionsViewed] = useState(new Set());
  const [newBadges, setNewBadges] = useState([]);
  const [profileStability, setProfileStability] = useState(null);
  const [testsCompleted, setTestsCompleted] = useState(0);

  // Total sections: deep has 7 (summary, strengths, blind_spots, team_phases, energy, tips, complementary)
  // Concise has 5 (summary, strengths, blind_spots, tips, complementary)
  const totalSections = mode === 'deep' ? 7 : 5;

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      try {
        let preferredMode = mode;

        // First, get user preferences to know the correct mode
        if (user) {
          const profileData = await api.getOrCreateProfile(user.uid, null);
          if (profileData?.profile_id) {
            setProfileId(profileData.profile_id);

            // Track app open for weekly wanderer badge
            await api.trackAppOpen(profileData.profile_id);

            // Get user preferences FIRST to know the correct mode
            const prefs = await api.getUserPreferences(profileData.profile_id);
            if (prefs.insight_mode) {
              preferredMode = prefs.insight_mode;
              setMode(prefs.insight_mode);
            }

            // Get badges
            const badgeData = await api.getBadges(profileData.profile_id);
            setBadges(badgeData);

            // Get full profile to check stability
            try {
              const fullProfile = await api.getProfileView(profileData.profile_id);
              // Get stability from the relevant mode context or overall
              const relevantMode = modeContext || 'hackathon';
              const modeProfile = fullProfile.mode_profiles?.[relevantMode];
              if (modeProfile) {
                setProfileStability(modeProfile.stability || 'new');
                setTestsCompleted(modeProfile.tests_included || 0);
              } else {
                setProfileStability('new');
                setTestsCompleted(fullProfile.total_tests || 0);
              }
            } catch (err) {
              console.error('Failed to load profile for stability:', err);
            }
          }
        }

        // Now load insights with the correct mode
        const insightsData = await api.getArchetypeInsights(archetypeId, preferredMode);
        setInsights(insightsData);
      } catch (err) {
        console.error('Failed to load insights:', err);
        setError('Failed to load insights');
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [archetypeId, user, modeContext]);

  // Reload insights when mode changes
  useEffect(() => {
    if (!archetypeId || isLoading) return;

    const reloadInsights = async () => {
      try {
        const insightsData = await api.getArchetypeInsights(archetypeId, mode);
        setInsights(insightsData);

        // Save preference
        if (profileId) {
          await api.setInsightMode(profileId, mode);
        }
      } catch (err) {
        console.error('Failed to reload insights:', err);
      }
    };

    reloadInsights();
  }, [mode]);

  // Track section view
  const handleSectionView = async (sectionId) => {
    if (!profileId || sectionsViewed.has(sectionId)) return;

    setSectionsViewed(prev => new Set([...prev, sectionId]));

    try {
      const result = await api.trackInsightView(profileId, archetypeId, sectionId, 0);
      if (result.newly_awarded_badges?.length > 0) {
        setNewBadges(prev => [...prev, ...result.newly_awarded_badges]);
      }
    } catch (err) {
      console.error('Failed to track view:', err);
    }
  };

  // Track time spent on blind spots (for badge)
  const handleBlindSpotsTimeTracking = async (seconds) => {
    if (!profileId) return;

    try {
      const result = await api.trackInsightView(profileId, archetypeId, 'blind_spots', seconds);
      if (result.newly_awarded_badges?.length > 0) {
        setNewBadges(prev => [...prev, ...result.newly_awarded_badges]);
      }
    } catch (err) {
      console.error('Failed to track time:', err);
    }
  };

  // Auto-dismiss badge toast after 5 seconds
  useEffect(() => {
    if (newBadges.length > 0) {
      const timer = setTimeout(() => {
        setNewBadges([]);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [newBadges]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#09090b] flex items-center justify-center">
        <div className="animate-spin h-10 w-10 border-4 border-violet-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error || !insights) {
    return (
      <div className="min-h-screen bg-[#09090b] flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error || 'Archetype not found'}</p>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-neutral-800 text-white rounded-lg hover:bg-neutral-700"
          >
            Go Home
          </button>
        </div>
      </div>
    );
  }

  const archetypeColor = insights.color || '#a78bfa';

  return (
    <div className="min-h-screen bg-[#09090b]">
      {/* Reading progress */}
      {mode === 'deep' && (
        <ReadingProgress sectionsRead={sectionsViewed.size} totalSections={totalSections} />
      )}

      {/* Header */}
      <div className={`sticky ${mode === 'deep' ? 'top-10' : 'top-0'} z-40 bg-[#09090b]/95 backdrop-blur-sm border-b border-neutral-800`}>
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-neutral-400 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            <span className="hidden sm:inline">Back</span>
          </button>

          <ModeToggle mode={mode} onChange={setMode} />

          <div className="w-16" />
        </div>
      </div>

      {/* Content */}
      <div className="max-w-3xl mx-auto px-4 py-8">
        {/* Mode Context Banner */}
        {modeContext && modeContextLabels[modeContext] && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 px-4 py-2 bg-violet-500/10 border border-violet-500/30 rounded-xl text-center"
          >
            <span className="text-sm text-violet-300">{modeContextLabels[modeContext]}</span>
          </motion.div>
        )}

        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div
            className="w-20 h-20 mx-auto mb-4 rounded-2xl flex items-center justify-center text-4xl"
            style={{ backgroundColor: `${archetypeColor}20` }}
          >
            {insights.icon || '✨'}
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">{insights.display_name}</h1>
          <p className="text-xl text-neutral-400 italic mb-3">{insights.tagline}</p>

          {/* Stability Badge */}
          {profileStability && (
            <div className="mt-3">
              <StabilityBadge stability={profileStability} showTooltip={true} />
            </div>
          )}
        </motion.div>

        {/* Quick Insights Cards - Always visible */}
        <QuickInsightsCards quickInsights={insights.quick_insights} color={archetypeColor} />

        {/* Stability Guidance for non-stable profiles */}
        {profileStability && profileStability !== 'stable' && (
          <StabilityGuidance
            stability={profileStability}
            testsCompleted={testsCompleted}
            testsForStable={3}
            assessmentMode={modeContext || 'hackathon'}
            onRetake={(mode) => {
              // Navigate to home with mode param to auto-start test
              navigate(`/?startMode=${mode || 'hackathon'}`);
            }}
          />
        )}

        {/* Trait Profile */}
        {insights.trait_profile && Object.keys(insights.trait_profile).length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8 p-6 bg-neutral-900/60 border border-neutral-800 rounded-2xl"
          >
            <h3 className="text-lg font-semibold text-white mb-4">Trait Profile</h3>
            {Object.entries(insights.trait_profile).map(([trait, score]) => (
              <TraitBar
                key={trait}
                trait={trait.replace('_', ' ')}
                score={score}
                color={archetypeColor}
              />
            ))}
          </motion.div>
        )}

        {/* Summary Section */}
        <InsightSection
          title="Who You Are"
          icon="🎯"
          defaultExpanded={true}
          sectionId="summary"
          onView={handleSectionView}
        >
          <p className="text-neutral-300 leading-relaxed whitespace-pre-line">
            {insights.summary}
          </p>
        </InsightSection>

        <div className="h-4" />

        {/* Collaboration Strengths */}
        <InsightSection
          title="Collaboration Strengths"
          icon="💪"
          sectionId="strengths"
          onView={handleSectionView}
        >
          {Array.isArray(insights.collaboration_strengths) ? (
            <ul className="space-y-3">
              {insights.collaboration_strengths.map((strength, idx) => (
                <li key={idx} className="flex items-baseline gap-3">
                  <span className="text-green-400 text-lg leading-none">+</span>
                  <span className="text-neutral-300">{strength}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-neutral-300 leading-relaxed whitespace-pre-line">
              {insights.collaboration_strengths}
            </p>
          )}
        </InsightSection>

        <div className="h-4" />

        {/* Potential Blind Spots */}
        <InsightSection
          title="Growth Opportunities"
          icon="🔍"
          sectionId="blind_spots"
          onView={handleSectionView}
        >
          {Array.isArray(insights.potential_blind_spots) ? (
            <ul className="space-y-3">
              {insights.potential_blind_spots.map((blindSpot, idx) => (
                <li key={idx} className="flex items-baseline gap-3">
                  <span className="text-yellow-400 text-lg leading-none">!</span>
                  <span className="text-neutral-300">{blindSpot}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-neutral-300 leading-relaxed whitespace-pre-line">
              {insights.potential_blind_spots}
            </p>
          )}
        </InsightSection>

        <div className="h-4" />

        {/* Team Phases (Deep mode only) */}
        {mode === 'deep' && insights.team_phases && (
          <>
            <InsightSection
              title="How You Show Up in Team Phases"
              icon="🔄"
              sectionId="team_phases"
              onView={handleSectionView}
            >
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {Object.entries(insights.team_phases).map(([phase, data]) => (
                  <div key={phase} className="p-4 bg-neutral-800/50 rounded-xl">
                    <h4 className="text-sm font-medium text-violet-400 uppercase tracking-wider mb-2">
                      {phase.replace('_', ' ')}
                    </h4>
                    {typeof data === 'object' ? (
                      <div className="space-y-2">
                        <div className="flex items-baseline gap-2">
                          <span className="text-green-400 leading-none">+</span>
                          <p className="text-sm text-neutral-300">{data.strength}</p>
                        </div>
                        <div className="flex items-baseline gap-2">
                          <span className="text-yellow-400 leading-none">!</span>
                          <p className="text-sm text-neutral-400">{data.watch_for}</p>
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-neutral-300">{data}</p>
                    )}
                  </div>
                ))}
              </div>
            </InsightSection>
            <div className="h-4" />
          </>
        )}

        {/* Energy Dynamics (Deep mode only) */}
        {mode === 'deep' && insights.energy_dynamics && (
          <>
            <InsightSection
              title="Energy Dynamics"
              icon="⚡"
              sectionId="energy"
              onView={handleSectionView}
            >
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                {(insights.energy_dynamics.energized_by || insights.energy_dynamics.energizes) && (
                  <div>
                    <h4 className="text-green-400 font-medium mb-3 flex items-center gap-2">
                      <span>+</span> What Energizes You
                    </h4>
                    <ul className="space-y-2">
                      {(insights.energy_dynamics.energized_by || insights.energy_dynamics.energizes).map((item, idx) => (
                        <li key={idx} className="text-sm text-neutral-300 flex items-start gap-2">
                          <span className="text-green-400">•</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {(insights.energy_dynamics.drained_by || insights.energy_dynamics.drains) && (
                  <div>
                    <h4 className="text-red-400 font-medium mb-3 flex items-center gap-2">
                      <span>-</span> What Drains You
                    </h4>
                    <ul className="space-y-2">
                      {(insights.energy_dynamics.drained_by || insights.energy_dynamics.drains).map((item, idx) => (
                        <li key={idx} className="text-sm text-neutral-300 flex items-start gap-2">
                          <span className="text-red-400">•</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </InsightSection>
            <div className="h-4" />
          </>
        )}

        {/* Actionable Tips */}
        <InsightSection
          title="Actionable Tips"
          icon="📝"
          sectionId="tips"
          onView={handleSectionView}
        >
          <div className="space-y-4">
            {insights.actionable_tips?.map((tip, idx) => (
              <div key={idx} className="flex items-start gap-4">
                <div
                  className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold shrink-0"
                  style={{ backgroundColor: `${archetypeColor}20`, color: archetypeColor }}
                >
                  {idx + 1}
                </div>
                <div className="flex-1">
                  {typeof tip === 'object' ? (
                    <>
                      <h4 className="font-medium text-white mb-1">{tip.title}</h4>
                      <p className="text-sm text-neutral-400">{tip.description}</p>
                    </>
                  ) : (
                    <p className="text-neutral-300">{tip}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </InsightSection>

        <div className="h-4" />

        {/* Team Context - Role, Dream Team, Creative Partner */}
        {insights.team_context && (
          <TeamContext
            teamContext={insights.team_context}
            color={archetypeColor}
            navigate={navigate}
          />
        )}

        {/* Complementary Archetypes - only show if no team_context */}
        {!insights.team_context && insights.complementary_archetypes?.length > 0 && (
          <InsightSection
            title="You Work Well With"
            icon="🤝"
            sectionId="complementary"
            onView={handleSectionView}
          >
            <div className="flex flex-wrap gap-3">
              {insights.complementary_archetypes.map((archetype, idx) => (
                <button
                  key={idx}
                  onClick={() => navigate(`/insights/${archetype.toLowerCase().replace(/\s+/g, '-').replace('the-', '')}`)}
                  className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 rounded-xl text-white text-sm transition-colors"
                >
                  {archetype}
                </button>
              ))}
            </div>
            <p className="text-sm text-neutral-500 mt-4">
              Coming soon: Find teammates who complement your style
            </p>
          </InsightSection>
        )}

        <div className="h-4" />

        {/* Related Badges */}
        {badges && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-6 bg-neutral-900/60 border border-neutral-800 rounded-2xl"
          >
            <h3 className="text-lg font-semibold text-white mb-4">Insight Badges</h3>

            {/* Progress toward insight badges */}
            <div className="space-y-3">
              {badges.incomplete?.filter(b =>
                ['curious_cat', 'aha_moment', 'blind_spot_hunter', 'the_revisitor'].includes(b.badge_id)
              ).map(badge => (
                <div key={badge.badge_id} className="flex items-center gap-3">
                  <span className="text-2xl opacity-50">{badgeIcons[badge.icon] || '🏆'}</span>
                  <div className="flex-1">
                    <p className="text-sm text-neutral-300">{badge.display_name}</p>
                    <p className="text-xs text-neutral-500">{badge.description}</p>
                  </div>
                </div>
              ))}

              {badges.earned?.filter(b =>
                ['curious_cat', 'aha_moment', 'blind_spot_hunter', 'the_revisitor'].includes(b.badge_id)
              ).map(badge => (
                <div key={badge.badge_id} className="flex items-center gap-3">
                  <span className="text-2xl">{badgeIcons[badge.icon] || '🏆'}</span>
                  <div className="flex-1">
                    <p className="text-sm text-white">{badge.display_name}</p>
                    <p className="text-xs text-green-400">Earned!</p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* New badge notification */}
        <AnimatePresence>
          {newBadges.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 50 }}
              className="fixed bottom-6 left-4 right-4 mx-auto max-w-md p-4 bg-gradient-to-r from-violet-600 to-purple-600 rounded-2xl shadow-lg"
            >
              <div className="flex items-center gap-3">
                <span className="text-3xl">{badgeIcons[newBadges[0].icon] || '🏆'}</span>
                <div>
                  <p className="font-semibold text-white">Badge Earned!</p>
                  <p className="text-sm text-white/80">{newBadges[0].display_name}</p>
                </div>
                <button
                  onClick={() => setNewBadges([])}
                  className="ml-auto text-white/60 hover:text-white"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
