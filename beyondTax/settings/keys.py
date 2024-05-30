from beyondTax.settings.base import env


FRONTEND_HOST = env("FRONTEND_HOST")
HOST = env("HOST")

ENCODED_ID_ATTR = "encoded_id"


# FRONTEND URLS
FE_GOOGLE_LOGIN_SUCCESS = FRONTEND_HOST + "/google-signin-success/?token={token}"
