import { useState } from 'react';
import { motion } from 'framer-motion';

const archetypeEmojis = {
  Visionary: '🌟',
  Operator: '⚙️',
  Catalyst: '🤝',
  Pragmatist: '🎯',
  Explorer: '🗺️'
};

const archetypeColors = {
  Visionary: 'from-yellow-400 to-orange-500',
  Operator: 'from-blue-400 to-cyan-500',
  Catalyst: 'from-green-400 to-emerald-500',
  Pragmatist: 'from-purple-400 to-indigo-500',
  Explorer: 'from-pink-400 to-rose-500'
};

// Simple radar chart component
function RadarChart({ scores }) {
  const traits = Object.keys(scores);
  const numTraits = traits.length;
  const angleStep = (2 * Math.PI) / numTraits;
  const centerX = 150;
  const centerY = 150;
  const maxRadius = 100;

  // Calculate points for each trait
  const points = traits.map((trait, i) => {
    const angle = angleStep * i - Math.PI / 2; // Start from top
    const value = scores[trait] / 100; // Normalize to 0-1
    const r = value * maxRadius;
    return {
      x: centerX + r * Math.cos(angle),
      y: centerY + r * Math.sin(angle),
      label: trait.replace('_', ' '),
      value: scores[trait],
      labelX: centerX + (maxRadius + 40) * Math.cos(angle),
      labelY: centerY + (maxRadius + 40) * Math.sin(angle)
    };
  });

  // Create path for the polygon
  const pathData = points.map((p, i) =>
    `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`
  ).join(' ') + ' Z';

  // Grid circles
  const gridCircles = [0.25, 0.5, 0.75, 1].map(r => r * maxRadius);

  return (
    <svg viewBox="0 0 300 300" className="w-full max-w-xs mx-auto">
      {/* Grid circles */}
      {gridCircles.map((r, i) => (
        <circle
          key={i}
          cx={centerX}
          cy={centerY}
          r={r}
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth="1"
        />
      ))}

      {/* Grid lines */}
      {traits.map((_, i) => {
        const angle = angleStep * i - Math.PI / 2;
        return (
          <line
            key={i}
            x1={centerX}
            y1={centerY}
            x2={centerX + maxRadius * Math.cos(angle)}
            y2={centerY + maxRadius * Math.sin(angle)}
            stroke="rgba(255,255,255,0.1)"
            strokeWidth="1"
          />
        );
      })}

      {/* Data polygon */}
      <motion.path
        d={pathData}
        fill="rgba(139, 92, 246, 0.3)"
        stroke="rgb(139, 92, 246)"
        strokeWidth="2"
        initial={{ opacity: 0, scale: 0.5 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8, delay: 0.3 }}
      />

      {/* Data points */}
      {points.map((p, i) => (
        <motion.circle
          key={i}
          cx={p.x}
          cy={p.y}
          r="5"
          fill="rgb(139, 92, 246)"
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.5 + i * 0.1 }}
        />
      ))}

      {/* Labels */}
      {points.map((p, i) => (
        <text
          key={i}
          x={p.labelX}
          y={p.labelY}
          textAnchor="middle"
          dominantBaseline="middle"
          fill="rgba(255,255,255,0.7)"
          fontSize="10"
          className="font-medium"
        >
          {p.label}
        </text>
      ))}
    </svg>
  );
}

function StarRating({ rating, onRate }) {
  return (
    <div className="flex gap-2">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          onClick={() => onRate(star)}
          className={`text-3xl transition-transform hover:scale-110 ${
            star <= rating ? 'text-yellow-400' : 'text-gray-600'
          }`}
        >
          ★
        </button>
      ))}
    </div>
  );
}

