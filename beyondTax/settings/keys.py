from beyondTax.settings.base import env
from beyondTax.settings.django_settings import IS_LIVE


FRONTEND_HOST = env("FRONTEND_HOST")
HOST = env("HOST")

BACKEND_BASE_URL = f"https://{HOST}" if IS_LIVE else f"http://{HOST}"

ENCODED_ID_ATTR = "encoded_id"


# FRONTEND URLS
FE_GOOGLE_LOGIN_SUCCESS = FRONTEND_HOST + "/google-signin-success/?token={token}"
