/**
 * Reusable skeleton loader components for loading states
 * All components use animate-pulse with neutral-800 backgrounds to match dark theme
 */

/**
 * Skeleton text lines
 * @param {Object} props
 * @param {number} [props.lines=3] - Number of lines to display
 * @param {string} [props.className=''] - Additional CSS classes
 */
export function SkeletonText({ lines = 3, className = '' }) {
  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-4 bg-neutral-800 rounded animate-pulse"
          style={{
            width: i === lines - 1 ? '75%' : '100%' // Last line shorter
          }}
        />
      ))}
    </div>
  );
}

/**
 * Skeleton card placeholder
 * @param {Object} props
 * @param {string} [props.className=''] - Additional CSS classes
 */
export function SkeletonCard({ className = '' }) {
  return (
    <div className={`bg-neutral-900/60 border border-neutral-800 rounded-2xl p-5 ${className}`}>
      <div className="flex items-start gap-4">
        {/* Icon placeholder */}
        <div className="w-12 h-12 bg-neutral-800 rounded-xl animate-pulse flex-shrink-0" />

        <div className="flex-1 space-y-3">
          {/* Title */}
          <div className="h-5 w-1/3 bg-neutral-800 rounded animate-pulse" />
          {/* Subtitle */}
          <div className="h-4 w-1/2 bg-neutral-800 rounded animate-pulse" />
          {/* Description lines */}
          <div className="space-y-2 mt-4">
            <div className="h-3 bg-neutral-800 rounded animate-pulse" />
            <div className="h-3 w-4/5 bg-neutral-800 rounded animate-pulse" />
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Skeleton avatar/profile picture
 * @param {Object} props
 * @param {'sm'|'md'|'lg'} [props.size='md'] - Avatar size
 */
export function SkeletonAvatar({ size = 'md' }) {
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-20 h-20'
  };

  return (
    <div
      className={`${sizeClasses[size]} bg-neutral-800 rounded-full animate-pulse`}
    />
  );
}

/**
 * Skeleton button placeholder
 * @param {Object} props
 * @param {'sm'|'md'|'lg'} [props.size='md'] - Button size
 * @param {string} [props.className=''] - Additional CSS classes
 */
export function SkeletonButton({ size = 'md', className = '' }) {
  const sizeClasses = {
    sm: 'h-8 w-20',
    md: 'h-10 w-28',
    lg: 'h-12 w-36'
  };

  return (
    <div
      className={`${sizeClasses[size]} bg-neutral-800 rounded-xl animate-pulse ${className}`}
    />
  );
}

/**
 * Full-page loading skeleton for profile/results pages
 */
export function SkeletonProfile() {
  return (
    <div className="min-h-screen bg-[#09090b] p-6">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="h-8 w-24 bg-neutral-800 rounded animate-pulse" />
          <SkeletonAvatar size="md" />
        </div>

        {/* Profile header */}
        <div className="text-center mb-8">
          <SkeletonAvatar size="lg" />
          <div className="mt-4 space-y-2">
            <div className="h-6 w-40 bg-neutral-800 rounded animate-pulse mx-auto" />
            <div className="h-4 w-32 bg-neutral-800 rounded animate-pulse mx-auto" />
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3 mb-8">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="bg-neutral-900/60 border border-neutral-800 rounded-xl p-4"
            >
              <div className="h-8 w-12 bg-neutral-800 rounded animate-pulse mx-auto mb-2" />
              <div className="h-3 w-16 bg-neutral-800 rounded animate-pulse mx-auto" />
            </div>
          ))}
        </div>

        {/* Cards */}
        <div className="space-y-4">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    </div>
  );
}

/**
 * Inline loading spinner
 * @param {Object} props
 * @param {'sm'|'md'|'lg'} [props.size='md'] - Spinner size
 * @param {string} [props.className=''] - Additional CSS classes
 */
export function LoadingSpinner({ size = 'md', className = '' }) {
  const sizeClasses = {
    sm: 'h-4 w-4 border-2',
    md: 'h-8 w-8 border-3',
    lg: 'h-12 w-12 border-4'
  };

  return (
    <div
      className={`${sizeClasses[size]} border-violet-500 border-t-transparent rounded-full animate-spin ${className}`}
    />
  );
}
