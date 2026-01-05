import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import * as api from '../api';

// Base URL for shareable profile links
const SHARE_BASE_URL = 'https://personality.ception.one/u/';

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

// Stability badge component with tooltip
function StabilityBadge({ stability, size = 'md', showTooltip = false }) {
  const [tooltipVisible, setTooltipVisible] = useState(false);

  const config = {
    stable: {
      label: 'Stable',
      color: '#22c55e',
      icon: '✓',
      description: 'Consistent results',
      tooltip: 'Your results are consistent across multiple assessments. This is reliably you.'
    },
    converging: {
      label: 'Emerging',
      color: '#eab308',
      icon: '→',
      description: 'Becoming clearer',
      tooltip: "We're seeing a pattern form. One more test will give you a stable profile."
    },
    inconsistent: {
      label: 'Variable',
      color: '#f97316',
      icon: '~',
      description: 'Results vary',
      tooltip: 'Your results vary between assessments. This could mean you\'re adaptable, or try answering more carefully.'
    },
    new: {
      label: 'New',
      color: '#a78bfa',
      icon: '★',
      description: 'Take more tests',
      tooltip: 'Take more tests to confirm your archetype and build a stable profile.'
    },
  };

  const { label, color, icon, description, tooltip } = config[stability] || config.new;
  const sizeClass = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-3 py-1';

  return (
    <div className="relative inline-block">
      <div
        className={`inline-flex items-center gap-1.5 rounded-full font-medium cursor-help ${sizeClass}`}
        style={{ backgroundColor: `${color}20`, color }}
        title={!showTooltip ? description : undefined}
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

      {/* Tooltip */}
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

// Badge display component
function BadgeItem({ badge, onClick }) {
  const icon = badgeIcons[badge.icon] || '🏆';
  const rarityColor = rarityColors[badge.rarity] || rarityColors.common;

  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      aria-label={`View ${badge.display_name} badge details - ${badge.rarity} rarity`}
      className="w-16 h-16 rounded-xl flex items-center justify-center relative group"
      style={{ backgroundColor: `${rarityColor}15`, border: `1px solid ${rarityColor}30` }}
    >
      <span className="text-2xl" aria-hidden="true">{icon}</span>
      {/* Rarity indicator */}
      <div
        className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full"
        style={{ backgroundColor: rarityColor }}
        aria-hidden="true"
      />
    </motion.button>
  );
}

// Badges section component
function BadgesSection({ badges, onBadgeClick }) {
  if (!badges || badges.earned?.length === 0) {
    return (
      <div className="text-center py-6">
        <span className="text-4xl opacity-50">🏆</span>
        <p className="text-neutral-500 mt-2 text-sm">No badges yet</p>
        <p className="text-neutral-600 text-xs">Complete tests and explore insights to earn badges</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex flex-wrap gap-3 justify-center">
        {badges.earned?.map(badge => (
          <BadgeItem key={badge.badge_id} badge={badge} onClick={() => onBadgeClick?.(badge)} />
        ))}
      </div>
      <div className="mt-4 text-center">
        <p className="text-sm text-neutral-400">
          {badges.badges_count} badge{badges.badges_count !== 1 ? 's' : ''} earned • {badges.total_points} points
        </p>
      </div>
    </div>
  );
}

// Badge detail modal with focus management
function BadgeDetailModal({ badge, onClose }) {
  const modalRef = useRef(null);
  const previousFocusRef = useRef(null);

  useEffect(() => {
    if (badge) {
      // Store the element that had focus before opening
      previousFocusRef.current = document.activeElement;
      // Focus the modal
      modalRef.current?.focus();
    }
    return () => {
      // Return focus when closing
      previousFocusRef.current?.focus();
    };
  }, [badge]);

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  if (!badge) return null;

  const icon = badgeIcons[badge.icon] || '🏆';
  const rarityColor = rarityColors[badge.rarity] || rarityColors.common;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="badge-modal-title"
    >
      <motion.div
        ref={modalRef}
        tabIndex={-1}
        onKeyDown={handleKeyDown}
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={e => e.stopPropagation()}
        className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6 max-w-sm w-full outline-none"
      >
        <div className="text-center">
          <div
            className="w-20 h-20 mx-auto rounded-2xl flex items-center justify-center mb-4"
            style={{ backgroundColor: `${rarityColor}20` }}
          >
            <span className="text-5xl" aria-hidden="true">{icon}</span>
          </div>
          <h3 id="badge-modal-title" className="text-xl font-bold text-white mb-1">{badge.display_name}</h3>
          <p
            className="text-sm font-medium capitalize mb-3"
            style={{ color: rarityColor }}
          >
            {badge.rarity}
          </p>
          <p className="text-neutral-300 mb-4">{badge.description}</p>
          {badge.earned_at && (
            <p className="text-sm text-neutral-400">
              Earned {new Date(badge.earned_at * 1000).toLocaleDateString('en-US', {
                month: 'long',
                day: 'numeric',
                year: 'numeric'
              })}
            </p>
          )}
        </div>
        <button
          onClick={onClose}
          className="mt-6 w-full py-3 bg-neutral-800 hover:bg-neutral-700 rounded-xl text-white font-medium transition-colors"
        >
          Close
        </button>
      </motion.div>
    </motion.div>
  );
}

// Confidence explanation tooltip
function ConfidenceTooltip() {
  const [visible, setVisible] = useState(false);

  return (
    <div className="relative inline-block">
      <button
        className="text-neutral-500 hover:text-neutral-400"
        onMouseEnter={() => setVisible(true)}
        onMouseLeave={() => setVisible(false)}
        onClick={() => setVisible(!visible)}
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </button>

      <AnimatePresence>
        {visible && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 5 }}
            className="absolute z-50 top-full mt-2 right-0 w-64 p-3 bg-neutral-800 border border-neutral-700 rounded-xl shadow-lg text-sm text-neutral-300"
          >
            <div className="absolute -top-1.5 right-3 w-3 h-3 rotate-45 bg-neutral-800 border-l border-t border-neutral-700" />
            Confidence measures how strongly your responses point to this archetype versus others. Higher confidence means clearer signal. Below 50% means your profile is still forming.
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Archetype colors mapping
const archetypeColors = {
  'The Architect': '#60a5fa',
  'The Catalyst': '#f97316',
  'The Strategist': '#8b5cf6',
  'The Guide': '#22c55e',
  'The Alchemist': '#eab308',
  'The Gardener': '#10b981',
  'The Luminary': '#f59e0b',
  'The Sentinel': '#6366f1',
};

// Mode display names
const modeLabels = {
  hackathon: { label: 'Under Pressure', icon: '⚡', description: 'How you collaborate under pressure' },
  overall: { label: 'Full Profile', icon: '✨', description: 'Complete personality picture' },
  deep_dive: { label: 'Deep Dive', icon: '🔍', description: 'Context-specific insights' },
};

// Profile card component
function ProfileCard({ title, icon, archetype, confidence, stability, testsIncluded, testsExcluded, color }) {
  const archetypeColor = color || archetypeColors[archetype] || '#a78bfa';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-neutral-900/80 border border-neutral-800 rounded-2xl p-5"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{icon}</span>
          <div>
            <h3 className="text-lg font-semibold text-white">{title}</h3>
            <p className="text-sm text-neutral-500">
              {testsIncluded} test{testsIncluded !== 1 ? 's' : ''}
              {testsExcluded > 0 && <span className="text-neutral-600"> ({testsExcluded} excluded)</span>}
            </p>
          </div>
        </div>
        <StabilityBadge stability={stability} size="sm" />
      </div>

      <div className="flex items-center justify-between">
        <div>
          <p className="text-2xl font-bold" style={{ color: archetypeColor }}>
            {archetype || 'Not yet determined'}
          </p>
          {confidence > 0 && (
            <p className="text-sm text-neutral-400 mt-1">
              {Math.round(confidence)}% confidence
            </p>
          )}
        </div>
        {archetype && (
          <div
            className="w-12 h-12 rounded-xl flex items-center justify-center"
            style={{ backgroundColor: `${archetypeColor}20` }}
          >
            <span className="text-2xl">{archetypeColor === '#60a5fa' ? '🏛️' : '✨'}</span>
          </div>
        )}
      </div>
    </motion.div>
  );
}

// Empty state component
function EmptyState({ message, submessage }) {
  return (
    <div className="text-center py-12">
      <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-neutral-800 flex items-center justify-center">
        <span className="text-3xl">📊</span>
      </div>
      <p className="text-neutral-300 mb-2">{message}</p>
      <p className="text-sm text-neutral-500">{submessage}</p>
    </div>
  );
}

export default function ProfilePage({ onClose, onStartTest }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [username, setUsername] = useState(null);
  const [isSettingUsername, setIsSettingUsername] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);
  const [badges, setBadges] = useState(null);
  const [selectedBadge, setSelectedBadge] = useState(null);

  useEffect(() => {
    const loadProfile = async () => {
      if (!user) return;

      setIsLoading(true);
      setError(null);

      try {
        // First get or create profile to get the profile_id
        const profileData = await api.getOrCreateProfile(user.uid, null);
        if (profileData?.profile_id) {
          // Then get the full profile view
          const fullProfile = await api.getProfileView(profileData.profile_id);
          setProfile({ ...fullProfile, profile_id: profileData.profile_id });
          setUsername(fullProfile.username);

          // Load badges
          try {
            const badgesData = await api.getBadges(profileData.profile_id);
            setBadges(badgesData);
          } catch (err) {
            console.error('Failed to load badges:', err);
          }

          // Track app open for weekly wanderer badge
          try {
            await api.trackAppOpen(profileData.profile_id);
          } catch (err) {
            console.error('Failed to track app open:', err);
          }

          // Auto-generate username if not set
          if (!fullProfile.username && user.displayName) {
            setIsSettingUsername(true);
            try {
              const { username: generatedUsername } = await api.generateUsername(user.displayName);
              const result = await api.setUsername(profileData.profile_id, generatedUsername, user.displayName);
              if (result.success) {
                setUsername(result.username);
              }
            } catch (err) {
              console.error('Failed to generate username:', err);
            } finally {
              setIsSettingUsername(false);
            }
          }
        }
      } catch (err) {
        console.error('Failed to load profile:', err);
        setError('Failed to load profile');
      } finally {
        setIsLoading(false);
      }
    };

    loadProfile();
  }, [user]);

  // Navigate to insights page
  const handleViewInsights = (archetype) => {
    if (!archetype) return;
    const archetypeId = archetype.toLowerCase().replace(/\s+/g, '-').replace('the-', '');
    navigate(`/insights/${archetypeId}`);
  };

  const handleCopyLink = async () => {
    if (!username) return;

    const profileUrl = `${SHARE_BASE_URL}${username}`;
    try {
      await navigator.clipboard.writeText(profileUrl);
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2000);
    } catch (err) {
      console.error('Failed to copy link:', err);
    }
  };

  const hasAnyData = profile && (
    Object.keys(profile.mode_profiles || {}).length > 0 ||
    Object.keys(profile.deep_dive_profiles || {}).length > 0
  );

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-[#09090b] overflow-y-auto"
    >
      {/* Header */}
      <div className="sticky top-0 z-10 bg-[#09090b]/95 backdrop-blur-sm border-b border-neutral-800">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center justify-between">
          <button
            onClick={onClose}
            className="flex items-center gap-2 text-neutral-400 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            <span className="hidden sm:inline">Back</span>
          </button>

          <h1 className="text-lg font-semibold text-white">My Profile</h1>

          <div className="w-16" /> {/* Spacer for centering */}
        </div>
      </div>

      {/* Content */}
      <div className="max-w-2xl mx-auto px-4 py-6">
        {/* Loading state */}
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin h-10 w-10 border-4 border-violet-500 border-t-transparent rounded-full" />
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="text-center py-12">
            <p className="text-red-400 mb-4">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-neutral-800 text-white rounded-lg hover:bg-neutral-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Profile content */}
        {!isLoading && !error && (
          <>
            {/* User info */}
            <div className="text-center mb-8">
              {user?.photoURL ? (
                <img
                  src={user.photoURL}
                  alt={user.displayName || 'User'}
                  className="w-20 h-20 rounded-full mx-auto mb-4 border-4 border-neutral-800"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <div className="w-20 h-20 rounded-full mx-auto mb-4 bg-violet-600 flex items-center justify-center text-white text-2xl font-semibold">
                  {(user?.displayName || user?.email || 'U')[0].toUpperCase()}
                </div>
              )}
              <h2 className="text-xl font-bold text-white">{user?.displayName || 'User'}</h2>

              {/* Username display */}
              {username && (
                <p className="text-sm text-violet-400 mt-1">@{username}</p>
              )}
              {isSettingUsername && (
                <p className="text-sm text-neutral-500 mt-1">Setting up your username...</p>
              )}

              {profile?.member_since && (
                <p className="text-sm text-neutral-500 mt-1">
                  Member since {new Date(profile.member_since * 1000).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                </p>
              )}

              {/* Share profile button */}
              {username && (
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleCopyLink}
                  className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-white text-sm transition-colors"
                >
                  {copiedLink ? (
                    <>
                      <svg className="w-4 h-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-green-400">Link Copied!</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                      </svg>
                      <span>Share Profile</span>
                    </>
                  )}
                </motion.button>
              )}
            </div>

            {/* Stats summary */}
            {hasAnyData && (
              <div className="grid grid-cols-3 gap-3 mb-8">
                <div className="bg-neutral-900/60 border border-neutral-800 rounded-xl p-4 text-center">
                  <p className="text-2xl font-bold text-white">{profile.total_tests || 0}</p>
                  <p className="text-xs text-neutral-500">Tests Taken</p>
                </div>
                <div className="bg-neutral-900/60 border border-neutral-800 rounded-xl p-4 text-center">
                  <p className="text-2xl font-bold text-green-400">{profile.tests_included || 0}</p>
                  <p className="text-xs text-neutral-500">Included</p>
                </div>
                <div className="bg-neutral-900/60 border border-neutral-800 rounded-xl p-4 text-center">
                  <p className="text-2xl font-bold text-neutral-500">{profile.tests_excluded || 0}</p>
                  <p className="text-xs text-neutral-500">Excluded</p>
                </div>
              </div>
            )}

            {/* Badges Section */}
            <div className="mb-8">
              <h3 className="text-sm font-medium text-neutral-400 uppercase tracking-wider mb-4">
                Badges
              </h3>
              <div className="bg-neutral-900/60 border border-neutral-800 rounded-2xl p-5">
                <BadgesSection badges={badges} onBadgeClick={setSelectedBadge} />
              </div>
            </div>

            {/* No data state */}
            {!hasAnyData && (
              <EmptyState
                message="No personality data yet"
                submessage="Take your first test to start building your profile"
              />
            )}

            {/* Mode profiles */}
            {profile?.mode_profiles && Object.keys(profile.mode_profiles).length > 0 && (
              <div className="mb-8">
                <h3 className="text-sm font-medium text-neutral-400 uppercase tracking-wider mb-4">
                  Assessment Profiles
                </h3>
                <div className="space-y-4">
                  {Object.entries(profile.mode_profiles).map(([mode, data]) => {
                    const modeInfo = modeLabels[mode] || { label: mode, icon: '📊', description: '' };
                    return (
                      <ProfileCard
                        key={mode}
                        title={modeInfo.label}
                        icon={modeInfo.icon}
                        archetype={data.current_archetype}
                        confidence={data.confidence || 0}
                        stability={data.stability || 'new'}
                        testsIncluded={data.tests_included || 0}
                        testsExcluded={data.tests_excluded || 0}
                      />
                    );
                  })}
                </div>
              </div>
            )}

            {/* Deep dive profiles */}
            {profile?.deep_dive_profiles && Object.keys(profile.deep_dive_profiles).length > 0 && (
              <div className="mb-8">
                <h3 className="text-sm font-medium text-neutral-400 uppercase tracking-wider mb-4">
                  Deep Dive Profiles
                </h3>
                <div className="space-y-4">
                  {Object.entries(profile.deep_dive_profiles).map(([interest, data]) => (
                    <ProfileCard
                      key={interest}
                      title={interest.charAt(0).toUpperCase() + interest.slice(1)}
                      icon="🔍"
                      archetype={data.current_archetype}
                      confidence={data.confidence || 0}
                      stability={data.stability || 'new'}
                      testsIncluded={data.tests_included || 0}
                      testsExcluded={0}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Current archetype highlight with View Insights */}
            {profile?.current_archetype && (
              <div className="mb-8 p-6 rounded-2xl bg-gradient-to-br from-violet-500/10 to-purple-500/10 border border-violet-500/30">
                <p className="text-sm text-violet-300 mb-2">Most Recent Archetype</p>
                <p className="text-3xl font-bold text-white mb-4">{profile.current_archetype}</p>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handleViewInsights(profile.current_archetype)}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  View Full Insights
                </motion.button>
              </div>
            )}

            {/* Take another test CTA */}
            <div className="mt-8 text-center">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => {
                  onClose();
                  if (onStartTest) onStartTest();
                }}
                className="px-6 py-3 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 text-white font-medium hover:from-violet-500 hover:to-purple-500 transition-all"
              >
                Take Another Test
              </motion.button>
              <p className="text-sm text-neutral-500 mt-3">
                More tests = more accurate profile
              </p>
            </div>
          </>
        )}
      </div>

      {/* Badge detail modal */}
      <AnimatePresence>
        {selectedBadge && (
          <BadgeDetailModal badge={selectedBadge} onClose={() => setSelectedBadge(null)} />
        )}
      </AnimatePresence>
    </motion.div>
  );
}
