import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * Stability badge component with optional tooltip
 * @param {Object} props
 * @param {'stable'|'converging'|'inconsistent'|'new'} props.stability - The stability status
 * @param {'sm'|'md'} [props.size='md'] - Badge size
 * @param {boolean} [props.showTooltip=false] - Whether to show interactive tooltip
 */
export default function StabilityBadge({ stability, size = 'md', showTooltip = false }) {
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

  const sizeClasses = {
    sm: 'text-[10px] px-1.5 py-0.5 gap-1',
    md: 'text-sm px-3 py-1 gap-1.5',
  };

  const sizeClass = sizeClasses[size] || sizeClasses.md;

  return (
    <div className="relative inline-block">
      <div
        className={`inline-flex items-center rounded-full font-medium cursor-help ${sizeClass}`}
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
