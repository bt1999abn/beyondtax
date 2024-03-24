import environ
import os

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
env = environ.Env(
    DEBUG=(bool, False)
)

BASE_DATE_FORMAT = "%d-%m-%Y"
BASE_TIME_FORMAT = "%I:%M %p"
BASE_DATETIME_FORMAT = "%d-%m-%Y %I:%M %p"

BASE_INPUT_DATETIME_FORMATS = [
    BASE_DATETIME_FORMAT,
    "%Y-%m-%d %I:%M %p",
    "%Y-%m-%d %H:%M",
]

BASE_TIME_INPUT_FORMATS = [
    "%H:%M:%S",  # '14:30:59'
    "%H:%M:%S.%f",  # '14:30:59.000200'
    "%H:%M",  # '14:30'
    "%I:%M %p",  # '14:30'
]
