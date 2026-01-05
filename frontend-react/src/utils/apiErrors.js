/**
 * Standardized API error handling utilities
 * Provides user-friendly error messages and consistent error structure
 */

/**
 * Error codes for different error types
 */
export const ErrorCodes = {
  NETWORK_ERROR: 'NETWORK_ERROR',
  UNAUTHORIZED: 'UNAUTHORIZED',
  FORBIDDEN: 'FORBIDDEN',
  NOT_FOUND: 'NOT_FOUND',
  RATE_LIMITED: 'RATE_LIMITED',
  SERVER_ERROR: 'SERVER_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  TIMEOUT: 'TIMEOUT',
  UNKNOWN: 'UNKNOWN'
};

/**
 * Parse and standardize API errors
 * Returns user-friendly error messages
 *
 * @param {Error|Response} error - The error from fetch or other source
 * @returns {{ code: string, message: string, retry: boolean, status?: number }}
 */
export function handleApiError(error) {
  // Network error (fetch failed, no response)
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return {
      code: ErrorCodes.NETWORK_ERROR,
      message: 'Unable to connect. Please check your internet connection.',
      retry: true
    };
  }

  // Timeout error
  if (error.name === 'AbortError') {
    return {
      code: ErrorCodes.TIMEOUT,
      message: 'Request timed out. Please try again.',
      retry: true
    };
  }

  // Response errors (from fetch that returned non-ok status)
  if (error.status || error.response?.status) {
    const status = error.status || error.response?.status;
    const data = error.data || error.response?.data;

    switch (status) {
      case 400:
        return {
          code: ErrorCodes.VALIDATION_ERROR,
          message: data?.detail || data?.message || 'Invalid request. Please check your input.',
          retry: false,
          status
        };

      case 401:
        return {
          code: ErrorCodes.UNAUTHORIZED,
          message: 'Please sign in to continue.',
          retry: false,
          status
        };

      case 403:
        return {
          code: ErrorCodes.FORBIDDEN,
          message: "You don't have permission to access this resource.",
          retry: false,
          status
        };

      case 404:
        return {
          code: ErrorCodes.NOT_FOUND,
          message: 'The requested resource was not found.',
          retry: false,
          status
        };

      case 429:
        return {
          code: ErrorCodes.RATE_LIMITED,
          message: 'Too many requests. Please wait a moment and try again.',
          retry: true,
          status
        };

      case 500:
      case 502:
      case 503:
      case 504:
        return {
          code: ErrorCodes.SERVER_ERROR,
          message: 'Server error. Please try again in a moment.',
          retry: true,
          status
        };

      default:
        return {
          code: ErrorCodes.UNKNOWN,
          message: data?.detail || data?.message || 'Something went wrong. Please try again.',
          retry: true,
          status
        };
    }
  }

  // Generic error
  return {
    code: ErrorCodes.UNKNOWN,
    message: error.message || 'Something went wrong. Please try again.',
    retry: true
  };
}

/**
 * Wrapper for API calls with automatic error handling
 * Returns a consistent { data, error } structure
 *
 * @template T
 * @param {() => Promise<T>} fn - The async function to execute
 * @returns {Promise<{ data: T | null, error: { code: string, message: string, retry: boolean } | null }>}
 *
 * @example
 * const { data, error } = await apiCall(() => api.getProfile(id));
 * if (error) {
 *   showError(error.message);
 *   if (error.retry) {
 *     // Show retry button
 *   }
 * }
 */
export async function apiCall(fn) {
  try {
    const data = await fn();
    return { data, error: null };
  } catch (error) {
    return { data: null, error: handleApiError(error) };
  }
}

/**
 * Enhanced fetch wrapper with timeout and error handling
 *
 * @param {string} url - The URL to fetch
 * @param {RequestInit} [options={}] - Fetch options
 * @param {number} [timeoutMs=30000] - Timeout in milliseconds
 * @returns {Promise<Response>}
 */
export async function fetchWithTimeout(url, options = {}, timeoutMs = 30000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });

    if (!response.ok) {
      const error = new Error(`HTTP ${response.status}`);
      error.status = response.status;
      try {
        error.data = await response.json();
      } catch {
        // Response wasn't JSON
      }
      throw error;
    }

    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Check if an error is retryable
 * @param {{ code: string, retry: boolean }} error
 * @returns {boolean}
 */
export function isRetryableError(error) {
  return error?.retry === true;
}
