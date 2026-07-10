"""Loads .env on package import, before any submodule reads configuration:
``apps.api.pipeline_ops`` resolves ``EWL_CACHE_DIR`` when it first builds the bar
repository. This ``__init__`` runs ahead of every ``apps.api.*`` submodule.
"""

from dotenv import load_dotenv

load_dotenv()
