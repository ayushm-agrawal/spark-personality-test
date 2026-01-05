import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import GoogleSignInButton from './GoogleSignInButton';
import { Analytics } from '../services/analytics';

// Trait configuration
const traitConfig = [
  { name: 'O', full: 'Openness', color: '#fdba74' },
  { name: 'C', full: 'Conscientiousness', color: '#c4b5fd' },
  { name: 'E', full: 'Extraversion', color: '#67e8f9' },
  { name: 'A', full: 'Agreeableness', color: '#86efac' },
  { name: 'S', full: 'Stability', color: '#f9a8d4' },
];

// Custom Archetype Symbol Component - unique symbol per archetype
const ArchetypeSymbol = ({ archetype, size = 120, color = "#c4b5fd" }) => {
  // Unique symbols for each archetype
  const symbols = {
    'The Architect': (
      <>
        {/* Blueprint/building structure */}
        <motion.rect
          x="35" y="50" width="20" height="35"
          stroke={color} strokeWidth="2" fill={`${color}15`}
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ pathLength: 1, opacity: 1 }}
          transition={{ duration: 0.8 }}
        />
        <motion.rect
          x="55" y="35" width="30" height="50"
          stroke={color} strokeWidth="2" fill={`${color}20`}
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ pathLength: 1, opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        />
        <motion.path
          d="M35 50 L60 28 L85 50"
          stroke={color} strokeWidth="2.5" fill="none"
          strokeLinecap="round" strokeLinejoin="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.6, delay: 0.5 }}
        />
      </>
    ),
    'The Catalyst': (
      <>
        {/* Spark/explosion star */}
        <motion.path
          d="M60 15 L63 45 L90 40 L68 55 L85 80 L60 65 L35 80 L52 55 L30 40 L57 45 Z"
          stroke={color} strokeWidth="2" fill={`${color}25`}
          initial={{ scale: 0, rotate: -30 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ duration: 0.8, type: "spring" }}
        />
        <motion.circle
          cx="60" cy="52" r="8"
          fill={color}
          initial={{ scale: 0 }}
          animate={{ scale: [0, 1.3, 1] }}
          transition={{ delay: 0.5, duration: 0.4 }}
        />
      </>
    ),
    'The Strategist': (
      <>
        {/* Chess knight / strategic mind */}
        <motion.path
          d="M45 85 L45 60 Q45 45 55 40 L55 35 Q65 35 65 45 L70 45 Q80 50 75 65 L75 85 Z"
          stroke={color} strokeWidth="2" fill={`${color}20`}
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1 }}
        />
        <motion.circle cx="58" cy="48" r="3" fill={color} initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.8 }} />
        {/* Grid lines suggesting planning */}
        <motion.path d="M30 70 L90 70 M30 55 L90 55" stroke={color} strokeWidth="1" opacity="0.3" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 0.5 }} />
      </>
    ),
    'The Guide': (
      <>
        {/* Compass / guiding star */}
        <motion.circle cx="60" cy="60" r="30" stroke={color} strokeWidth="2" fill="none" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.8 }} />
        <motion.path d="M60 25 L65 55 L60 60 L55 55 Z" fill={color} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }} />
        <motion.path d="M60 95 L55 65 L60 60 L65 65 Z" fill={`${color}60`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }} />
        <motion.path d="M25 60 L55 55 L60 60 L55 65 Z" fill={`${color}60`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }} />
        <motion.path d="M95 60 L65 65 L60 60 L65 55 Z" fill={`${color}60`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.7 }} />
        <motion.circle cx="60" cy="60" r="5" fill={color} initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.8 }} />
      </>
    ),
    'The Alchemist': (
      <>
        {/* Flask / transformation symbol */}
        <motion.path
          d="M50 30 L50 50 L35 80 Q30 90 45 90 L75 90 Q90 90 85 80 L70 50 L70 30"
          stroke={color} strokeWidth="2" fill={`${color}15`}
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1 }}
        />
        <motion.path d="M48 30 L72 30" stroke={color} strokeWidth="3" strokeLinecap="round" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 0.3 }} />
        {/* Bubbles */}
        <motion.circle cx="50" cy="70" r="4" fill={color} opacity="0.6" initial={{ y: 10, opacity: 0 }} animate={{ y: 0, opacity: 0.6 }} transition={{ delay: 0.8, duration: 0.5 }} />
        <motion.circle cx="65" cy="75" r="3" fill={color} opacity="0.4" initial={{ y: 10, opacity: 0 }} animate={{ y: 0, opacity: 0.4 }} transition={{ delay: 1, duration: 0.5 }} />
        <motion.circle cx="55" cy="65" r="2" fill={color} opacity="0.5" initial={{ y: 10, opacity: 0 }} animate={{ y: 0, opacity: 0.5 }} transition={{ delay: 1.1, duration: 0.5 }} />
      </>
    ),
    'The Gardener': (
      <>
        {/* Growing plant / nurturing */}
        <motion.path
          d="M60 90 L60 50"
          stroke={color} strokeWidth="3" strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.6 }}
        />
        {/* Leaves */}
        <motion.path d="M60 70 Q45 60 50 45 Q60 55 60 70" fill={color} opacity="0.7" initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.4, type: "spring" }} />
        <motion.path d="M60 60 Q75 50 70 35 Q60 45 60 60" fill={color} opacity="0.5" initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.6, type: "spring" }} />
        <motion.path d="M60 50 Q40 45 45 30 Q55 40 60 50" fill={color} opacity="0.6" initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.8, type: "spring" }} />
        {/* Ground */}
        <motion.ellipse cx="60" cy="92" rx="20" ry="5" fill={`${color}30`} initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.2 }} />
      </>
    ),
    'The Luminary': (
      <>
        {/* Beacon with emanating rays - illumination */}
        <motion.circle
          cx="60" cy="60" r="15"
          fill={color}
          initial={{ scale: 0 }}
          animate={{ scale: [0, 1.2, 1] }}
          transition={{ duration: 0.6 }}
        />
        <motion.circle
          cx="60" cy="60" r="22"
          stroke={color} strokeWidth="2" fill="none" opacity="0.5"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.3 }}
        />
        {/* Rays emanating outward */}
        {[0, 45, 90, 135, 180, 225, 270, 315].map((angle, i) => {
          const rad = (angle * Math.PI) / 180;
          const x1 = 60 + 28 * Math.cos(rad);
          const y1 = 60 + 28 * Math.sin(rad);
          const x2 = 60 + 45 * Math.cos(rad);
          const y2 = 60 + 45 * Math.sin(rad);
          return (
            <motion.line
              key={angle}
              x1={x1} y1={y1} x2={x2} y2={y2}
              stroke={color}
              strokeWidth={i % 2 === 0 ? "3" : "2"}
              strokeLinecap="round"
              opacity={i % 2 === 0 ? 0.9 : 0.5}
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: i % 2 === 0 ? 0.9 : 0.5 }}
              transition={{ delay: 0.5 + i * 0.05, duration: 0.3 }}
            />
          );
        })}
      </>
    ),
    'The Sentinel': (
      <>
        {/* Shield / guardian */}
        <motion.path
          d="M60 25 L85 35 L85 60 Q85 85 60 95 Q35 85 35 60 L35 35 Z"
          stroke={color} strokeWidth="2.5" fill={`${color}20`}
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1 }}
        />
        {/* Inner emblem */}
        <motion.path
          d="M60 45 L70 55 L70 70 L60 80 L50 70 L50 55 Z"
          stroke={color} strokeWidth="2" fill={`${color}40`}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.6, type: "spring" }}
        />
        <motion.circle cx="60" cy="60" r="5" fill={color} initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.9 }} />
      </>
    ),
    'default': (
      <>
        {/* Fallback: abstract personality symbol */}
        <motion.circle
          cx="60" cy="60" r="30"
          stroke={color} strokeWidth="2" fill={`${color}15`}
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1 }}
        />
        <motion.circle
          cx="60" cy="60" r="18"
          stroke={color} strokeWidth="1.5" fill="none" opacity="0.6"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.8, delay: 0.3 }}
        />
        <motion.circle
          cx="60" cy="60" r="8"
          fill={color}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.8, type: "spring" }}
        />
      </>
    )
  };

  return (
    <svg width={size} height={size} viewBox="0 0 120 120" fill="none">
      {symbols[archetype] || symbols['default']}
    </svg>
  );
};

