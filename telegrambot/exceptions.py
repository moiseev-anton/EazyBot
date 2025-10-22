class StateExpiredError(Exception):
    """Raised when the stored context or state cannot be restored."""

    def __init__(self, message: str | None = None):
        self.message = message or "Failed to restore user context"
        super().__init__(self.message)