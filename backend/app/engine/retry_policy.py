import random

class RetryPolicy:
    @staticmethod
    def calculate_backoff(attempt: int, base_delay: float = 2.0, max_delay: float = 60.0, jitter_ratio: float = 0.25) -> float:
        """
        Calculates exponential backoff with full jitter to avoid thundering herd problems.
        Formula: Delay = min(max_delay, base * 2^(attempt - 1)) + jitter
        """
        if attempt <= 0:
            return 0.0
        
        exponential = base_delay * (2 ** (attempt - 1))
        capped = min(max_delay, exponential)
        
        # Add random jitter
        jitter = random.uniform(0, capped * jitter_ratio)
        return round(capped + jitter, 2)
