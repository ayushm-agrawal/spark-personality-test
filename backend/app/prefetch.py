"""
Question Pre-fetching System for Ception

This module implements speculative pre-fetching of likely next questions
based on LLM-predicted answer probabilities. This reduces perceived latency
by generating questions before the user submits their answer.
"""

import asyncio
import logging
import time
from typing import Dict, Optional, List, Callable, Any
from dataclasses import dataclass, field
from threading import Lock

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a dedicated logger for prefetch operations
prefetch_logger = logging.getLogger("prefetch")
prefetch_logger.setLevel(logging.INFO)


@dataclass
class PrefetchedQuestion:
    """A pre-generated question for a specific answer option."""
    answer_key: str
    question: Dict
    generated_at: float
    probability: float


@dataclass
class SessionPrefetchState:
    """Tracks prefetch state for a session."""
    session_id: str
    current_question_id: str
    prefetched: Dict[str, PrefetchedQuestion] = field(default_factory=dict)
    pending_tasks: List[asyncio.Task] = field(default_factory=list)
    lock: Lock = field(default_factory=Lock)
    created_at: float = field(default_factory=time.time)


class QuestionPreFetcher:
    """
    Manages speculative pre-fetching of next questions based on predicted answers.

    Usage:
        prefetcher = QuestionPreFetcher(generate_fn=generate_next_question_async)

        # After returning a question with predictions:
        await prefetcher.start_prefetch(
            session_id="abc123",
            current_question_id="q_1",
            predictions={"a": 0.6, "b": 0.3, "c": 0.1}
        )

        # When user submits answer:
        cached_question = await prefetcher.get_cached_question(
            session_id="abc123",
            current_question_id="q_1",
            answer_key="a"
        )
        if cached_question:
            return cached_question  # Fast path!
        else:
            return generate_fresh()  # Slow path
    """

    # Probability threshold - only prefetch options above this
    PROBABILITY_THRESHOLD = 0.10

    # Maximum number of options to prefetch (usually top 2)
    MAX_PREFETCH_OPTIONS = 2

    # Stagger delays by probability rank (ms)
    STAGGER_DELAYS = [0, 200, 400]  # First option immediate, second after 200ms, etc.

    # Cache expiry time (seconds)
    CACHE_TTL = 300  # 5 minutes

    # Maximum sessions to track (memory management)
    MAX_SESSIONS = 1000

    def __init__(self, generate_fn: Callable):
        """
        Initialize the prefetcher.

        Args:
            generate_fn: Async function that generates a question given (session_id, simulated_answer)
                         Should return the next question dict.
        """
        self.generate_fn = generate_fn
        self.sessions: Dict[str, SessionPrefetchState] = {}
        self._global_lock = Lock()

    def _cleanup_old_sessions(self):
        """Remove stale sessions to prevent memory bloat."""
        current_time = time.time()
        expired = [
            sid for sid, state in self.sessions.items()
            if current_time - state.created_at > self.CACHE_TTL
        ]
        for sid in expired:
            self._cancel_session(sid)

        # If still too many, remove oldest
        if len(self.sessions) > self.MAX_SESSIONS:
            sorted_sessions = sorted(
                self.sessions.items(),
                key=lambda x: x[1].created_at
            )
            for sid, _ in sorted_sessions[:len(self.sessions) - self.MAX_SESSIONS]:
                self._cancel_session(sid)

    def _cancel_session(self, session_id: str):
        """Cancel pending tasks and remove session from cache."""
        if session_id in self.sessions:
            state = self.sessions[session_id]
            for task in state.pending_tasks:
                if not task.done():
                    task.cancel()
            del self.sessions[session_id]

    async def start_prefetch(
        self,
        session_id: str,
        current_question_id: str,
        predictions: Dict[str, float],
        simulate_answer_fn: Optional[Callable] = None
    ):
        """
        Start pre-fetching questions for likely answers.

        Args:
            session_id: The session ID
            current_question_id: ID of the question being displayed
            predictions: Dict mapping answer keys to probabilities {"a": 0.6, "b": 0.3, "c": 0.1}
            simulate_answer_fn: Optional function to simulate an answer before generating
        """
        with self._global_lock:
            self._cleanup_old_sessions()

            # Cancel any existing prefetch for this session
            if session_id in self.sessions:
                self._cancel_session(session_id)

            # Create new prefetch state
            state = SessionPrefetchState(
                session_id=session_id,
                current_question_id=current_question_id
            )
            self.sessions[session_id] = state

        # Sort predictions by probability (descending)
        sorted_preds = sorted(
            predictions.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Filter by threshold and limit
        eligible = [
            (key, prob) for key, prob in sorted_preds
            if prob >= self.PROBABILITY_THRESHOLD
        ][:self.MAX_PREFETCH_OPTIONS]

        if not eligible:
            prefetch_logger.debug(f"[PREFETCH] No predictions above threshold for session {session_id}")
            return

        prefetch_logger.info(f"[PREFETCH] 🚀 Starting background prefetch for session {session_id[:8]}...")
        prefetch_logger.info(f"[PREFETCH] 📊 Predictions: {[(k, f'{p:.0%}') for k, p in eligible]}")

        # Launch staggered prefetch tasks
        for idx, (answer_key, probability) in enumerate(eligible):
            delay = self.STAGGER_DELAYS[idx] / 1000.0 if idx < len(self.STAGGER_DELAYS) else 0.5

            task = asyncio.create_task(
                self._prefetch_one(
                    state=state,
                    answer_key=answer_key,
                    probability=probability,
                    delay=delay,
                    simulate_answer_fn=simulate_answer_fn
                )
            )
            state.pending_tasks.append(task)

    async def _prefetch_one(
        self,
        state: SessionPrefetchState,
        answer_key: str,
        probability: float,
        delay: float,
        simulate_answer_fn: Optional[Callable]
    ):
        """Prefetch a single question after a delay."""
        try:
            if delay > 0:
                prefetch_logger.info(f"[PREFETCH] ⏳ Waiting {delay:.1f}s before prefetching answer '{answer_key}'...")
                await asyncio.sleep(delay)

            start_time = time.time()
            prefetch_logger.info(f"[PREFETCH] 🔄 Generating question for answer '{answer_key}' (p={probability:.0%})...")

            # Generate the question (this is the expensive LLM call)
            question = await self.generate_fn(
                state.session_id,
                answer_key,
                simulate_answer_fn
            )

            elapsed = time.time() - start_time

            if question and not question.get("error") and not question.get("prefetch_skip"):
                with state.lock:
                    state.prefetched[answer_key] = PrefetchedQuestion(
                        answer_key=answer_key,
                        question=question,
                        generated_at=time.time(),
                        probability=probability
                    )
                prefetch_logger.info(f"[PREFETCH] ✅ Prefetch COMPLETE for '{answer_key}' in {elapsed:.1f}s - Question cached!")
            elif question.get("prefetch_skip"):
                prefetch_logger.info(f"[PREFETCH] ⏭️ Skipped prefetch for '{answer_key}': {question.get('reason', 'unknown')}")
            else:
                prefetch_logger.warning(f"[PREFETCH] ⚠️ Prefetch failed for '{answer_key}': {question.get('error', 'unknown')}")

        except asyncio.CancelledError:
            prefetch_logger.info(f"[PREFETCH] 🚫 Prefetch cancelled for '{answer_key}' (user answered differently)")
        except Exception as e:
            prefetch_logger.error(f"[PREFETCH] ❌ Error prefetching '{answer_key}': {e}")

    async def get_cached_question(
        self,
        session_id: str,
        current_question_id: str,
        answer_key: str,
        max_wait_ms: int = 500
    ) -> Optional[Dict]:
        """
        Get a cached question if available, optionally waiting briefly for pending prefetch.

        Args:
            session_id: The session ID
            current_question_id: ID of the question that was answered
            answer_key: The answer the user selected
            max_wait_ms: Maximum time to wait for pending prefetch (0 = no wait)

        Returns:
            The cached question dict, or None if not available
        """
        if session_id not in self.sessions:
            return None

        state = self.sessions[session_id]

        # Verify this is for the right question
        if state.current_question_id != current_question_id:
            logging.debug(f"Question ID mismatch: {current_question_id} vs {state.current_question_id}")
            return None

        # Check if already cached
        with state.lock:
            if answer_key in state.prefetched:
                cached = state.prefetched[answer_key]
                # Check TTL
                if time.time() - cached.generated_at < self.CACHE_TTL:
                    age = time.time() - cached.generated_at
                    prefetch_logger.info(f"[PREFETCH] 🎯 CACHE HIT for '{answer_key}'! Using pre-generated question (age: {age:.1f}s)")
                    return cached.question

        # If not cached but we're willing to wait, check for pending task
        if max_wait_ms > 0:
            prefetch_logger.info(f"[PREFETCH] ⏳ Waiting up to {max_wait_ms}ms for pending prefetch of '{answer_key}'...")
            # Find the task for this answer
            for task in state.pending_tasks:
                if not task.done():
                    try:
                        await asyncio.wait_for(task, timeout=max_wait_ms / 1000.0)
                    except asyncio.TimeoutError:
                        prefetch_logger.info(f"[PREFETCH] ⏰ Timeout waiting for prefetch of '{answer_key}'")
                    except Exception as e:
                        prefetch_logger.error(f"[PREFETCH] Error waiting for prefetch: {e}")
                    break

            # Check again after waiting
            with state.lock:
                if answer_key in state.prefetched:
                    cached = state.prefetched[answer_key]
                    if time.time() - cached.generated_at < self.CACHE_TTL:
                        prefetch_logger.info(f"[PREFETCH] 🎯 CACHE HIT (after wait) for '{answer_key}'!")
                        return cached.question

        prefetch_logger.info(f"[PREFETCH] ❌ CACHE MISS for '{answer_key}' - generating fresh question")
        return None

    def invalidate_session(self, session_id: str):
        """Clear prefetch cache for a session (e.g., after answer submission)."""
        with self._global_lock:
            self._cancel_session(session_id)

    def get_cached_question_sync(
        self,
        session_id: str,
        current_question_id: str,
        answer_key: str
    ) -> Optional[Dict]:
        """
        Synchronous version of get_cached_question.

        Only returns immediately available cached questions, doesn't wait for pending.
        Use this from sync code paths.
        """
        if session_id not in self.sessions:
            return None

        state = self.sessions[session_id]

        # Verify this is for the right question
        if state.current_question_id != current_question_id:
            return None

        # Check if already cached
        with state.lock:
            if answer_key in state.prefetched:
                cached = state.prefetched[answer_key]
                # Check TTL
                if time.time() - cached.generated_at < self.CACHE_TTL:
                    age = time.time() - cached.generated_at
                    prefetch_logger.info(f"[PREFETCH] 🎯 SYNC CACHE HIT for '{answer_key}'! (age: {age:.1f}s)")
                    return cached.question

        return None

    def get_stats(self) -> Dict:
        """Get prefetcher statistics for monitoring."""
        total_prefetched = sum(
            len(state.prefetched) for state in self.sessions.values()
        )
        total_pending = sum(
            len([t for t in state.pending_tasks if not t.done()])
            for state in self.sessions.values()
        )
        return {
            "active_sessions": len(self.sessions),
            "total_prefetched": total_prefetched,
            "pending_tasks": total_pending
        }


# Singleton instance (will be initialized in services.py)
_prefetcher: Optional[QuestionPreFetcher] = None


def get_prefetcher() -> Optional[QuestionPreFetcher]:
    """Get the singleton prefetcher instance."""
    return _prefetcher


def init_prefetcher(generate_fn: Callable) -> QuestionPreFetcher:
    """Initialize the singleton prefetcher with the generate function."""
    global _prefetcher
    _prefetcher = QuestionPreFetcher(generate_fn=generate_fn)
    return _prefetcher
