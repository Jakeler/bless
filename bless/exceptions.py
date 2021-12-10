class BlessError(Exception):
    """
    Base Exception for Bless
    """

class BlessUnsupportedHardware(BlessError):
    """
    Hardware does not support peripheral mode
    """