function StarRating({ rating, onRate }) {
  return (
    <div className="flex justify-center gap-2">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          onClick={() => onRate(star)}
          className={`text-3xl transition-transform hover:scale-110 ${star <= rating ? 'text-yellow-400' : 'text-neutral-600'}`}
        >
          ★
        </button>
      ))}
    </div>
  );
}

// Archetype rarity percentages (for social proof)
const archetypeRarity = {
  'The Architect': 8,
  'The Catalyst': 11,
  'The Strategist': 9,
  'The Guide': 14,
  'The Alchemist': 7,
  'The Gardener': 16,
  'The Luminary': 12,
  'The Sentinel': 15,
};

// Archetype teaser lines (curiosity gap - intriguing but incomplete)
const archetypeTeasers = {
  'The Architect': "Builds systems others can't imagine...",
  'The Catalyst': "Sparks change wherever they go...",
  'The Strategist': "Sees ten moves ahead...",
  'The Guide': "Lights the path for others...",
  'The Alchemist': "Transforms chaos into gold...",
  'The Gardener': "Nurtures what others overlook...",
  'The Luminary': "Illuminates hidden possibilities...",
  'The Sentinel': "Guards what truly matters...",
};

// Static Archetype Symbol for Instagram Story (no animations for html2canvas)
const ArchetypeSymbolStatic = ({ archetype, size = 90, color = "#c4b5fd" }) => {
  const symbols = {
    'The Architect': (
      <>
        <rect x="35" y="50" width="20" height="35" stroke={color} strokeWidth="2" fill={`${color}15`} />
        <rect x="55" y="35" width="30" height="50" stroke={color} strokeWidth="2" fill={`${color}20`} />
        <path d="M35 50 L60 28 L85 50" stroke={color} strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      </>
    ),
    'The Catalyst': (
      <>
        <path d="M60 15 L63 45 L90 40 L68 55 L85 80 L60 65 L35 80 L52 55 L30 40 L57 45 Z" stroke={color} strokeWidth="2" fill={`${color}25`} />
        <circle cx="60" cy="52" r="8" fill={color} />
      </>
    ),
    'The Strategist': (
      <>
        <path d="M45 85 L45 60 Q45 45 55 40 L55 35 Q65 35 65 45 L70 45 Q80 50 75 65 L75 85 Z" stroke={color} strokeWidth="2" fill={`${color}20`} />
        <circle cx="58" cy="48" r="3" fill={color} />
        <path d="M30 70 L90 70 M30 55 L90 55" stroke={color} strokeWidth="1" opacity="0.3" />
      </>
    ),
    'The Guide': (
      <>
        <circle cx="60" cy="60" r="30" stroke={color} strokeWidth="2" fill="none" />
        <path d="M60 25 L65 55 L60 60 L55 55 Z" fill={color} />
        <path d="M60 95 L55 65 L60 60 L65 65 Z" fill={`${color}60`} />
        <path d="M25 60 L55 55 L60 60 L55 65 Z" fill={`${color}60`} />
        <path d="M95 60 L65 65 L60 60 L65 55 Z" fill={`${color}60`} />
        <circle cx="60" cy="60" r="5" fill={color} />
      </>
    ),
    'The Alchemist': (
      <>
        <path d="M50 30 L50 50 L35 80 Q30 90 45 90 L75 90 Q90 90 85 80 L70 50 L70 30" stroke={color} strokeWidth="2" fill={`${color}15`} />
        <path d="M48 30 L72 30" stroke={color} strokeWidth="3" strokeLinecap="round" />
        <circle cx="50" cy="70" r="4" fill={color} opacity="0.6" />
        <circle cx="65" cy="75" r="3" fill={color} opacity="0.4" />
        <circle cx="55" cy="65" r="2" fill={color} opacity="0.5" />
      </>
    ),
    'The Gardener': (
      <>
        <path d="M60 90 L60 50" stroke={color} strokeWidth="3" strokeLinecap="round" />
        <path d="M60 70 Q45 60 50 45 Q60 55 60 70" fill={color} opacity="0.7" />
        <path d="M60 60 Q75 50 70 35 Q60 45 60 60" fill={color} opacity="0.5" />
        <path d="M60 50 Q40 45 45 30 Q55 40 60 50" fill={color} opacity="0.6" />
        <ellipse cx="60" cy="92" rx="20" ry="5" fill={`${color}30`} />
      </>
    ),
    'The Luminary': (
      <>
        <circle cx="60" cy="60" r="15" fill={color} />
        <circle cx="60" cy="60" r="22" stroke={color} strokeWidth="2" fill="none" opacity="0.5" />
        {/* Rays */}
        {[0, 45, 90, 135, 180, 225, 270, 315].map((angle, i) => {
          const rad = (angle * Math.PI) / 180;
          const x1 = 60 + 28 * Math.cos(rad);
          const y1 = 60 + 28 * Math.sin(rad);
          const x2 = 60 + 45 * Math.cos(rad);
          const y2 = 60 + 45 * Math.sin(rad);
          return (
            <line key={angle} x1={x1} y1={y1} x2={x2} y2={y2} stroke={color} strokeWidth={i % 2 === 0 ? "3" : "2"} strokeLinecap="round" opacity={i % 2 === 0 ? 0.9 : 0.5} />
          );
        })}
      </>
    ),
    'The Sentinel': (
      <>
        <path d="M60 25 L85 35 L85 60 Q85 85 60 95 Q35 85 35 60 L35 35 Z" stroke={color} strokeWidth="2.5" fill={`${color}20`} />
        <path d="M60 45 L70 55 L70 70 L60 80 L50 70 L50 55 Z" stroke={color} strokeWidth="2" fill={`${color}40`} />
        <circle cx="60" cy="60" r="5" fill={color} />
      </>
    ),
    'default': (
      <>
        <circle cx="60" cy="60" r="30" stroke={color} strokeWidth="2" fill={`${color}15`} />
        <circle cx="60" cy="60" r="18" stroke={color} strokeWidth="1.5" fill="none" opacity="0.6" />
        <circle cx="60" cy="60" r="8" fill={color} />
      </>
    )
  };

  return (
    <svg width={size} height={size} viewBox="0 0 120 120" fill="none">
      {symbols[archetype] || symbols['default']}
    </svg>
  );
};

