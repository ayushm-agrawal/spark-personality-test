import { createContext, useContext, useState, useEffect, useRef } from 'react';
import {
  signInWithPopup,
  signInWithRedirect,
  getRedirectResult,
  signOut,
  onAuthStateChanged
} from 'firebase/auth';
import { auth, googleProvider } from '../firebase';

const AuthContext = createContext(null);

// Detect if we're in an in-app browser where popups don't work
const isInAppBrowser = () => {
  const ua = navigator.userAgent || navigator.vendor || window.opera;
  return (
    /FBAN|FBAV|Instagram|Twitter|Line|WhatsApp|Snapchat|Pinterest/i.test(ua) ||
    /(iPhone|iPod|iPad).*AppleWebKit(?!.*Safari)/i.test(ua) ||
    (/wv\)/.test(ua) && /Android/.test(ua)) ||
    /WebView/i.test(ua)
  );
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);
  const redirectChecked = useRef(false);

  useEffect(() => {
    // Only check redirect result once (StrictMode protection)
    if (!redirectChecked.current) {
      redirectChecked.current = true;
      getRedirectResult(auth)
        .then((result) => {
          if (result?.user) {
            setUser(result.user);
          }
        })
        .catch((error) => {
          if (error.code !== 'auth/popup-closed-by-user') {
            console.error('Redirect result error:', error);
          }
        });
    }

    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user);
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const signInWithGoogle = async () => {
    setAuthError(null);

    // Use redirect directly for in-app browsers (popups don't work there)
    if (isInAppBrowser()) {
      try {
        await signInWithRedirect(auth, googleProvider);
        return; // Won't reach here - page redirects
      } catch (error) {
        console.error('Google sign-in redirect error:', error);
        setAuthError(error.message);
        throw error;
      }
    }

    // For regular browsers (desktop and mobile Safari/Chrome), try popup first
    try {
      const result = await signInWithPopup(auth, googleProvider);
      return result.user;
    } catch (error) {
      // If popup fails, fallback to redirect
      if (error.code === 'auth/popup-blocked' ||
          error.code === 'auth/popup-closed-by-user' ||
          error.code === 'auth/cancelled-popup-request') {
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
