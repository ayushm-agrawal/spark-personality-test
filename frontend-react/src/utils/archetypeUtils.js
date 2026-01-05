import * as api from '../api';

// Cache for archetype data
let archetypeCache = null;

/**
 * Get all archetypes (cached)
 */
export async function getArchetypes() {
  if (!archetypeCache) {
    archetypeCache = await api.getArchetypes();
  }
  return archetypeCache;
}

/**
 * Get a single archetype by name
 */
export async function getArchetypeByName(name) {
  const response = await getArchetypes();
  // API returns {archetypes: {"The Architect": {...}, ...}}
  const archetypeData = response.archetypes?.[name];
  if (archetypeData) {
    return { name, ...archetypeData };
  }
  return null;
}

/**
 * Transform holistic profile mode data into Results-compatible format
 * @param {object} modeData - Data from mode_profiles or deep_dive_profiles
 * @param {string} mode - The mode ('hackathon', 'overall', 'deep_dive')
 * @param {string} interest - Optional interest for deep_dive mode
 * @returns {Promise<object>} - Results-compatible object
 */
export async function profileModeToResults(modeData, mode, interest = null) {
  const archetypeName = modeData.current_archetype;

  // Get full archetype details
  let archetypeDetails = null;
  try {
    archetypeDetails = await getArchetypeByName(archetypeName);
  } catch (err) {
    console.error('Failed to fetch archetype details:', err);
  }

  // Build normalized scores from weighted_scores
  const normalizedScores = {};
  if (modeData.weighted_scores) {
    Object.entries(modeData.weighted_scores).forEach(([trait, data]) => {
      // weighted_scores has structure: { trait: { weight_total, weighted_sum } }
      // weighted_sum already contains values weighted by 0-100 scores
      if (data && typeof data === 'object' && data.weight_total > 0) {
        normalizedScores[trait] = data.weighted_sum / data.weight_total;
      } else if (typeof data === 'number') {
        normalizedScores[trait] = data;
      }
    });
  }

  // Also handle "Emotional_Stability" -> "Stability" mapping for frontend
  if (normalizedScores.Emotional_Stability && !normalizedScores.Stability) {
    normalizedScores.Stability = normalizedScores.Emotional_Stability;
  }

  // If no weighted scores, use archetype's default profile
  if (Object.keys(normalizedScores).length === 0 && archetypeDetails?.big_five_profile) {
    Object.entries(archetypeDetails.big_five_profile).forEach(([trait, value]) => {
      normalizedScores[trait] = value;
    });
    if (normalizedScores.Emotional_Stability && !normalizedScores.Stability) {
      normalizedScores.Stability = normalizedScores.Emotional_Stability;
    }
  }

  // Build the results object
  const results = {
    test_complete: true,
    mode: mode,
    archetype: archetypeDetails ? {
      name: archetypeDetails.name,
      emoji: archetypeDetails.emoji || '✨',
      color: archetypeDetails.color || '#a78bfa',
      tagline: archetypeDetails.tagline || '',
      description: archetypeDetails.description || '',
      zone_of_genius: archetypeDetails.zone_of_genius || '',
      deepest_aspiration: archetypeDetails.deepest_aspiration || '',
      growth_opportunity: archetypeDetails.growth_opportunity || '',
      team_value: archetypeDetails.team_value || '',
      ideal_partners: archetypeDetails.ideal_partners || [],
      creative_partner: archetypeDetails.creative_partner || '',
      hackathon_superpower: archetypeDetails.hackathon_superpower || '',
      hackathon_pitfall: archetypeDetails.hackathon_pitfall || '',
    } : {
      name: archetypeName,
      emoji: '✨',
      color: '#a78bfa',
    },
    archetype_confidence: modeData.confidence || 50,
    confidence: {
      tier: modeData.stability === 'stable' ? 'clear' : 'emerging',
      confidence_pct: modeData.confidence || 50,
    },
    normalized_scores: normalizedScores,
    mode_specific: {
      interest: interest,
    },
    // Mark this as a profile view (not a fresh test result)
    is_profile_view: true,
    profile_data: {
      tests_included: modeData.tests_included || 0,
      tests_excluded: modeData.tests_excluded || 0,
      stability: modeData.stability,
    }
  };

  return results;
}

// Archetype colors for consistent styling
export const archetypeColors = {
  'The Architect': '#60a5fa',
  'The Catalyst': '#f97316',
  'The Strategist': '#8b5cf6',
  'The Guide': '#22c55e',
  'The Alchemist': '#eab308',
  'The Gardener': '#10b981',
  'The Luminary': '#f59e0b',
  'The Sentinel': '#6366f1',
};

// Get color for an archetype
export function getArchetypeColor(name) {
  return archetypeColors[name] || '#a78bfa';
}