// Short descriptive labels for radar chart
const traitShortLabels = {
  'O': 'Open',
  'C': 'Focus',
  'E': 'Social',
  'A': 'Warm',
  'S': 'Calm',
};

// Radar chart component for Instagram story
function RadarChart({ traits, size = 160, color }) {
  const centerX = size / 2;
  const centerY = size / 2;
  const radius = size * 0.28; // Smaller to fit labels with padding

  // Calculate points for pentagon
  const getPoint = (index, value) => {
    const angle = (Math.PI * 2 * index) / 5 - Math.PI / 2;
    const r = (value / 100) * radius;
    return {
      x: centerX + r * Math.cos(angle),
      y: centerY + r * Math.sin(angle),
    };
  };

  // Create path for trait values
  const points = traits.map((trait, i) => getPoint(i, trait.value));
  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ') + ' Z';

  // Create grid lines
  const gridLevels = [25, 50, 75, 100];

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {/* Grid lines */}
      {gridLevels.map((level) => {
        const gridPoints = [0, 1, 2, 3, 4].map(i => getPoint(i, level));
        const gridPath = gridPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ') + ' Z';
        return (
          <path
            key={level}
            d={gridPath}
            fill="none"
            stroke="#F1F5F9"
            strokeWidth="0.5"
            opacity="0.1"
          />
        );
      })}

      {/* Axis lines */}
      {[0, 1, 2, 3, 4].map(i => {
        const endPoint = getPoint(i, 100);
        return (
          <line
            key={i}
            x1={centerX}
            y1={centerY}
            x2={endPoint.x}
            y2={endPoint.y}
            stroke="#F1F5F9"
            strokeWidth="0.5"
            opacity="0.1"
          />
        );
      })}

      {/* Filled area */}
      <path
        d={pathD}
        fill={color}
        fillOpacity="0.3"
        stroke={color}
        strokeWidth="2"
      />

      {/* Data points - match archetype color for cohesive branding */}
      {points.map((p, i) => (
        <circle
          key={i}
          cx={p.x}
          cy={p.y}
          r="4"
          fill={color}
          opacity={0.7 + (i * 0.075)}
        />
      ))}

      {/* Labels - descriptive short words */}
      {traits.map((trait, i) => {
        const labelPoint = getPoint(i, 135);
        const label = traitShortLabels[trait.name] || trait.name;
        return (
          <text
            key={i}
            x={labelPoint.x}
            y={labelPoint.y}
            textAnchor="middle"
            dominantBaseline="middle"
            fill={trait.color}
            fontSize="9"
            fontWeight="600"
            style={{ fontFamily: 'system-ui, -apple-system, sans-serif' }}
          >
            {label}
          </text>
        );
      })}
    </svg>
  );
}

