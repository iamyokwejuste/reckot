import time
import logging
from enum import Enum
from typing import Callable, Any, Optional
from collections import deque
from threading import Lock
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpenException(Exception):
    pass


class GeminiCircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        name: str = "gemini_circuit"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._lock = Lock()
        self._failure_history = deque(maxlen=100)

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.time() - self._last_failure_time >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit breaker {self.name} entering HALF_OPEN state")
            return self._state

    def call(self, func: Callable, *args, **kwargs) -> Any:
        current_state = self.state

        if current_state == CircuitState.OPEN:
            logger.warning(f"Circuit breaker {self.name} is OPEN, rejecting call")
            raise CircuitBreakerOpenException(
                f"Circuit breaker {self.name} is OPEN. Service temporarily unavailable."
            )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                logger.info(f"Circuit breaker {self.name} call succeeded, closing circuit")
                self._state = CircuitState.CLOSED
                self._failure_count = 0

    def _on_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            self._failure_history.append({
                'timestamp': self._last_failure_time,
                'failure_count': self._failure_count
            })

            logger.warning(
                f"Circuit breaker {self.name} failure {self._failure_count}/{self.failure_threshold}"
            )

            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.error(
                    f"Circuit breaker {self.name} OPENED after {self._failure_count} failures"
                )

    def reset(self):
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None
            logger.info(f"Circuit breaker {self.name} manually reset")

    def get_metrics(self) -> dict:
        with self._lock:
            return {
                'name': self.name,
                'state': self._state.value,
                'failure_count': self._failure_count,
                'failure_threshold': self.failure_threshold,
                'last_failure_time': self._last_failure_time,
                'recovery_timeout': self.recovery_timeout,
                'recent_failures': list(self._failure_history)
            }


class ModelFallbackStrategy:
    def __init__(self):
        self.primary_model = getattr(settings, "GEMINI_MODEL", "gemini-3-flash-preview")
        self.fallback_models = [
            getattr(settings, "GEMINI_LITE_MODEL", "gemini-1.5-flash-8b"),
            "gemini-1.5-flash",
        ]
        self.current_model_index = 0
        self._lock = Lock()

    def get_current_model(self) -> str:
        with self._lock:
            if self.current_model_index == 0:
                return self.primary_model
            elif self.current_model_index <= len(self.fallback_models):
                return self.fallback_models[self.current_model_index - 1]
            return self.primary_model

    def switch_to_fallback(self) -> Optional[str]:
        with self._lock:
            self.current_model_index += 1
            if self.current_model_index <= len(self.fallback_models):
                next_model = self.fallback_models[self.current_model_index - 1]
                logger.info(f"Switching to fallback model: {next_model}")
                return next_model
            logger.error("All fallback models exhausted")
            return None

    def reset_to_primary(self):
        with self._lock:
            self.current_model_index = 0
            logger.info(f"Reset to primary model: {self.primary_model}")


class RequestQueue:
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.queue = deque(maxlen=max_size)
        self._lock = Lock()

    def enqueue(self, request_data: dict):
        with self._lock:
            self.queue.append({
                'data': request_data,
                'timestamp': time.time(),
                'retry_count': 0
            })
            logger.info(f"Request queued. Queue size: {len(self.queue)}")

    def dequeue(self) -> Optional[dict]:
        with self._lock:
            if self.queue:
                return self.queue.popleft()
            return None

    def get_size(self) -> int:
        with self._lock:
            return len(self.queue)

    def clear(self):
        with self._lock:
            self.queue.clear()
            logger.info("Request queue cleared")


gemini_circuit_breaker = GeminiCircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    name="gemini_primary"
)

model_fallback = ModelFallbackStrategy()
failed_request_queue = RequestQueue(max_size=100)
