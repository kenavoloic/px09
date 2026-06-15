"""
Django settings auto-selection module.

Automatically selects the appropriate settings module based on environment.
"""

import os

# Determine which settings to use based on environment
environment = os.environ.get("DJANGO_ENVIRONMENT", "dev")

if environment == "prod":
    from .prod import *
else:
    from .dev import *
