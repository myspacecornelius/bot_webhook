import sys
import os

# Add current directory to path so imports work
sys.path.append(os.getcwd())

from phantom.auth.license import LicenseValidator, UserTier

# Import the EXACT secret being used by the app code
from phantom.api.auth_routes import LICENSE_SECRET

print(f"Using Secret: {LICENSE_SECRET[:5]}...")

validator = LicenseValidator(LICENSE_SECRET)
key = validator.generate_license(
    user_id="admin-user-v2",
    email="admin@phantom.bot",
    tier=UserTier.ELITE,
    duration_days=3650
)

print(f"\nGenerated Key:\n{key}\n")

