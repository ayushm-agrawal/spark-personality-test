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

// Detect if we're on a real mobile device or in-app browser (not DevTools emulation)
const shouldUseRedirect = () => {
  // DevTools mobile emulation has maxTouchPoints = 0, real mobile has > 0
  const isRealMobile = navigator.maxTouchPoints > 0;

  // In localhost dev mode, always use popup (redirect has issues with StrictMode)
  if (window.location.hostname === 'localhost') {
    return false;
  }

  const ua = navigator.userAgent || navigator.vendor || window.opera;
  // Use redirect for real mobile or in-app browsers
  return (
    isRealMobile && (
      /Android|iPhone|iPad|iPod/i.test(ua) ||
      /FBAN|FBAV|Instagram|Twitter|Line|WhatsApp|Snapchat|Pinterest/i.test(ua) ||
      /(iPhone|iPod|iPad).*AppleWebKit(?!.*Safari)/i.test(ua) ||
      (/wv\)/.test(ua) && /Android/.test(ua)) ||
      /WebView/i.test(ua)
    )
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

    if (shouldUseRedirect()) {
      // Mobile/in-app browsers: use redirect
      try {
        await signInWithRedirect(auth, googleProvider);
      } catch (error) {
        console.error('Google sign-in redirect error:', error);
        setAuthError(error.message);
        throw error;
      }
    } else {
      // Desktop: use popup (COOP warnings are harmless)
      try {
        const result = await signInWithPopup(auth, googleProvider);
        return result.user;
      } catch (error) {
        if (error.code === 'auth/popup-blocked') {
          // Fallback to redirect if popup blocked
          await signInWithRedirect(auth, googleProvider);
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
