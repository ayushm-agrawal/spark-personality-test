import { useState } from 'react';
import { motion } from 'framer-motion';
import { profileModeToResults, getArchetypeColor } from '../utils/archetypeUtils';
import StabilityBadge from './shared/StabilityBadge';

// Mode display config
const modeConfig = {
  hackathon: {
    label: 'Under Pressure',
    icon: '⚡',
    color: '#fb923c',
    description: 'Team collaboration under pressure'
  },
  overall: {
    label: 'Overall',
    icon: '✨',
    color: '#a78bfa',
    description: 'General personality profile'
  }
};

// Individual archetype card (clickable)
function ArchetypeCard({ mode, interest, archetype, testsIncluded, stability, color, onClick, isLoading }) {
  const isDeepDive = mode === 'deep_dive';
  const config = isDeepDive ? null : modeConfig[mode];

  // For deep dive, show interest name; otherwise show mode label
  const displayLabel = isDeepDive
    ? (interest ? interest.charAt(0).toUpperCase() + interest.slice(1) : 'Deep Dive')
    : (config?.label || mode);

  const displayIcon = isDeepDive ? '🔍' : (config?.icon || '📊');
  const displayColor = color || getArchetypeColor(archetype) || config?.color || '#a78bfa';

  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      disabled={isLoading}
      className="w-full bg-neutral-900/60 border border-neutral-800 rounded-xl p-4 text-left hover:border-violet-400/50 transition-colors disabled:opacity-50"
    >
      <div className="flex items-center gap-3">
        {/* Icon */}
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

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span className="text-neutral-400 text-xs">{displayLabel}</span>
            {stability && <StabilityBadge stability={stability} />}
          </div>
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

        {/* Arrow */}
        <svg className="w-4 h-4 text-neutral-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </motion.button>
  );
}

// Fallback for no holistic profile (use latest result per mode)
function FallbackArchetypeCard({ assessment, onClick }) {
  const mode = assessment.mode;
  const interest = assessment.modeSpecific?.interest;
  const isDeepDive = mode === 'deep_dive';
  const config = isDeepDive ? null : modeConfig[mode];

  const displayLabel = isDeepDive
    ? (interest ? interest.charAt(0).toUpperCase() + interest.slice(1) : 'Deep Dive')
    : (config?.label || mode);

  const displayIcon = isDeepDive ? '🔍' : (config?.icon || '📊');
  const color = assessment.archetype?.color || config?.color || '#a78bfa';

  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className="w-full bg-neutral-900/60 border border-neutral-800 rounded-xl p-4 text-left hover:border-violet-400/50 transition-colors"
    >
      <div className="flex items-center gap-3">
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center text-xl flex-shrink-0"
          style={{ backgroundColor: `${color}20` }}
        >
          {displayIcon}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span className="text-neutral-400 text-xs">{displayLabel}</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-neutral-800 text-neutral-400">Latest</span>
          </div>
          <div
            className="text-base font-semibold truncate"
            style={{ color }}
          >
            {assessment.archetype?.name || 'Unknown'}
          </div>
          <p className="text-neutral-500 text-xs mt-0.5">
            {assessment.completedAt?.toLocaleDateString()}
          </p>
        </div>

        <svg className="w-4 h-4 text-neutral-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </motion.button>
  );
}

export default function YourArchetypes({
  holisticProfile = null,
  userHistory = [],
  onViewArchetype,
  onViewGallery
}) {
  const [loadingKey, setLoadingKey] = useState(null);

  // If we have holistic profile data, use it
  const hasHolisticData = holisticProfile && (
    Object.keys(holisticProfile.mode_profiles || {}).length > 0 ||
    Object.keys(holisticProfile.deep_dive_profiles || {}).length > 0
  );

  // Handle click on holistic profile card - transform data for Results page
  const handleProfileClick = async (modeData, mode, interest = null) => {
    if (!onViewArchetype) return;

    const key = interest ? `deep_dive:${interest}` : mode;
    setLoadingKey(key);

    try {
      const resultsData = await profileModeToResults(modeData, mode, interest);
      onViewArchetype(resultsData);
    } catch (err) {
      console.error('Failed to load archetype details:', err);
    } finally {
      setLoadingKey(null);
    }
  };

  // If no holistic data, fall back to grouping userHistory by mode
  const groupedHistory = {};
  if (!hasHolisticData && userHistory.length > 0) {
    userHistory.forEach(assessment => {
      const mode = assessment.mode;
      const interest = assessment.modeSpecific?.interest;
      const key = mode === 'deep_dive' && interest ? `deep_dive:${interest}` : mode;

      // Keep only the most recent per mode/interest
      if (!groupedHistory[key]) {
        groupedHistory[key] = assessment;
      }
    });
  }

  // No data at all
  if (!hasHolisticData && Object.keys(groupedHistory).length === 0) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="w-full"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white text-sm font-medium">Your Archetypes</h3>
        {onViewGallery && (
          <button
            onClick={onViewGallery}
            className="inline-flex items-center gap-1.5 text-xs text-violet-400 hover:text-violet-300 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            <span className="hidden sm:inline">All Archetypes</span>
          </button>
        )}
      </div>

      <div className="space-y-3">
        {/* Render from holistic profile if available */}
        {hasHolisticData && (
          <>
            {/* Mode profiles (hackathon, overall) */}
            {Object.entries(holisticProfile.mode_profiles || {}).map(([mode, data]) => (
              <ArchetypeCard
                key={mode}
                mode={mode}
                archetype={data.current_archetype}
                testsIncluded={data.tests_included || 0}
                stability={data.stability}
                onClick={() => handleProfileClick(data, mode)}
                isLoading={loadingKey === mode}
              />
            ))}

            {/* Deep dive profiles (by interest) */}
            {Object.entries(holisticProfile.deep_dive_profiles || {}).map(([interest, data]) => (
              <ArchetypeCard
                key={`deep_dive:${interest}`}
                mode="deep_dive"
                interest={interest}
                archetype={data.current_archetype}
                testsIncluded={data.tests_included || 1}
                stability={data.stability}
                color="#2dd4bf"
                onClick={() => handleProfileClick(data, 'deep_dive', interest)}
                isLoading={loadingKey === `deep_dive:${interest}`}
              />
            ))}
          </>
        )}

        {/* Fallback to grouped history if no holistic data */}
        {!hasHolisticData && Object.entries(groupedHistory).map(([key, assessment]) => (
          <FallbackArchetypeCard
            key={key}
            assessment={assessment}
            onClick={() => onViewArchetype?.(assessment)}
          />
        ))}
      </div>
    </motion.div>
  );
}
