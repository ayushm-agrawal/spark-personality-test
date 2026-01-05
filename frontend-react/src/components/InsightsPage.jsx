import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  const navigate = useNavigate();
  const { user } = useAuth();

  const [insights, setInsights] = useState(null);
  const [mode, setMode] = useState('concise');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [profileId, setProfileId] = useState(null);
  const [badges, setBadges] = useState(null);
  const [sectionsViewed, setSectionsViewed] = useState(new Set());
  const [newBadges, setNewBadges] = useState([]);

  // Total sections in deep mode
  const totalSections = mode === 'deep' ? 8 : 5;

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      try {
        // Load insights
        const insightsData = await api.getArchetypeInsights(archetypeId, mode);
        setInsights(insightsData);

        // Load user profile and preferences if authenticated
        if (user) {
          const profileData = await api.getOrCreateProfile(user.uid, null);
          if (profileData?.profile_id) {
            setProfileId(profileData.profile_id);

            // Track app open for weekly wanderer badge
            await api.trackAppOpen(profileData.profile_id);

            // Get user preferences
            const prefs = await api.getUserPreferences(profileData.profile_id);
            if (prefs.insight_mode) {
              setMode(prefs.insight_mode);
            }

            // Get badges
            const badgeData = await api.getBadges(profileData.profile_id);
            setBadges(badgeData);
          }
        }
      } catch (err) {
        console.error('Failed to load insights:', err);
        setError('Failed to load insights');
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [archetypeId, user]);

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
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-10"
        >
          <div
            className="w-20 h-20 mx-auto mb-4 rounded-2xl flex items-center justify-center text-4xl"
            style={{ backgroundColor: `${archetypeColor}20` }}
          >
            {insights.icon || '✨'}
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">{insights.display_name}</h1>
          <p className="text-xl text-neutral-400 italic">{insights.tagline}</p>
        </motion.div>

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
                <li key={idx} className="flex items-start gap-3">
                  <span className="text-green-400 mt-1">+</span>
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
                <li key={idx} className="flex items-start gap-3">
                  <span className="text-yellow-400 mt-1">!</span>
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
                {Object.entries(insights.team_phases).map(([phase, description]) => (
                  <div key={phase} className="p-4 bg-neutral-800/50 rounded-xl">
                    <h4 className="text-sm font-medium text-violet-400 uppercase tracking-wider mb-2">
                      {phase.replace('_', ' ')}
                    </h4>
                    <p className="text-sm text-neutral-300">{description}</p>
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
                {insights.energy_dynamics.energizes && (
                  <div>
                    <h4 className="text-green-400 font-medium mb-3 flex items-center gap-2">
                      <span>+</span> What Energizes You
                    </h4>
                    <ul className="space-y-2">
                      {insights.energy_dynamics.energizes.map((item, idx) => (
                        <li key={idx} className="text-sm text-neutral-300 flex items-start gap-2">
                          <span className="text-green-400">•</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {insights.energy_dynamics.drains && (
                  <div>
                    <h4 className="text-red-400 font-medium mb-3 flex items-center gap-2">
                      <span>-</span> What Drains You
                    </h4>
                    <ul className="space-y-2">
                      {insights.energy_dynamics.drains.map((item, idx) => (
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
                <div>
                  <h4 className="font-medium text-white mb-1">{tip.title}</h4>
                  <p className="text-sm text-neutral-400">{tip.description}</p>
                </div>
              </div>
            ))}
          </div>
        </InsightSection>

        <div className="h-4" />

        {/* Complementary Archetypes */}
        {insights.complementary_archetypes?.length > 0 && (
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
