from beyondTax.settings import base as base_settings

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ('knox.auth.TokenAuthentication',),
    "EXCEPTION_HANDLER": "drf_standardized_errors.handler.exception_handler",
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "shared.rest.renderer.CustomJSONRenderer",
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    'DEFAULT_PAGINATION_CLASS': 'shared.rest.pagination.CustomPagination',
    'PAGE_SIZE': 20,
    "DATETIME_FORMAT": base_settings.BASE_DATETIME_FORMAT,
    "DATETIME_INPUT_FORMATS": base_settings.BASE_INPUT_DATETIME_FORMATS
}

# CORS Settings
CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_WHITELIST = (
    'http://localhost:3000',
    'http://localhost:3001',
    'https://www.beyondtax.co',
    'https://beyondtax.co',
)
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://\w+\.beyondtax\.co$",
]

