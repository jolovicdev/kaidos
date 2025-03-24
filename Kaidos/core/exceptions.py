class KaidosError(Exception):
    """Base exception class for all Kaidos-related errors."""
    pass


class BlockchainError(KaidosError):
    """Base exception class for blockchain-related errors."""
    pass


class InvalidBlockError(BlockchainError):
    """Raised when a block fails validation."""
    pass


class ChainValidationError(BlockchainError):
    """Raised when blockchain validation fails."""
    pass


class TransactionError(KaidosError):
    """Base exception class for transaction-related errors."""
    pass


class InvalidTransactionError(TransactionError):
    """Raised when a transaction fails validation."""
    pass


class InsufficientFundsError(TransactionError):
    """Raised when a transaction attempts to spend more than available."""
    pass


class WalletError(KaidosError):
    """Base exception class for wallet-related errors."""
    pass


class KeyGenerationError(WalletError):
    """Raised when key generation fails."""
    pass


class SignatureError(WalletError):
    """Raised when transaction signing or verification fails."""
    pass


class NetworkError(KaidosError):
    """Base exception class for network-related errors."""
    pass


class NodeConnectionError(NetworkError):
    """Raised when connection to a node fails."""
    pass


class ConsensusError(NetworkError):
    """Raised when consensus algorithm fails."""
    pass


class DatabaseError(KaidosError):
    """Raised when database operations fail."""
    pass