export default function Results({ results, onFeedback }) {
  const [rating, setRating] = useState(0);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  if (!results) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-12 w-12 border-4 border-purple-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  const {
    suggested_archetype: archetype,
    archetype_confidence: confidence,
    normalized_scores: scores,
    trait_breakdown: traitBreakdown,
    all_matches: allMatches,
    archetype_description: description,
    compatibility
  } = results;

  const handleRate = async (stars) => {
    setRating(stars);
    if (!feedbackSubmitted) {
      await onFeedback(stars - 1);
      setFeedbackSubmitted(true);
    }
  };

  return (
    <div className="min-h-screen px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Archetype reveal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.3, type: 'spring', stiffness: 200 }}
            className={`w-24 h-24 mx-auto mb-6 rounded-2xl bg-gradient-to-br ${archetypeColors[archetype] || 'from-purple-500 to-pink-500'} flex items-center justify-center text-5xl`}
          >
            {archetypeEmojis[archetype] || '✨'}
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="text-4xl md:text-5xl font-bold mb-3 gradient-text"
          >
            You're a {archetype}!
          </motion.h1>

          {confidence !== undefined && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.7 }}
              className="text-gray-400"
            >
              {confidence > 70 ? 'Strong match' : confidence > 40 ? 'Good match' : 'Emerging profile'} ({Math.round(confidence)}% confidence)
            </motion.p>
          )}
        </motion.div>

        {/* Trait radar chart */}
        {scores && (
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="glass-card p-6 mb-8"
          >
            <h2 className="text-xl font-semibold text-white mb-4 text-center">Your Trait Profile</h2>
            <RadarChart scores={scores} />

            {/* Trait breakdown */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mt-6">
              {traitBreakdown && Object.entries(traitBreakdown).map(([trait, data]) => (
                <div key={trait} className="text-center p-3 rounded-lg bg-white/5">
                  <p className="text-xs text-gray-400 mb-1">{trait.replace('_', ' ')}</p>
                  <p className="text-lg font-semibold text-white">{Math.round(data.score)}</p>
                  <p className="text-xs text-purple-400">{data.level}</p>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Description sections */}
        {description && (
          <div className="space-y-6 mb-8">
            {description.overview && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 1 }}
                className="glass-card p-6"
              >
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                  ✨ Overview
                </h3>
                <p className="text-gray-300 leading-relaxed">{description.overview}</p>
              </motion.div>
            )}

            {description.team_work_style && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 1.1 }}
                className="glass-card p-6"
              >
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                  🤝 How You Work in Teams
                </h3>
                <p className="text-gray-300 leading-relaxed">{description.team_work_style}</p>
              </motion.div>
            )}

            {description.ideal_team_situation && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 1.2 }}
                className="glass-card p-6"
              >
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                  🚀 Where You Excel
                </h3>
                <p className="text-gray-300 leading-relaxed">{description.ideal_team_situation}</p>
              </motion.div>
            )}

            {description.compatible_archetypes && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 1.3 }}
                className="glass-card p-6"
              >
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                  💫 Best Team Partners
                </h3>
                {typeof description.compatible_archetypes === 'object' ? (
                  <div className="space-y-3">
                    {Object.entries(description.compatible_archetypes).map(([arch, reason]) => (
                      <div key={arch} className="flex items-start gap-3">
                        <span className="text-2xl">{archetypeEmojis[arch] || '✨'}</span>
                        <div>
                          <p className="font-medium text-white">{arch}</p>
                          <p className="text-gray-400 text-sm">{reason}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-300">{description.compatible_archetypes}</p>
                )}
              </motion.div>
            )}
          </div>
        )}

        {/* All archetype matches */}
        {allMatches && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.4 }}
            className="glass-card p-6 mb-8"
          >
            <h3 className="text-lg font-semibold text-white mb-4">All Archetype Matches</h3>
            <div className="space-y-3">
              {Object.entries(allMatches).map(([arch, score], index) => (
                <div key={arch} className="flex items-center gap-3">
                  <span className="text-xl w-8">{archetypeEmojis[arch] || '✨'}</span>
                  <span className="w-24 text-gray-300">{arch}</span>
                  <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
                    <motion.div
                      className={`h-full ${index === 0 ? 'bg-purple-500' : 'bg-gray-500'}`}
                      initial={{ width: 0 }}
                      animate={{ width: `${score}%` }}
                      transition={{ delay: 1.5 + index * 0.1, duration: 0.5 }}
                    />
                  </div>
                  <span className="text-gray-400 w-12 text-right">{Math.round(score)}%</span>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Feedback */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.6 }}
          className="text-center py-8"
        >
          <p className="text-gray-400 mb-4">How was your experience?</p>
          <StarRating rating={rating} onRate={handleRate} />
          {feedbackSubmitted && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-green-400 mt-3"
            >
              Thanks for your feedback!
            </motion.p>
          )}
        </motion.div>

        {/* Share button */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.8 }}
          className="text-center pb-8"
        >
          <button
            onClick={() => {
              const text = `I'm a ${archetype}! ${archetypeEmojis[archetype]} Discover your team archetype at Ception`;
              navigator.clipboard.writeText(text);
            }}
            className="px-6 py-3 rounded-xl bg-white/10 text-white hover:bg-white/20 transition-colors"
          >
            📋 Copy to Share
          </button>
        </motion.div>
      </div>
    </div>
  );
}
