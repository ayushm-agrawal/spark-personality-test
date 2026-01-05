/**
 * Shared Components Barrel Export
 *
 * Import shared components from a single location:
 * import { StabilityBadge, ErrorBoundary, SkeletonCard } from './components/shared';
 */

// Display components
export { default as StabilityBadge } from './StabilityBadge';

// Error handling
export { default as ErrorBoundary } from './ErrorBoundary';

// Loading states
export {
  SkeletonText,
  SkeletonCard,
  SkeletonAvatar,
  SkeletonButton,
  SkeletonProfile,
  LoadingSpinner
} from './LoadingSkeleton';

// Feedback components
export { default as OfflineBanner } from './OfflineBanner';
