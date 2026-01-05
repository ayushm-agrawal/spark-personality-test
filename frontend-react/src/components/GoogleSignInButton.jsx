import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

// Google "G" logo SVG
const GoogleLogo = ({ className = "w-4 h-4" }) => (
  <svg className={className} viewBox="0 0 24 24">
    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
  </svg>
);

export default function GoogleSignInButton({ variant = 'icon', onViewProfile = null, showProfileBadge = false }) {
  const { signInWithGoogle, isAuthenticated, user, logout, loading } = useAuth();
  const { isDark } = useTheme();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isSigningIn, setIsSigningIn] = useState(false);

  const handleSignIn = async () => {
    setIsSigningIn(true);
    try {
      await signInWithGoogle();
    } catch (error) {
      console.error('Sign in failed:', error);
    } finally {
      setIsSigningIn(false);
    }
  };

  const handleLogout = async () => {
    setIsMenuOpen(false);
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  // Show loading state
  if (loading) {
    return (
      <div className={`w-8 h-8 rounded-full animate-pulse ${isDark ? 'bg-neutral-800' : 'bg-gray-200'}`} />
    );
  }

  // Authenticated state - show user avatar with dropdown
  if (isAuthenticated && user) {
    const handleProfileClick = () => {
      setIsMenuOpen(false);
      if (onViewProfile) onViewProfile();
    };

    return (
      <div className="relative">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-full border transition-colors focus:outline-none focus:border-violet-400 ${
            isDark
              ? 'bg-neutral-800/80 border-neutral-700 hover:border-violet-400'
              : 'bg-white border-gray-200 hover:border-violet-400 shadow-sm'
          }`}
        >
          <div className="relative">
            <div className="w-7 h-7 rounded-full overflow-hidden">
              {user.photoURL ? (
                <img
                  src={user.photoURL}
                  alt={user.displayName || 'User'}
                  className="w-full h-full object-cover"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <div className="w-full h-full bg-violet-600 flex items-center justify-center text-white text-xs font-semibold">
                  {(user.displayName || user.email || 'U')[0].toUpperCase()}
                </div>
              )}
            </div>
            {/* Animated badge for new profile feature */}
            {showProfileBadge && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute -top-1 -right-1"
              >
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-violet-500"></span>
                </span>
              </motion.div>
            )}
          </div>
          <span className={`text-sm hidden sm:block max-w-[100px] truncate ${isDark ? 'text-neutral-300' : 'text-gray-700'}`}>
            {user.displayName?.split(' ')[0] || 'Profile'}
          </span>
          <svg className={`w-4 h-4 ${isDark ? 'text-neutral-500' : 'text-gray-400'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </motion.button>

        {/* Tooltip for badge */}
        {showProfileBadge && !isMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1 }}
            className="absolute right-0 top-12 z-40 px-3 py-2 bg-violet-600 text-white text-xs rounded-lg shadow-lg whitespace-nowrap"
          >
            <div className="absolute -top-1.5 right-4 w-3 h-3 bg-violet-600 rotate-45"></div>
            View your personality profile!
          </motion.div>
        )}

        <AnimatePresence>
          {isMenuOpen && (
            <>
              {/* Backdrop to close menu */}
              <div
                className="fixed inset-0 z-40"
                onClick={() => setIsMenuOpen(false)}
              />

              <motion.div
                initial={{ opacity: 0, y: -10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.95 }}
                transition={{ duration: 0.15 }}
                className={`absolute right-0 top-12 z-50 rounded-xl shadow-xl border py-2 min-w-[180px] ${
                  isDark
                    ? 'bg-neutral-800 border-neutral-700'
                    : 'bg-white border-gray-200'
                }`}
              >
                <div className={`px-4 py-2 border-b ${isDark ? 'border-neutral-700' : 'border-gray-100'}`}>
                  <p className={`text-sm font-medium truncate ${isDark ? 'text-white' : 'text-gray-900'}`}>
                    {user.displayName || 'User'}
                  </p>
                  <p className={`text-xs truncate ${isDark ? 'text-neutral-400' : 'text-gray-500'}`}>
                    {user.email}
                  </p>
                </div>

                {/* My Profile button */}
                {onViewProfile && (
                  <button
                    onClick={handleProfileClick}
                    className={`w-full px-4 py-2.5 text-left text-sm transition-colors flex items-center gap-3 ${
                      isDark
                        ? 'text-white hover:bg-neutral-700'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <svg className="w-4 h-4 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    My Profile
                  </button>
                )}

                <button
                  onClick={handleLogout}
                  className={`w-full px-4 py-2.5 text-left text-sm transition-colors flex items-center gap-3 ${
                    isDark
                      ? 'text-neutral-400 hover:bg-neutral-700 hover:text-white'
                      : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'
                  }`}
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  Sign Out
                </button>
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </div>
    );
  }

  // Not authenticated - show sign in button
  if (variant === 'icon') {
    return (
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={handleSignIn}
        disabled={isSigningIn}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-full border transition-colors disabled:opacity-50 ${
          isDark
            ? 'bg-neutral-800/80 border-neutral-700 hover:border-violet-400'
            : 'bg-white border-gray-200 hover:border-violet-400 shadow-sm'
        }`}
        title="Sign in with Google"
      >
        {isSigningIn ? (
          <div className={`w-4 h-4 border-2 rounded-full animate-spin ${isDark ? 'border-neutral-500 border-t-white' : 'border-gray-300 border-t-gray-600'}`} />
        ) : (
          <>
            <GoogleLogo className="w-4 h-4" />
            <span className={`text-sm ${isDark ? 'text-neutral-300' : 'text-gray-700'}`}>Sign in</span>
          </>
        )}
      </motion.button>
    );
  }

  // Full button variant (for Results page)
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={handleSignIn}
      disabled={isSigningIn}
      className="flex items-center justify-center gap-3 px-6 py-3 bg-white text-gray-700 rounded-xl font-medium shadow-lg hover:shadow-xl transition-all disabled:opacity-50"
    >
      {isSigningIn ? (
        <div className="w-5 h-5 border-2 border-gray-400 border-t-gray-700 rounded-full animate-spin" />
      ) : (
        <>
          <GoogleLogo className="w-5 h-5" />
          <span>Sign in to save results</span>
        </>
      )}
    </motion.button>
  );
}
