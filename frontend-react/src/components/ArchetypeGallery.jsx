import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import * as api from '../api';

// Archetype symbols for visual identity
const ArchetypeSymbols = {
  'The Architect': ({ size = 48, color }) => (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none">
      <rect x="14" y="20" width="8" height="14" stroke={color} strokeWidth="1.5" fill={`${color}15`} />
      <rect x="22" y="14" width="12" height="20" stroke={color} strokeWidth="1.5" fill={`${color}20`} />
      <path d="M14 20 L24 10 L34 20" stroke={color} strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  'The Catalyst': ({ size = 48, color }) => (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none">
      <path d="M24 6 L26 18 L38 16 L28 24 L36 36 L24 28 L12 36 L20 24 L10 16 L22 18 Z" stroke={color} strokeWidth="1.5" fill={`${color}20`} />
      <circle cx="24" cy="22" r="4" fill={color} />
    </svg>
  ),
  'The Strategist': ({ size = 48, color }) => (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none">
      <path d="M18 38 L18 24 Q18 16 24 14 L24 12 Q30 12 30 18 L32 18 Q38 22 34 30 L34 38 Z" stroke={color} strokeWidth="1.5" fill={`${color}15`} />
      <circle cx="25" cy="20" r="2" fill={color} />
      <path d="M12 30 L36 30 M12 22 L36 22" stroke={color} strokeWidth="1" opacity="0.3" />
    </svg>
  ),
  'The Guide': ({ size = 48, color }) => (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none">
      <circle cx="24" cy="24" r="14" stroke={color} strokeWidth="1.5" fill="none" />
      <path d="M24 8 L26 22 L24 24 L22 22 Z" fill={color} />
      <path d="M24 40 L22 26 L24 24 L26 26 Z" fill={`${color}60`} />
      <path d="M8 24 L22 22 L24 24 L22 26 Z" fill={`${color}60`} />
      <path d="M40 24 L26 26 L24 24 L26 22 Z" fill={`${color}60`} />
      <circle cx="24" cy="24" r="3" fill={color} />
    </svg>
  ),
  'The Alchemist': ({ size = 48, color }) => (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none">
      <path d="M20 12 L20 22 L14 36 Q12 40 18 40 L30 40 Q36 40 34 36 L28 22 L28 12" stroke={color} strokeWidth="1.5" fill={`${color}15`} />
      <path d="M19 12 L29 12" stroke={color} strokeWidth="2" strokeLinecap="round" />
      <circle cx="21" cy="32" r="2" fill={color} opacity="0.6" />
      <circle cx="27" cy="34" r="1.5" fill={color} opacity="0.4" />
      <circle cx="24" cy="30" r="1" fill={color} opacity="0.8" />
    </svg>
  ),
  'The Gardener': ({ size = 48, color }) => (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none">
      <path d="M24 40 L24 22" stroke={color} strokeWidth="2" strokeLinecap="round" />
      <path d="M24 22 Q20 18 16 20 Q14 22 18 26 Q22 24 24 22" fill={color} opacity="0.6" />
      <path d="M24 22 Q28 18 32 20 Q34 22 30 26 Q26 24 24 22" fill={color} opacity="0.6" />
      <path d="M24 16 Q24 10 24 8" stroke={color} strokeWidth="2" strokeLinecap="round" />
      <path d="M24 14 Q20 12 18 14 Q18 18 22 18 Q24 16 24 14" fill={color} />
      <path d="M24 14 Q28 12 30 14 Q30 18 26 18 Q24 16 24 14" fill={color} />
      <ellipse cx="24" cy="42" rx="8" ry="2" fill={color} opacity="0.3" />
    </svg>
  ),
  'The Luminary': ({ size = 48, color }) => (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none">
      <circle cx="24" cy="24" r="8" fill={color} opacity="0.3" />
      <circle cx="24" cy="24" r="5" fill={color} />
      {[0, 45, 90, 135, 180, 225, 270, 315].map((angle, i) => (
        <line
          key={i}
          x1={24 + Math.cos(angle * Math.PI / 180) * 12}
          y1={24 + Math.sin(angle * Math.PI / 180) * 12}
          x2={24 + Math.cos(angle * Math.PI / 180) * 18}
          y2={24 + Math.sin(angle * Math.PI / 180) * 18}
          stroke={color}
          strokeWidth="2"
          strokeLinecap="round"
        />
      ))}
    </svg>
  ),
  'The Sentinel': ({ size = 48, color }) => (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none">
      <path d="M24 6 L38 14 L38 28 Q38 38 24 44 Q10 38 10 28 L10 14 Z" stroke={color} strokeWidth="1.5" fill={`${color}15`} />
      <path d="M24 12 L32 16 L32 26 Q32 32 24 36 Q16 32 16 26 L16 16 Z" stroke={color} strokeWidth="1" fill={`${color}20`} />
      <circle cx="24" cy="24" r="3" fill={color} />
    </svg>
  ),
};

// Fun facts and additional details for each archetype
const archetypeExtras = {
  'The Architect': {
    funFact: "Architects often find themselves reorganizing their environment before they can focus on creative work.",
    famousExamples: "Think Elon Musk's systematic approach or Marie Kondo's structured philosophy.",
    bestEnvironment: "Clean desk, clear mind. You thrive with systems and dedicated workspaces.",
    stressSign: "When you start making spreadsheets for your spreadsheets.",
  },
  'The Catalyst': {
    funFact: "Catalysts are often responsible for the 'crazy idea that actually worked' at companies.",
    famousExamples: "Think Richard Branson's bold moves or Lady Gaga's reinventions.",
    bestEnvironment: "Dynamic spaces with lots of stimulation and opportunities for spontaneous collaboration.",
    stressSign: "When you can't sit still and everything feels too slow.",
  },
  'The Strategist': {
    funFact: "Strategists often visualize scenarios in their head like a chess game before making decisions.",
    famousExamples: "Think Warren Buffett's calculated moves or Serena Williams' match preparation.",
    bestEnvironment: "Quiet spaces for deep thinking with access to data and information.",
    stressSign: "When you start seeing threats in every scenario and can't relax.",
  },
  'The Guide': {
    funFact: "Guides often remember details about people that others forget—they're natural connectors.",
    famousExamples: "Think Oprah's empathetic interviews or Mr. Rogers' gentle wisdom.",
    bestEnvironment: "Collaborative settings where you can mentor and support others.",
    stressSign: "When you're so focused on others' needs that you forget your own.",
  },
  'The Alchemist': {
    funFact: "Alchemists often have breakthrough ideas in unusual places—showers, walks, or at 3am.",
    famousExamples: "Think David Bowie's transformations or Miyazaki's imaginative worlds.",
    bestEnvironment: "Private creative spaces with room for experimentation and no judgment.",
    stressSign: "When nothing feels original and everything seems derivative.",
  },
  'The Gardener': {
    funFact: "Gardeners are the ones who remember to water the office plant and check in on quiet teammates.",
    famousExamples: "Think Dolly Parton's consistent generosity or Keanu Reeves' steady kindness.",
    bestEnvironment: "Stable, supportive teams where long-term growth is valued over quick wins.",
    stressSign: "When you're exhausted from taking care of everyone but yourself.",
  },
  'The Luminary': {
    funFact: "Luminaries can often articulate what everyone's feeling but nobody has said yet.",
    famousExamples: "Think Steve Jobs' reality distortion field or Martin Luther King Jr.'s visions.",
    bestEnvironment: "Stages, platforms, and spaces where big ideas are welcomed.",
    stressSign: "When your ideas feel too big for anyone to understand.",
  },
  'The Sentinel': {
    funFact: "Sentinels are often the last ones to leave during a crisis—they're the steady hands.",
    famousExamples: "Think Tom Hanks' reliable presence or Ruth Bader Ginsburg's unwavering commitment.",
    bestEnvironment: "Predictable structures where your reliability can shine.",
    stressSign: "When you feel like the only responsible one and can't trust anyone else.",
  },
};

// Trait labels for display
const traitLabels = {
  'Openness': { short: 'Open', color: '#fdba74' },
  'Conscientiousness': { short: 'Focus', color: '#c4b5fd' },
  'Extraversion': { short: 'Social', color: '#67e8f9' },
  'Agreeableness': { short: 'Warm', color: '#86efac' },
  'Emotional_Stability': { short: 'Calm', color: '#f9a8d4' },
};

function ArchetypeCard({ archetype, isExpanded, onToggle }) {
  const Symbol = ArchetypeSymbols[archetype.name];
  const extras = archetypeExtras[archetype.name] || {};
  const traits = archetype.big_five_profile || {};

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl overflow-hidden"
      style={{
        background: `linear-gradient(135deg, ${archetype.color}15 0%, transparent 50%)`,
        border: `1px solid ${archetype.color}30`,
      }}
    >
      {/* Header - always visible */}
      <button
        onClick={onToggle}
        className="w-full p-5 text-left flex items-start gap-4 hover:bg-white/5 transition-colors"
      >
        <div
          className="flex-shrink-0 w-14 h-14 rounded-xl flex items-center justify-center"
          style={{ backgroundColor: `${archetype.color}20` }}
        >
          {Symbol && <Symbol size={40} color={archetype.color} />}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">{archetype.emoji}</span>
            <h3 className="text-lg font-bold" style={{ color: archetype.color }}>
              {archetype.name}
            </h3>
          </div>
          <p className="text-neutral-400 text-sm italic">"{archetype.tagline}"</p>
        </div>

        <motion.svg
          className="w-5 h-5 text-neutral-500 flex-shrink-0 mt-1"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          animate={{ rotate: isExpanded ? 180 : 0 }}
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </motion.svg>
      </button>

      {/* Expanded content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-5 space-y-5">
              {/* Description */}
              <p className="text-neutral-300 text-sm leading-relaxed">
                {archetype.description}
              </p>

              {/* Trait Profile */}
              <div className="bg-neutral-900/50 rounded-xl p-4">
                <h4 className="text-xs text-neutral-500 uppercase tracking-wider mb-3">Trait Profile</h4>
                <div className="space-y-2">
                  {Object.entries(traits).map(([trait, value]) => (
                    <div key={trait} className="flex items-center gap-3">
                      <span className="text-xs text-neutral-400 w-12" style={{ color: traitLabels[trait]?.color }}>
                        {traitLabels[trait]?.short || trait}
                      </span>
                      <div className="flex-1 h-2 bg-neutral-800 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${value}%` }}
                          transition={{ duration: 0.5, delay: 0.1 }}
                          className="h-full rounded-full"
                          style={{ backgroundColor: traitLabels[trait]?.color || archetype.color }}
                        />
                      </div>
                      <span className="text-xs text-neutral-500 w-8 text-right">{value}%</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Key Insights */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="bg-neutral-900/50 rounded-xl p-4">
                  <h4 className="text-xs text-neutral-500 uppercase tracking-wider mb-2">Zone of Genius</h4>
                  <p className="text-sm text-neutral-300">{archetype.zone_of_genius}</p>
                </div>
                <div className="bg-neutral-900/50 rounded-xl p-4">
                  <h4 className="text-xs text-neutral-500 uppercase tracking-wider mb-2">Deepest Aspiration</h4>
                  <p className="text-sm text-neutral-300">{archetype.deepest_aspiration}</p>
                </div>
                <div className="bg-neutral-900/50 rounded-xl p-4">
                  <h4 className="text-xs text-neutral-500 uppercase tracking-wider mb-2">Growth Edge</h4>
                  <p className="text-sm text-neutral-300">{archetype.growth_opportunity}</p>
                </div>
                <div className="bg-neutral-900/50 rounded-xl p-4">
                  <h4 className="text-xs text-neutral-500 uppercase tracking-wider mb-2">Team Superpower</h4>
                  <p className="text-sm text-neutral-300">{archetype.team_value}</p>
                </div>
              </div>

              {/* Fun Extras */}
              {extras.funFact && (
                <div className="bg-gradient-to-r from-neutral-900/80 to-transparent rounded-xl p-4 border-l-2" style={{ borderColor: archetype.color }}>
                  <h4 className="text-xs uppercase tracking-wider mb-2" style={{ color: archetype.color }}>Fun Fact</h4>
                  <p className="text-sm text-neutral-300">{extras.funFact}</p>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {extras.bestEnvironment && (
                  <div className="bg-neutral-900/30 rounded-xl p-4">
                    <h4 className="text-xs text-neutral-500 uppercase tracking-wider mb-2">Best Environment</h4>
                    <p className="text-sm text-neutral-400">{extras.bestEnvironment}</p>
                  </div>
                )}
                {extras.stressSign && (
                  <div className="bg-neutral-900/30 rounded-xl p-4">
                    <h4 className="text-xs text-neutral-500 uppercase tracking-wider mb-2">Stress Sign</h4>
                    <p className="text-sm text-neutral-400">{extras.stressSign}</p>
                  </div>
                )}
              </div>

              {/* Creative Partners */}
              <div className="flex flex-wrap gap-2">
                <span className="text-xs text-neutral-500">Best creative partners:</span>
                {archetype.ideal_partners?.map((partner) => (
                  <span
                    key={partner}
                    className="text-xs px-2 py-1 rounded-full bg-neutral-800 text-neutral-300"
                  >
                    {partner}
                  </span>
                ))}
              </div>

              {/* Hackathon Mode */}
              {archetype.hackathon_superpower && (
                <div className="bg-orange-500/10 rounded-xl p-4 border border-orange-500/20">
                  <h4 className="text-xs text-orange-400 uppercase tracking-wider mb-2">⚡ In a Hackathon</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-neutral-500">Superpower: </span>
                      <span className="text-neutral-300">{archetype.hackathon_superpower}</span>
                    </div>
                    <div>
                      <span className="text-neutral-500">Watch out for: </span>
                      <span className="text-neutral-300">{archetype.hackathon_pitfall}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default function ArchetypeGallery({ onClose, userArchetype }) {
  const [archetypes, setArchetypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);
  const [filter, setFilter] = useState('all'); // all, yours, compatible

  useEffect(() => {
    api.getArchetypes()
      .then((data) => {
        // Transform the object to array with names
        const archetypeList = Object.entries(data.archetypes || data).map(([name, details]) => ({
          name,
          ...details,
        }));
        setArchetypes(archetypeList);

        // If user has an archetype, expand it by default
        if (userArchetype) {
          setExpandedId(userArchetype);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [userArchetype]);

  const filteredArchetypes = archetypes.filter((a) => {
    if (filter === 'all') return true;
    if (filter === 'yours' && userArchetype) return a.name === userArchetype;
    if (filter === 'compatible' && userArchetype) {
      const userArch = archetypes.find((arch) => arch.name === userArchetype);
      return userArch?.ideal_partners?.includes(a.name) || userArch?.growth_partners?.includes(a.name);
    }
    return true;
  });

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-[#09090b] overflow-y-auto"
    >
      {/* Header */}
      <div className="sticky top-0 z-10 bg-[#09090b]/95 backdrop-blur-sm border-b border-neutral-800">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">The Archetypes</h1>
            <p className="text-neutral-500 text-sm">8 creative personalities, infinite possibilities</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-neutral-400 hover:text-white transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Filter tabs - only show if user has an archetype */}
        {userArchetype && (
          <div className="max-w-4xl mx-auto px-4 pb-3 flex gap-2">
            {[
              { id: 'all', label: 'All Archetypes' },
              { id: 'yours', label: 'Yours' },
              { id: 'compatible', label: 'Compatible' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setFilter(tab.id)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                  filter === tab.id
                    ? 'bg-violet-500/20 text-violet-300 border border-violet-500/30'
                    : 'bg-neutral-800 text-neutral-400 border border-transparent hover:bg-neutral-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin h-8 w-8 border-2 border-violet-500 border-t-transparent rounded-full" />
          </div>
        ) : (
          <div className="space-y-4">
            {filteredArchetypes.map((archetype, index) => (
              <motion.div
                key={archetype.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <ArchetypeCard
                  archetype={archetype}
                  isExpanded={expandedId === archetype.name}
                  onToggle={() => setExpandedId(expandedId === archetype.name ? null : archetype.name)}
                />
              </motion.div>
            ))}
          </div>
        )}

        {/* CTA at bottom */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="text-center py-12"
        >
          <p className="text-neutral-500 mb-4">Which archetype are you?</p>
          <button
            onClick={onClose}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 text-white font-semibold hover:from-violet-500 hover:to-purple-500 transition-colors"
          >
            Take the Assessment
          </button>
        </motion.div>
      </div>
    </motion.div>
  );
}
