import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import * as api from '../api';
import { profileModeToResults, getArchetypeColor } from '../utils/archetypeUtils';

// Mode display config
const modeConfig = {
  hackathon: {
    label: 'Under Pressure',
    icon: '⚡',
    description: 'Team collaboration under pressure'
  },
  overall: {
    label: 'Overall',
    icon: '✨',
    description: 'General personality profile'
  }
};

// Archetype card for public profile
function ArchetypeCard({ mode, interest, archetype, testsIncluded, stability, onClick, isLoading }) {
  const isDeepDive = mode === 'deep_dive';
  const config = isDeepDive ? null : modeConfig[mode];

  const displayLabel = isDeepDive
    ? (interest ? interest.charAt(0).toUpperCase() + interest.slice(1) : 'Deep Dive')
    : (config?.label || mode);

  const displayIcon = isDeepDive ? '🔍' : (config?.icon || '📊');
  const displayColor = getArchetypeColor(archetype) || config?.color || '#a78bfa';

  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      disabled={isLoading}
      className="w-full bg-neutral-900/60 border border-neutral-800 rounded-xl p-4 text-left hover:border-violet-400/50 transition-colors disabled:opacity-50"
    >
      <div className="flex items-center gap-3">
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center text-xl flex-shrink-0"
          style={{ backgroundColor: `${displayColor}20` }}
        >
          {isLoading ? (
            <div className="w-5 h-5 border-2 border-neutral-500 border-t-white rounded-full animate-spin" />
          ) : (
            displayIcon
          )}
        </div>

        <div className="flex-1 min-w-0">
          <span className="text-neutral-400 text-xs">{displayLabel}</span>
          <div
            className="text-base font-semibold truncate"
            style={{ color: displayColor }}
          >
            {archetype || 'Not yet determined'}
          </div>
          <p className="text-neutral-500 text-xs mt-0.5">
            {testsIncluded} test{testsIncluded !== 1 ? 's' : ''}
          </p>
        </div>

        <svg className="w-4 h-4 text-neutral-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </motion.button>
  );
}

