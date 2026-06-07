"""Loads .env on package import, before any submodule imports ``engine``:
``engine.data`` reads ``EWL_CACHE_DIR`` at import time, so the override must
already be in ``os.environ``. This ``__init__`` runs ahead of every ``apps.api.*`` submodule.
"""

from dotenv import load_dotenv

load_dotenv()
