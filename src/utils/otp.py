"""One-time password (OTP) utilities.

This module provides a secure OTP generator used for short-lived user
verification (for example, email or SMS verification codes). It uses the
`secrets` module to ensure cryptographic randomness suitable for
authentication contexts.
"""

import secrets
import string


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP of the requested length.

    The function returns a string composed only of digits. It uses
    `secrets.choice` to pick digits from `string.digits`, which provides
    cryptographically secure randomness suitable for one-time codes.

    Args:
        length: Number of digits in the OTP. Defaults to 6.

    Returns:
        A string containing the generated numeric OTP.
    """

    otp = "".join(secrets.choice(string.digits) for _ in range(length))
    return otp