export default function PublicProfile() {
  const { username } = useParams();
  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedResults, setSelectedResults] = useState(null);
  const [loadingKey, setLoadingKey] = useState(null);

  useEffect(() => {
    const loadProfile = async () => {
      if (!username) return;

      setIsLoading(true);
      setError(null);

      try {
        const profileData = await api.getPublicProfile(username);
        if (profileData.error) {
          setError(profileData.error);
        } else {
          setProfile(profileData);
        }
      } catch (err) {
        console.error('Failed to load profile:', err);
        setError('Profile not found');
      } finally {
        setIsLoading(false);
      }
    };

    loadProfile();
  }, [username]);

  const handleViewArchetype = async (modeData, mode, interest = null) => {
    const key = interest ? `deep_dive:${interest}` : mode;
    setLoadingKey(key);

    try {
      const resultsData = await profileModeToResults(modeData, mode, interest);
      setSelectedResults(resultsData);
    } catch (err) {
      console.error('Failed to load archetype details:', err);
    } finally {
      setLoadingKey(null);
    }
  };

  const hasAnyData = profile && (
    Object.keys(profile.mode_profiles || {}).length > 0 ||
    Object.keys(profile.deep_dive_profiles || {}).length > 0
  );

  // If viewing a specific archetype result
  if (selectedResults) {
    const archetype = selectedResults.archetype || {};
    const archetypeColor = archetype.color || '#a78bfa';

    return (
      <div className="min-h-screen bg-[#09090b] text-white">
        <div className="max-w-2xl mx-auto px-4 py-8">
          {/* Back button */}
          <button
            onClick={() => setSelectedResults(null)}
            className="flex items-center gap-2 text-neutral-400 hover:text-white transition-colors mb-6"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            <span>Back to profile</span>
          </button>

          {/* Archetype header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-8"
          >
            <div
              className="w-20 h-20 rounded-2xl mx-auto mb-4 flex items-center justify-center text-4xl"
              style={{ backgroundColor: `${archetypeColor}20` }}
            >
              {archetype.emoji || '✨'}
            </div>
            <h1 className="text-3xl font-bold" style={{ color: archetypeColor }}>
              {archetype.name}
            </h1>
            {archetype.tagline && (
              <p className="text-neutral-400 mt-2 italic">{archetype.tagline}</p>
            )}
          </motion.div>

          {/* Description */}
          {archetype.description && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-neutral-900/60 border border-neutral-800 rounded-2xl p-6 mb-6"
            >
              <p className="text-neutral-300 leading-relaxed">{archetype.description}</p>
            </motion.div>
          )}

          {/* Zone of genius */}
          {archetype.zone_of_genius && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-neutral-900/60 border border-neutral-800 rounded-2xl p-6 mb-6"
            >
              <h3 className="text-sm font-medium text-neutral-400 mb-2">Zone of Genius</h3>
              <p className="text-white">{archetype.zone_of_genius}</p>
            </motion.div>
          )}

          {/* Growth opportunity */}
          {archetype.growth_opportunity && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-neutral-900/60 border border-neutral-800 rounded-2xl p-6 mb-6"
            >
              <h3 className="text-sm font-medium text-neutral-400 mb-2">Growth Opportunity</h3>
              <p className="text-white">{archetype.growth_opportunity}</p>
            </motion.div>
          )}

          {/* Team value */}
          {archetype.team_value && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="bg-neutral-900/60 border border-neutral-800 rounded-2xl p-6 mb-6"
            >
              <h3 className="text-sm font-medium text-neutral-400 mb-2">Team Value</h3>
              <p className="text-white">{archetype.team_value}</p>
            </motion.div>
          )}

          {/* CTA */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="text-center mt-8"
          >
            <Link
              to="/"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 text-white font-medium hover:from-violet-500 hover:to-purple-500 transition-all"
            >
              Discover Your Archetype
            </Link>
          </motion.div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#09090b] text-white">
      <div className="max-w-2xl mx-auto px-4 py-8">
        {/* Loading state */}
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin h-10 w-10 border-4 border-violet-500 border-t-transparent rounded-full" />
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="text-center py-20">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-neutral-800 flex items-center justify-center">
              <span className="text-3xl">🔍</span>
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">Profile Not Found</h2>
            <p className="text-neutral-400 mb-6">This profile doesn't exist or is not public.</p>
            <Link
              to="/"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-medium transition-colors"
            >
              Take the Test
            </Link>
          </div>
        )}

        {/* Profile content */}
        {!isLoading && !error && profile && (
          <>
            {/* Header */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center mb-8"
            >
              <div className="w-20 h-20 rounded-full mx-auto mb-4 bg-violet-600 flex items-center justify-center text-white text-2xl font-semibold">
                {(profile.display_name || profile.username || 'U')[0].toUpperCase()}
              </div>
              <h1 className="text-2xl font-bold text-white">{profile.display_name || profile.username}</h1>
              <p className="text-violet-400 mt-1">@{profile.username}</p>
              {profile.total_tests > 0 && (
                <p className="text-neutral-500 text-sm mt-2">
                  {profile.total_tests} test{profile.total_tests !== 1 ? 's' : ''} completed
                </p>
              )}
            </motion.div>

            {/* Archetypes */}
            {hasAnyData && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                <h2 className="text-sm font-medium text-neutral-400 uppercase tracking-wider mb-4">
                  Archetypes
                </h2>
                <div className="space-y-3">
                  {/* Mode profiles */}
                  {Object.entries(profile.mode_profiles || {}).map(([mode, data]) => (
                    <ArchetypeCard
                      key={mode}
                      mode={mode}
                      archetype={data.current_archetype}
                      testsIncluded={data.tests_included || 0}
                      stability={data.stability}
                      onClick={() => handleViewArchetype(data, mode)}
                      isLoading={loadingKey === mode}
                    />
                  ))}

                  {/* Deep dive profiles */}
                  {Object.entries(profile.deep_dive_profiles || {}).map(([interest, data]) => (
                    <ArchetypeCard
                      key={`deep_dive:${interest}`}
                      mode="deep_dive"
                      interest={interest}
                      archetype={data.current_archetype}
                      testsIncluded={data.tests_included || 0}
                      stability={data.stability}
                      onClick={() => handleViewArchetype(data, 'deep_dive', interest)}
                      isLoading={loadingKey === `deep_dive:${interest}`}
                    />
                  ))}
                </div>
              </motion.div>
            )}

            {/* No data */}
            {!hasAnyData && (
              <div className="text-center py-12">
                <p className="text-neutral-400">No archetypes to display yet.</p>
              </div>
            )}

            {/* CTA */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="text-center mt-10"
            >
              <Link
                to="/"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 text-white font-medium hover:from-violet-500 hover:to-purple-500 transition-all"
              >
                Discover Your Archetype
              </Link>
              <p className="text-sm text-neutral-500 mt-3">
                Find out what makes you unique
              </p>
            </motion.div>
          </>
        )}
      </div>
    </div>
  );
}
