import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import * as api from '../api';

// Stability badge component
function StabilityBadge({ stability, size = 'md' }) {
  const config = {
    stable: { label: 'Stable', color: '#22c55e', icon: '✓', description: 'Consistent results' },
    converging: { label: 'Converging', color: '#eab308', icon: '→', description: 'Becoming clearer' },
    inconsistent: { label: 'Variable', color: '#f97316', icon: '~', description: 'Results vary' },
    new: { label: 'New', color: '#a78bfa', icon: '★', description: 'Take more tests' },
  };

  const { label, color, icon, description } = config[stability] || config.new;
  const sizeClass = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-3 py-1';

  return (
    <div
      className={`inline-flex items-center gap-1.5 rounded-full font-medium ${sizeClass}`}
      style={{ backgroundColor: `${color}20`, color }}
      title={description}
    >
      <span>{icon}</span>
      <span>{label}</span>
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
  hackathon: { label: 'Hackathon', icon: '🚀', description: 'Team collaboration under pressure' },
  overall: { label: 'Overall', icon: '✨', description: 'General personality profile' },
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
  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

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
          setProfile(fullProfile);
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
              {profile?.member_since && (
                <p className="text-sm text-neutral-500 mt-1">
                  Member since {new Date(profile.member_since * 1000).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                </p>
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

            {/* Current archetype highlight */}
            {profile?.current_archetype && (
              <div className="mb-8 p-6 rounded-2xl bg-gradient-to-br from-violet-500/10 to-purple-500/10 border border-violet-500/30">
                <p className="text-sm text-violet-300 mb-2">Most Recent Archetype</p>
                <p className="text-3xl font-bold text-white">{profile.current_archetype}</p>
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
    </motion.div>
  );
}
