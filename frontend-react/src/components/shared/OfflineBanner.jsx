import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useOnlineStatus } from '../../hooks/useOnlineStatus';

/**
 * A dismissible banner that appears when the user goes offline
 * Automatically hides when back online
 */
export default function OfflineBanner() {
  const isOnline = useOnlineStatus();
  const [dismissed, setDismissed] = useState(false);
  const [wasOffline, setWasOffline] = useState(false);

  // Reset dismissed state when going offline again
  useEffect(() => {
    if (!isOnline) {
      setDismissed(false);
      setWasOffline(true);
    }
  }, [isOnline]);

  // Show "back online" message briefly when reconnecting
  useEffect(() => {
    if (isOnline && wasOffline) {
      const timer = setTimeout(() => {
        setWasOffline(false);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [isOnline, wasOffline]);

  // Don't show if dismissed or fully online (never was offline)
  if (dismissed || (isOnline && !wasOffline)) {
    return null;
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -50 }}
        className="fixed top-0 left-0 right-0 z-[200] px-4 pt-2"
      >
        <div
          className={`max-w-lg mx-auto rounded-xl px-4 py-3 shadow-lg flex items-center justify-between gap-3 ${
            isOnline
              ? 'bg-green-500/90 text-white'
              : 'bg-amber-500/90 text-amber-950'
          }`}
        >
          <div className="flex items-center gap-3">
            {isOnline ? (
              <>
                <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-sm font-medium">Back online!</span>
              </>
            ) : (
              <>
                <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636a9 9 0 010 12.728m-3.536-3.536a4 4 0 010-5.656M6.343 6.343a8 8 0 000 11.314" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6" />
                </svg>
                <div>
                  <p className="text-sm font-medium">You're offline</p>
                  <p className="text-xs opacity-80">Some features may be unavailable</p>
                </div>
              </>
            )}
          </div>

          <button
            onClick={() => setDismissed(true)}
            className="p-1 hover:bg-black/10 rounded-lg transition-colors"
            aria-label="Dismiss"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
