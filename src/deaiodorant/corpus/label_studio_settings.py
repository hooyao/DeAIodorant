"""Label Studio settings for the loopback-only review service.

This module adapts Label Studio's Apache-2.0 Community Edition settings entry
point so the embedded-browser login can use a persistent local session.
"""

import json

from core.settings.base import *  # noqa: F403
from core.utils.secret_key import generate_secret_key_if_missing


SECRET_KEY = generate_secret_key_if_missing(BASE_DATA_DIR)  # noqa: F405

DJANGO_DB = get_env("DJANGO_DB", DJANGO_DB_SQLITE)  # noqa: F405
DATABASES = {"default": DATABASES_ALL[DJANGO_DB]}  # noqa: F405

MIDDLEWARE.append("organizations.middleware.DummyGetSessionMiddleware")  # noqa: F405
MIDDLEWARE.append("core.middleware.UpdateLastActivityMiddleware")  # noqa: F405
if INACTIVITY_SESSION_TIMEOUT_ENABLED:  # noqa: F405
    MIDDLEWARE.append("core.middleware.InactivitySessionTimeoutMiddleWare")  # noqa: F405

ADD_DEFAULT_ML_BACKENDS = False
LOGGING["root"]["level"] = get_env("LOG_LEVEL", "WARNING")  # noqa: F405
DEBUG = get_bool_env("DEBUG", False)  # noqa: F405
DEBUG_PROPAGATE_EXCEPTIONS = get_bool_env(  # noqa: F405
    "DEBUG_PROPAGATE_EXCEPTIONS", False
)
SESSION_COOKIE_SECURE = get_bool_env("SESSION_COOKIE_SECURE", False)  # noqa: F405
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

SENTRY_DSN = get_env(  # noqa: F405
    "SENTRY_DSN",
    "https://68b045ab408a4d32a910d339be8591a4@o227124.ingest.sentry.io/5820521",
)
SENTRY_ENVIRONMENT = get_env("SENTRY_ENVIRONMENT", "opensource")  # noqa: F405
FRONTEND_SENTRY_DSN = get_env(  # noqa: F405
    "FRONTEND_SENTRY_DSN",
    "https://5f51920ff82a4675a495870244869c6b@o227124.ingest.sentry.io/5838868",
)
FRONTEND_SENTRY_ENVIRONMENT = get_env(  # noqa: F405
    "FRONTEND_SENTRY_ENVIRONMENT", "opensource"
)
EDITOR_KEYMAP = json.dumps(get_env("EDITOR_KEYMAP"))  # noqa: F405

from label_studio import __version__
from label_studio.core.utils import sentry

sentry.init_sentry(release_name="label-studio", release_version=__version__)

from label_studio.core.utils.common import collect_versions

versions = collect_versions()
FEATURE_FLAGS_DEFAULT_VALUE = True
FEATURE_FLAGS_OFFLINE = get_bool_env("FEATURE_FLAGS_OFFLINE", True)  # noqa: F405
FEATURE_FLAGS_FILE = get_env("FEATURE_FLAGS_FILE", "feature_flags.json")  # noqa: F405
FEATURE_FLAGS_FROM_FILE = True
try:
    from core.utils.io import find_node

    find_node("label_studio", FEATURE_FLAGS_FILE, "file")
except IOError:
    FEATURE_FLAGS_FROM_FILE = False

STORAGE_PERSISTENCE = get_bool_env("STORAGE_PERSISTENCE", True)  # noqa: F405
USER_LOGIN_FORM = "deaiodorant.corpus.label_studio_auth.PersistentLocalLoginForm"
