class GithubRateLimitError(Exception):
    """Raised when github rate limit has exceeded"""
    pass

class GithubServerError(Exception):
    """Raised when Internal Server Error at Github"""
    pass