// Instagram Story Share Card Component (9:16 aspect ratio optimized)
function InstagramStoryCard({ archetype, archetypeColor, tagline, traits, zoneOfGenius, onClose }) {
  const cardRef = useRef(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [cardReady, setCardReady] = useState(false);

  const rarity = archetypeRarity[archetype] || 10;
  const teaser = archetypeTeasers[archetype] || tagline;

  useEffect(() => {
    // Small delay to ensure component is mounted
    const timer = setTimeout(() => setCardReady(true), 300);
    return () => clearTimeout(timer);
  }, []);

  const handleDownload = async () => {
    if (!cardRef.current) return;
    setIsGenerating(true);

    // Track share attempt
    Analytics.shareClicked('instagram_story');

    try {
      // Dynamic import html2canvas
      const html2canvas = (await import('html2canvas')).default;

      const canvas = await html2canvas(cardRef.current, {
        scale: 3, // Higher quality for Instagram
        backgroundColor: '#0F172A',
        logging: false,
        useCORS: true,
        allowTaint: true,
        removeContainer: false,
        // Handle modern color functions that html2canvas doesn't support
        onclone: (clonedDoc, element) => {
          // Convert any oklab/oklch colors to hex by forcing computed styles
          const allElements = element.querySelectorAll('*');
          allElements.forEach((el) => {
            const computed = window.getComputedStyle(el);
            // Force color to be applied as inline style with hex fallback
            if (computed.color) {
              el.style.color = computed.color;
            }
            if (computed.backgroundColor && computed.backgroundColor !== 'rgba(0, 0, 0, 0)') {
              el.style.backgroundColor = computed.backgroundColor;
            }
          });
        },
      });

      // Convert to blob
      const blob = await new Promise((resolve) => {
        canvas.toBlob((b) => resolve(b), 'image/png', 1.0);
      });

      if (!blob) {
        throw new Error('Failed to create image blob');
      }

      const fileName = `my-archetype-${archetype.replace(/\s+/g, '-').toLowerCase()}.png`;

      // Check if Web Share API is available and can share files (iOS Safari, Android Chrome)
      if (navigator.share && navigator.canShare) {
        const file = new File([blob], fileName, { type: 'image/png' });
        const shareData = { files: [file] };

        // Check if we can share this file type
        if (navigator.canShare(shareData)) {
          try {
            await navigator.share(shareData);
            Analytics.shareCompleted('web_share_api');
            setIsGenerating(false);
            return; // Success - user shared or saved via share sheet
          } catch (shareError) {
            // User cancelled or share failed - fall through to download
            if (shareError.name === 'AbortError') {
              setIsGenerating(false);
              return; // User cancelled, that's fine
            }
            console.log('Share failed, falling back to download:', shareError);
          }
        }
      }

      // Fallback: Traditional download (works on desktop, Android Files)
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.download = fileName;
      link.href = url;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      Analytics.shareCompleted('download');
      setIsGenerating(false);

    } catch (error) {
      console.error('Failed to generate image:', error);
      setIsGenerating(false);
      // Fallback: copy text to clipboard
      const text = `I'm ${archetype}! "${teaser}" - Only ${rarity}% get this result. Discover yours at personality.ception.one`;
      navigator.clipboard.writeText(text);
      alert('Image generation failed. Text copied to clipboard instead.');
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="relative max-w-xs w-full my-8"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute -top-10 right-0 text-white/60 hover:text-white p-2 z-10"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* The actual card - 9:16 aspect ratio - STATIC for html2canvas */}
        <div
          ref={cardRef}
          className="relative w-full overflow-hidden rounded-2xl"
          style={{
            aspectRatio: '9/16',
            background: '#0F172A',
          }}
        >
          {/* Gradient background - static */}
          <div
            className="absolute inset-0"
            style={{
              background: `
                radial-gradient(ellipse at 50% 20%, ${archetypeColor}40 0%, transparent 50%),
                radial-gradient(ellipse at 80% 80%, #38BDF820 0%, transparent 40%),
                radial-gradient(ellipse at 20% 70%, #FF6F6120 0%, transparent 40%)
              `,
            }}
          />

          {/* Content container */}
          <div className="relative z-10 h-full flex flex-col px-5 py-5">
            {/* Top section - moved higher with more space */}
            <div className="text-center mb-3">
              <p style={{ color: 'rgba(241, 245, 249, 0.6)', fontSize: '13px', letterSpacing: '0.08em', fontWeight: '500' }}>
                just discovered i'm...
              </p>
            </div>

            {/* Hero section */}
            <div className="flex-1 flex flex-col items-center justify-center" style={{ marginTop: '-8px' }}>
              {/* Archetype-specific symbol */}
              <div className="relative mb-3">
                <ArchetypeSymbolStatic archetype={archetype} size={90} color={archetypeColor} />
              </div>

              {/* Archetype name */}
              <h1
                style={{
                  fontSize: '28px',
                  fontWeight: '900',
                  textAlign: 'center',
                  letterSpacing: '-0.02em',
                  marginBottom: '8px',
                  color: archetypeColor,
                }}
              >
                {archetype.toUpperCase()}
              </h1>

              {/* Teaser line */}
              <p
                style={{
                  color: 'rgba(241, 245, 249, 0.8)',
                  textAlign: 'center',
                  fontSize: '13px',
                  fontStyle: 'italic',
                  padding: '0 12px',
                  lineHeight: '1.4',
                }}
              >
                "{teaser}"
              </p>

              {/* Zone of Genius */}
              {zoneOfGenius && (
                <div style={{ marginTop: '10px', padding: '0 12px', textAlign: 'center' }}>
                  <p style={{
                    color: 'rgba(241, 245, 249, 0.5)',
                    fontSize: '9px',
                    textTransform: 'uppercase',
                    letterSpacing: '0.12em',
                    marginBottom: '3px',
                  }}>
                    Zone of Genius
                  </p>
                  <p style={{
                    color: '#F1F5F9',
                    fontSize: '11px',
                    lineHeight: '1.4',
                  }}>
                    {zoneOfGenius}
                  </p>
                </div>
              )}

              {/* Top 3 Trait Scores */}
              <div style={{
                display: 'flex',
                justifyContent: 'center',
                gap: '8px',
                marginTop: '12px',
              }}>
                {[...traits]
                  .sort((a, b) => b.value - a.value)
                  .slice(0, 3)
                  .map((trait) => (
                    <div
                      key={trait.name}
                      style={{
                        textAlign: 'center',
                        padding: '6px 10px',
                        borderRadius: '8px',
                        backgroundColor: 'rgba(241, 245, 249, 0.08)',
                      }}
                    >
                      <div style={{ color: trait.color, fontSize: '16px', fontWeight: '700' }}>
                        {Math.round(trait.value)}%
                      </div>
                      <div style={{ color: 'rgba(241, 245, 249, 0.6)', fontSize: '9px' }}>
                        {trait.full}
                      </div>
                    </div>
                  ))}
              </div>

              {/* Radar Chart - smaller */}
              <div className="mt-1">
                <RadarChart traits={traits} size={140} color={archetypeColor} />
              </div>
            </div>

            {/* Social proof section */}
            <div style={{ textAlign: 'center', paddingBottom: '16px' }}>
              {/* Rarity badge */}
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 16px',
                  borderRadius: '999px',
                  backgroundColor: 'rgba(241, 245, 249, 0.1)',
                  border: '1px solid rgba(241, 245, 249, 0.2)',
                  marginBottom: '16px',
                }}
              >
                <span style={{ color: '#FDE047', fontSize: '12px' }}>✦</span>
                <span style={{ color: '#F1F5F9', fontSize: '12px', fontWeight: '500' }}>
                  Only {rarity}% get this result
                </span>
              </div>

              {/* URL CTA - prominent so viewers know where to go */}
              <div
                style={{
                  display: 'block',
                  padding: '10px 16px',
                  borderRadius: '10px',
                  fontWeight: '600',
                  color: 'white',
                  fontSize: '13px',
                  background: `linear-gradient(135deg, ${archetypeColor}, #38BDF8)`,
                  letterSpacing: '0.02em',
                }}
              >
                Find yours at personality.ception.one
              </div>
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="mt-4 flex gap-3">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleDownload}
            disabled={isGenerating || !cardReady}
            className="flex-1 py-3 px-4 rounded-xl font-medium text-white flex items-center justify-center gap-2 disabled:opacity-50"
            style={{
              background: 'linear-gradient(135deg, #E1306C, #F77737)',
            }}
          >
            {isGenerating ? (
              <>
                <svg className="animate-spin w-5 h-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Creating...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                </svg>
                Share Image
              </>
            )}
          </motion.button>
        </div>

        <p className="text-center text-[#F1F5F9]/40 text-xs mt-3">
          On iPhone: Tap "Save Image" from the share menu
        </p>
        <p className="text-center text-[#F1F5F9]/30 text-xs mt-1">
          Share to Instagram Stories with a link sticker!
        </p>
      </motion.div>
    </motion.div>
  );
}

