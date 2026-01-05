import { createContext, useContext, useState, useEffect } from 'react';
import {
  signInWithPopup,
  signInWithRedirect,
  getRedirectResult,
  signOut,
  onAuthStateChanged
} from 'firebase/auth';
import { auth, googleProvider } from '../firebase';

const AuthContext = createContext(null);

// Detect if we're in an in-app browser or environment where popups don't work well
const isInAppBrowser = () => {
  const ua = navigator.userAgent || navigator.vendor || window.opera;
  // Check for common in-app browser patterns
  return (
    /FBAN|FBAV|Instagram|Twitter|Line|WhatsApp|Snapchat|Pinterest/i.test(ua) ||
    // iOS webview
    (/(iPhone|iPod|iPad).*AppleWebKit(?!.*Safari)/i.test(ua)) ||
    // Android webview
    (/wv\)/.test(ua) && /Android/.test(ua)) ||
    // Generic webview detection
    /WebView/i.test(ua)
  );
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  useEffect(() => {
    // Check for redirect result first (in case we're returning from a redirect sign-in)
    getRedirectResult(auth)
      .then((result) => {
        if (result?.user) {
          setUser(result.user);
        }
      })
      .catch((error) => {
        // Ignore "no redirect operation" errors, only log real errors
        if (error.code !== 'auth/popup-closed-by-user' &&
            error.code !== 'auth/cancelled-popup-request') {
          console.error('Redirect result error:', error);
          setAuthError(error.message);
        }
      });

    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user);
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const signInWithGoogle = async () => {
    setAuthError(null);

    // Use redirect for in-app browsers, popup for regular browsers
    if (isInAppBrowser()) {
      try {
        // For in-app browsers, redirect is more reliable
        await signInWithRedirect(auth, googleProvider);
        // This won't return - page will redirect
      } catch (error) {
        console.error('Google sign-in redirect error:', error);
        setAuthError(error.message);
        throw error;
      }
    } else {
      // Try popup first for regular browsers
      try {
        const result = await signInWithPopup(auth, googleProvider);
        return result.user;
      } catch (error) {
        // If popup fails (blocked, closed, etc.), try redirect as fallback
        if (error.code === 'auth/popup-blocked' ||
            error.code === 'auth/popup-closed-by-user' ||
            error.code === 'auth/cancelled-popup-request') {
          console.log('Popup failed, falling back to redirect...');
          try {
            await signInWithRedirect(auth, googleProvider);
          } catch (redirectError) {
            console.error('Redirect fallback failed:', redirectError);
            setAuthError(redirectError.message);
            throw redirectError;
          }
        } else {
          console.error('Google sign-in error:', error);
          setAuthError(error.message);
          throw error;
        }
      }
    }
  };

  const logout = async () => {
    try {
      await signOut(auth);
    } catch (error) {
      console.error('Sign out error:', error);
      throw error;
    }
  };

  const value = {
    user,
    loading,
    signInWithGoogle,
    logout,
    isAuthenticated: !!user,
    authError
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