// Confidence Info Tooltip Component
function ConfidenceInfo({ confidence, archetypeColor }) {
  const [showTooltip, setShowTooltip] = useState(false);

  const tier = confidence?.tier || 'emerging';
  const explanation = confidence?.explanation;
  const confidencePct = confidence?.confidence_pct || confidence?.archetype_confidence || 50;

  const getTierLabel = () => {
    if (tier === 'clear') return 'Strong match';
    if (tier === 'emerging') return 'Emerging Profile';
    return 'Exploring';
  };

  const getTierColor = () => {
    if (tier === 'clear') return archetypeColor;
    if (tier === 'emerging') return '#fbbf24'; // amber
    return '#f97316'; // orange
  };

  return (
    <div className="relative inline-flex items-center gap-2 mt-2">
      {/* Tier badge */}
      {tier !== 'clear' && (
        <span
          className="px-2 py-0.5 text-xs font-medium rounded-full"
          style={{ backgroundColor: `${getTierColor()}20`, color: getTierColor() }}
        >
          {getTierLabel()}
        </span>
      )}

      {/* Confidence text */}
      <span className="text-neutral-500">
        {tier === 'clear' ? 'Strong match' : ''} {Math.round(confidencePct)}% confidence
      </span>

      {/* Info icon for non-clear tiers */}
      {tier !== 'clear' && explanation && (
        <button
          onClick={() => setShowTooltip(!showTooltip)}
          className="text-neutral-500 hover:text-neutral-300 transition-colors"
          aria-label="More info about confidence"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </button>
      )}

      {/* Tooltip */}
      <AnimatePresence>
        {showTooltip && explanation && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            className="absolute top-full left-1/2 -translate-x-1/2 mt-2 z-50 w-72 p-3 rounded-xl bg-neutral-800 border border-neutral-700 shadow-xl"
          >
            <p className="text-sm text-neutral-200">{explanation}</p>
            <div className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-neutral-800 border-l border-t border-neutral-700 rotate-45" />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Stability badge component
function StabilityBadge({ stability }) {
  const config = {
    stable: { label: 'Stable', color: '#22c55e', icon: '✓', description: 'Your results are consistent' },
    converging: { label: 'Converging', color: '#eab308', icon: '→', description: 'Your profile is becoming clearer' },
    inconsistent: { label: 'Variable', color: '#f97316', icon: '~', description: 'Results vary between tests' },
    new: { label: 'New', color: '#a78bfa', icon: '★', description: 'Take more tests for better accuracy' },
  };

  const { label, color, icon, description } = config[stability] || config.new;

  return (
    <div
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
      style={{ backgroundColor: `${color}20`, color }}
      title={description}
    >
      <span>{icon}</span>
      <span>{label}</span>
    </div>
  );
}

export default function Results({ results, mode, interest, onFeedback, showSavePrompt = false, onViewGallery, holisticProfile = null }) {
  const [phase, setPhase] = useState('loading');
  const [showDetails, setShowDetails] = useState(false);
  const [rating, setRating] = useState(0);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);

  useEffect(() => {
    if (results) {
      // Phased reveal animation
      const timer1 = setTimeout(() => setPhase('reveal'), 1500);
      const timer2 = setTimeout(() => setPhase('complete'), 3000);
      const timer3 = setTimeout(() => setShowDetails(true), 4000);
      return () => {
        clearTimeout(timer1);
        clearTimeout(timer2);
        clearTimeout(timer3);
      };
    }
  }, [results]);

  if (!results) {
    return (
      <div className="min-h-screen bg-[#09090b] flex items-center justify-center">
        <div className="animate-spin h-12 w-12 border-4 border-violet-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  // Support both new and legacy response formats
  const archetype = results.archetype || {};
  const archetypeName = archetype.name || results.suggested_archetype;
  const archetypeEmoji = archetype.emoji || '✨';
  const archetypeColor = archetype.color || '#a78bfa';
  const archetypeTagline = archetype.tagline || '';
  const confidence = results.archetype_confidence;
  const confidenceData = results.confidence || { tier: 'emerging', confidence_pct: confidence };
  const scores = results.normalized_scores;
  const traitBreakdown = results.trait_breakdown;
  const allMatches = results.all_matches;
  const personalizedProfile = results.personalized_profile || results.archetype_description || {};
  const modeSpecific = results.mode_specific || {};
  const suspiciousWarning = results.suspicious_patterns;

  // Get interest from prop or from results (backend includes it in mode_specific)
  const displayInterest = interest || modeSpecific?.interest;

  // Build traits array from scores
  const traits = scores ? traitConfig.map(t => ({
    ...t,
    value: scores[t.full] || scores[t.full.replace(' ', '_')] || 50
  })) : [];

  const handleRate = async (stars) => {
    setRating(stars);
    if (!feedbackSubmitted) {
      await onFeedback(stars - 1);
      setFeedbackSubmitted(true);
    }
  };

  return (
    <div
      className="min-h-screen text-white overflow-x-hidden relative"
      style={{ background: '#09090b' }}
    >
      {/* Background */}
      <div className="absolute inset-0 overflow-hidden">
        <motion.div
          className="absolute inset-0"
          animate={{
            background: phase === 'complete'
              ? `radial-gradient(ellipse at 50% 30%, ${archetypeColor}30 0%, transparent 60%)`
              : `radial-gradient(ellipse at 50% 50%, ${archetypeColor}15 0%, transparent 50%)`
          }}
          transition={{ duration: 2 }}
        />
      </div>

      <div className="relative z-10 min-h-screen flex flex-col items-center justify-center px-6 py-12">
        <AnimatePresence mode="wait">
          {/* Loading Phase */}
          {phase === 'loading' && (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="text-center"
            >
              <motion.div
                className="w-20 h-20 mx-auto mb-8 rounded-full border-2 border-neutral-700 border-t-violet-400 relative"
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              />

              <p className="text-neutral-300 text-lg mb-4">
                Calculating your archetype...
              </p>

              <div className="flex justify-center gap-2">
                {traitConfig.map((trait, i) => (
                  <motion.span
                    key={trait.name}
                    className="text-xs px-2 py-1 rounded border border-neutral-700 text-neutral-500"
                    style={{ backgroundColor: `${trait.color}10` }}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 + i * 0.15 }}
                  >
                    {trait.name}
                  </motion.span>
                ))}
              </div>
            </motion.div>
          )}

          {/* Reveal Phase */}
          {phase === 'reveal' && (
            <motion.div
              key="reveal"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="text-center"
            >
              <motion.div
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ type: "spring", stiffness: 200, delay: 0.2 }}
                className="mb-6"
              >
                <ArchetypeSymbol archetype={archetypeName} size={140} color={archetypeColor} />
              </motion.div>

              <motion.h1
                className="text-5xl md:text-7xl font-bold"
                style={{ color: archetypeColor }}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
              >
                {archetypeName}
              </motion.h1>
            </motion.div>
          )}

          {/* Complete Phase */}
          {phase === 'complete' && (
            <motion.div
              key="complete"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="w-full max-w-4xl"
            >
              {/* Suspicious patterns warning banner */}
              {suspiciousWarning && (
                <motion.div
                  initial={{ opacity: 0, y: -20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mb-6 p-4 rounded-xl bg-amber-500/10 border border-amber-500/30"
                >
                  <div className="flex items-start gap-3">
                    <span className="text-amber-400 text-xl flex-shrink-0">⚠️</span>
                    <div className="flex-1">
                      <p className="text-amber-200 font-medium mb-1">Quick responses detected</p>
                      <p className="text-amber-200/80 text-sm mb-3">
                        {suspiciousWarning.warning || "Your results may be less accurate. For a clearer picture, you can retake the test."}
                      </p>
                      <div className="flex gap-3">
                        <button
                          onClick={() => window.location.reload()}
                          className="px-4 py-2 text-sm font-medium rounded-lg bg-amber-500/20 text-amber-200 hover:bg-amber-500/30 transition-colors"
                        >
                          Retake Test
                        </button>
                        <button
                          onClick={() => {}}
                          className="px-4 py-2 text-sm font-medium rounded-lg text-amber-200/60 hover:text-amber-200 transition-colors"
                        >
                          Keep these results
                        </button>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Hero */}
              <div className="text-center mb-10">
                <motion.div
                  className="mb-6"
                  animate={{ y: [0, -8, 0] }}
                  transition={{ duration: 4, repeat: Infinity }}
                >
                  <ArchetypeSymbol archetype={archetypeName} size={100} color={archetypeColor} />
                </motion.div>

                {/* Show interest context for deep_dive mode */}
                {mode === 'deep_dive' && displayInterest && (
                  <motion.p
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-lg text-neutral-400 mb-2"
                  >
                    When it comes to <span className="text-neutral-200 font-medium">{displayInterest}</span>, you're
                  </motion.p>
                )}

                <h1
                  className="text-5xl md:text-6xl font-bold mb-3"
                  style={{ color: archetypeColor }}
                >
                  {archetypeName}
                </h1>

                {archetypeTagline && (
                  <p className="text-xl text-neutral-300 italic">
                    "{archetypeTagline}"
                  </p>
                )}

                {/* Confidence tier display with tooltip */}
                <ConfidenceInfo confidence={confidenceData} archetypeColor={archetypeColor} />

                {/* Show explanation prominently for unclear tier */}
                {confidenceData?.tier === 'unclear' && confidenceData?.explanation && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-4 mx-auto max-w-md p-3 rounded-xl bg-orange-500/10 border border-orange-500/30"
                  >
                    <p className="text-sm text-orange-200">{confidenceData.explanation}</p>
                  </motion.div>
                )}

                {/* Test not included in profile warning */}
                {holisticProfile && holisticProfile.included_in_profile === false && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-4 mx-auto max-w-md p-3 rounded-xl bg-neutral-800/60 border border-neutral-700"
                  >
                    <p className="text-sm text-neutral-400">
                      This test wasn't included in your holistic profile due to unusual response patterns.
                    </p>
                  </motion.div>
                )}
              </div>

              {/* Holistic Profile Section - shown when user has multiple tests */}
              {holisticProfile && holisticProfile.holistic && holisticProfile.holistic.tests_included > 1 && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="mb-8 p-5 rounded-2xl bg-gradient-to-br from-neutral-900/80 to-neutral-800/60 border border-neutral-700"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-violet-500/20 flex items-center justify-center">
                        <svg className="w-5 h-5 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-white">Your Holistic Profile</h3>
                        <p className="text-sm text-neutral-400">
                          Based on {holisticProfile.holistic.tests_included} test{holisticProfile.holistic.tests_included > 1 ? 's' : ''}
                          {holisticProfile.holistic.tests_excluded > 0 && (
                            <span className="text-neutral-500"> ({holisticProfile.holistic.tests_excluded} excluded)</span>
                          )}
                        </p>
                      </div>
                    </div>
                    <StabilityBadge stability={holisticProfile.holistic.stability} />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-neutral-800/50">
                      <p className="text-neutral-500 text-sm mb-1">Overall Archetype</p>
                      <p className="text-xl font-bold" style={{ color: archetypeColor }}>
                        {holisticProfile.holistic.archetype || archetypeName}
                      </p>
                    </div>
                    <div className="p-4 rounded-xl bg-neutral-800/50">
                      <p className="text-neutral-500 text-sm mb-1">Overall Confidence</p>
                      <p className="text-xl font-bold text-white">
                        {Math.round(holisticProfile.holistic.confidence || 0)}%
                      </p>
                    </div>
                  </div>

                  {/* Show if this test result differs from holistic */}
                  {holisticProfile.holistic.archetype && holisticProfile.holistic.archetype !== archetypeName && (
                    <div className="mt-4 pt-4 border-t border-neutral-700">
                      <p className="text-sm text-neutral-400">
                        <span className="text-amber-400">Note:</span> This test gave you {archetypeName}, but your overall profile across multiple tests is {holisticProfile.holistic.archetype}.
                      </p>
                    </div>
                  )}
                </motion.div>
              )}

              {/* This Test section header - only when holistic profile exists */}
              {holisticProfile && holisticProfile.holistic && holisticProfile.holistic.tests_included > 1 && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex items-center gap-3 mb-4"
                >
                  <div className="h-px flex-1 bg-neutral-800" />
                  <span className="text-sm text-neutral-500 font-medium">This Test</span>
                  <div className="h-px flex-1 bg-neutral-800" />
                </motion.div>
              )}

              {/* Trait circles - grid on mobile, flex row on desktop */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="w-full mb-10"
              >
                {/* Mobile: 3+2 grid layout */}
                <div className="grid grid-cols-3 gap-4 md:hidden">
                  {traits.slice(0, 3).map((trait, i) => (
                    <motion.div
                      key={trait.name}
                      initial={{ opacity: 0, scale: 0 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.4 + i * 0.1 }}
                      className="flex flex-col items-center"
                    >
                      <div className="relative w-14 h-14 mb-2">
                        <svg className="w-14 h-14 -rotate-90" viewBox="0 0 56 56">
                          <circle cx="28" cy="28" r="24" fill="none" stroke="#262626" strokeWidth="4" />
                          <motion.circle
                            cx="28" cy="28" r="24" fill="none" stroke={trait.color} strokeWidth="4"
                            strokeLinecap="round" strokeDasharray={2 * Math.PI * 24}
                            initial={{ strokeDashoffset: 2 * Math.PI * 24 }}
                            animate={{ strokeDashoffset: 2 * Math.PI * 24 * (1 - trait.value / 100) }}
                            transition={{ delay: 0.6 + i * 0.1, duration: 1, ease: "easeOut" }}
                          />
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className="text-sm font-bold text-white">{Math.round(trait.value)}</span>
                        </div>
                      </div>
                      <span className="text-[10px] text-neutral-400 text-center">{trait.full}</span>
                    </motion.div>
                  ))}
                </div>
                <div className="grid grid-cols-2 gap-4 mt-4 max-w-[200px] mx-auto md:hidden">
                  {traits.slice(3).map((trait, i) => (
                    <motion.div
                      key={trait.name}
                      initial={{ opacity: 0, scale: 0 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.7 + i * 0.1 }}
                      className="flex flex-col items-center"
                    >
                      <div className="relative w-14 h-14 mb-2">
                        <svg className="w-14 h-14 -rotate-90" viewBox="0 0 56 56">
                          <circle cx="28" cy="28" r="24" fill="none" stroke="#262626" strokeWidth="4" />
                          <motion.circle
                            cx="28" cy="28" r="24" fill="none" stroke={trait.color} strokeWidth="4"
                            strokeLinecap="round" strokeDasharray={2 * Math.PI * 24}
                            initial={{ strokeDashoffset: 2 * Math.PI * 24 }}
                            animate={{ strokeDashoffset: 2 * Math.PI * 24 * (1 - trait.value / 100) }}
                            transition={{ delay: 0.9 + i * 0.1, duration: 1, ease: "easeOut" }}
                          />
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className="text-sm font-bold text-white">{Math.round(trait.value)}</span>
                        </div>
                      </div>
                      <span className="text-[10px] text-neutral-400 text-center">{trait.full}</span>
                    </motion.div>
                  ))}
                </div>

                {/* Desktop: single row */}
                <div className="hidden md:flex justify-center gap-6">
                  {traits.map((trait, i) => (
                    <motion.div
                      key={trait.name}
                      initial={{ opacity: 0, scale: 0 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.4 + i * 0.1 }}
                      className="flex flex-col items-center"
                    >
                      <div className="relative w-14 h-14 mb-2">
                        <svg className="w-14 h-14 -rotate-90" viewBox="0 0 56 56">
                          <circle cx="28" cy="28" r="24" fill="none" stroke="#262626" strokeWidth="4" />
                          <motion.circle
                            cx="28" cy="28" r="24" fill="none" stroke={trait.color} strokeWidth="4"
                            strokeLinecap="round" strokeDasharray={2 * Math.PI * 24}
                            initial={{ strokeDashoffset: 2 * Math.PI * 24 }}
                            animate={{ strokeDashoffset: 2 * Math.PI * 24 * (1 - trait.value / 100) }}
                            transition={{ delay: 0.6 + i * 0.1, duration: 1, ease: "easeOut" }}
                          />
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className="text-sm font-bold text-white">{Math.round(trait.value)}</span>
                        </div>
                      </div>
                      <span className="text-xs text-neutral-400">{trait.full}</span>
                    </motion.div>
                  ))}
                </div>
              </motion.div>

              {/* Details */}
              <AnimatePresence>
                {showDetails && (
                  <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="space-y-5"
                  >
                    {/* Description */}
                    {(personalizedProfile.overview || archetype.description) && (
                      <div className="bg-neutral-900/80 border border-neutral-800 rounded-2xl p-6">
                        <p className="text-lg text-neutral-200 leading-relaxed">
                          {personalizedProfile.overview || archetype.description}
                        </p>
                      </div>
                    )}

                    {/* Insight cards */}
                    <div className="grid md:grid-cols-3 gap-4">
                      {archetype.zone_of_genius && (
                        <motion.div
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.1 }}
                          className="bg-neutral-900/60 border rounded-xl p-5"
                          style={{ borderColor: `${archetypeColor}40` }}
                        >
                          <div className="text-sm mb-2 font-medium" style={{ color: archetypeColor }}>Zone of Genius</div>
                          <p className="text-neutral-100">{archetype.zone_of_genius}</p>
                        </motion.div>
                      )}

                      {archetype.deepest_aspiration && (
                        <motion.div
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: 0.2 }}
                          className="bg-neutral-900/60 border border-orange-500/30 rounded-xl p-5"
                        >
                          <div className="text-orange-300 text-sm mb-2 font-medium">Deepest Aspiration</div>
                          <p className="text-neutral-100">{archetype.deepest_aspiration}</p>
                        </motion.div>
                      )}

                      {archetype.growth_opportunity && (
                        <motion.div
                          initial={{ opacity: 0, x: 20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.3 }}
                          className="bg-neutral-900/60 border border-cyan-500/30 rounded-xl p-5"
                        >
                          <div className="text-cyan-300 text-sm mb-2 font-medium">Growth Edge</div>
                          <p className="text-neutral-100">{archetype.growth_opportunity}</p>
                        </motion.div>
                      )}
                    </div>

                    {/* Hackathon insights */}
                    {mode === 'hackathon' && (modeSpecific.hackathon_superpower || archetype.team_value) && (
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 }}
                        className="bg-neutral-900/60 border border-neutral-700 rounded-2xl p-6"
                      >
                        <div className="flex items-center gap-2 mb-5">
                          <div className="w-8 h-8 rounded-lg bg-orange-500/20 flex items-center justify-center">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                              <path d="M8 2 L9 7 L14 7 L10 10 L11 15 L8 12 L5 15 L6 10 L2 7 L7 7 Z"
                                stroke="#fdba74" strokeWidth="1.5" fill="none" />
                            </svg>
                          </div>
                          <h3 className="text-lg font-semibold text-neutral-100">In a Hackathon...</h3>
                        </div>

                        <div className="grid md:grid-cols-2 gap-5">
                          <div>
                            <p className="text-neutral-500 text-sm mb-1">Team Role</p>
                            <p className="text-xl font-medium text-white">{archetype.team_value || modeSpecific.team_value}</p>
                          </div>
                          {modeSpecific.hackathon_superpower && (
                            <div>
                              <p className="text-neutral-500 text-sm mb-1">Your Superpower</p>
                              <p className="text-xl font-medium text-white">{modeSpecific.hackathon_superpower}</p>
                            </div>
                          )}
                          {modeSpecific.hackathon_pitfall && (
                            <div>
                              <p className="text-neutral-500 text-sm mb-1">Watch Out For</p>
                              <p className="text-neutral-200">{modeSpecific.hackathon_pitfall}</p>
                            </div>
                          )}
                          {archetype.ideal_partners?.length > 0 && (
                            <div>
                              <p className="text-neutral-500 text-sm mb-1">Dream Team</p>
                              <div className="flex gap-2 flex-wrap">
                                {archetype.ideal_partners.map((mate) => (
                                  <span
                                    key={mate}
                                    className="px-3 py-1 bg-neutral-800 border border-neutral-700 rounded-full text-sm text-neutral-200"
                                  >
                                    {mate}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </motion.div>
                    )}

                    {/* Creative partner */}
                    {archetype.creative_partner && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.5 }}
                        className="text-center py-6"
                      >
                        <p className="text-neutral-500 mb-2">Your creative partner archetype</p>
                        <p className="text-2xl font-bold text-emerald-300">
                          {archetype.creative_partner}
                        </p>
                        <p className="text-neutral-500 text-sm mt-2">Find them. Build together.</p>
                      </motion.div>
                    )}

                    {/* All archetype matches */}
                    {allMatches && (
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.6 }}
                        className="bg-neutral-900/60 border border-neutral-800 rounded-2xl p-6"
                      >
                        <h3 className="text-lg font-semibold text-white mb-4">All Archetype Matches</h3>
                        <div className="space-y-3">
                          {Object.entries(allMatches).map(([arch, score], index) => (
                            <div key={arch} className="flex items-center gap-3">
                              <span className="w-28 text-neutral-300 text-sm truncate">{arch}</span>
                              <div className="flex-1 h-2 bg-neutral-700 rounded-full overflow-hidden">
                                <motion.div
                                  className="h-full rounded-full"
                                  style={{ backgroundColor: index === 0 ? archetypeColor : '#6B7280' }}
                                  initial={{ width: 0 }}
                                  animate={{ width: `${score}%` }}
                                  transition={{ delay: 0.7 + index * 0.1, duration: 0.5 }}
                                />
                              </div>
                              <span className="text-neutral-400 w-12 text-right text-sm">{Math.round(score)}%</span>
                            </div>
                          ))}
                        </div>
                      </motion.div>
                    )}

                    {/* View All Archetypes Button */}
                    {onViewGallery && (
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.7 }}
                        className="text-center"
                      >
                        <button
                          onClick={onViewGallery}
                          className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-neutral-900/60 border border-neutral-700 text-neutral-300 hover:bg-neutral-800 hover:text-white hover:border-violet-500/50 transition-all"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                          </svg>
                          Explore All 8 Archetypes
                        </button>
                      </motion.div>
                    )}

                    {/* Feedback */}
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.8 }}
                      className="text-center py-8"
                    >
                      <p className="text-neutral-400 mb-4">How was your experience?</p>
                      <StarRating rating={rating} onRate={handleRate} />
                      {feedbackSubmitted && (
                        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-green-400 mt-3">
                          Thanks for your feedback!
                        </motion.p>
                      )}
                    </motion.div>

                    {/* Save Prompt for unauthenticated users */}
                    {showSavePrompt && (
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 1 }}
                        className="py-6 border-t border-neutral-800 flex flex-col items-center"
                      >
                        <p className="text-neutral-400 mb-4 text-sm text-center">
                          Want to save your results and view them later?
                        </p>
                        <GoogleSignInButton variant="full" />
                        <p className="text-neutral-600 text-xs mt-3 text-center">
                          Sign in to save and track your personality over time
                        </p>
                      </motion.div>
                    )}

                    {/* Share CTA - prominent on mobile */}
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.9 }}
                      className="mt-6 p-6 rounded-2xl bg-gradient-to-br from-neutral-900 to-neutral-800 border border-neutral-700"
                    >
                      <p className="text-center text-neutral-300 text-sm mb-4">
                        Share your archetype with friends
                      </p>
                      <motion.button
                        whileHover={{ scale: 1.03 }}
                        whileTap={{ scale: 0.97 }}
                        onClick={() => setShowShareModal(true)}
                        className="w-full px-8 py-4 rounded-xl font-semibold text-white shadow-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-[#09090b] flex items-center justify-center gap-3"
                        style={{
                          background: 'linear-gradient(135deg, #E1306C, #F77737, #FCAF45)',
                        }}
                      >
                        <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                        </svg>
                        Share on Instagram
                      </motion.button>
                      <p className="text-center text-neutral-500 text-xs mt-3">
                        Create a story card to share your results
                      </p>
                    </motion.div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Instagram Share Modal */}
      <AnimatePresence>
        {showShareModal && (
          <InstagramStoryCard
            archetype={archetypeName}
            archetypeColor={archetypeColor}
            tagline={archetypeTagline}
            traits={traits}
            zoneOfGenius={archetype?.zone_of_genius}
            onClose={() => setShowShareModal(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
