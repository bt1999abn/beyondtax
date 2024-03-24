import math
import random
from decimal import Decimal

from django.conf import settings
from django.core.validators import RegexValidator
from accounts import constants as accounts_constants

PHONE_NUMBER_REGEX = RegexValidator(
    regex=r'^([1-9][0-9]{9})$', message=accounts_constants.PHONE_NUMBER_LIMIT_MESSAGE
)


def generate_otp():
    digits = "0123456789"
    otp = ""
    for _ in range(settings.EMAIL_OTP_LENGTH):
        otp += digits[math.floor(random.random() * len(digits))]
    return otp


def calculate_percentage(secured, total):
    return (secured / total) * 100


def calculate_percentage_value(total, percentage):
    return total * (percentage / 100)


def round_off_to_floor_fifty(number):
    number_of_fifties = math.floor(number / 50)
    return number_of_fifties * 50


def is_whole_number(number):
    if isinstance(number, Decimal):
        number = float(number)
    if isinstance(number, int) or (isinstance(number, float) and number.is_integer()):
        return True
    else:
        return False


def exclude_zeroes_in_decimal_number(number):
    """
    Converts 2.00 to 2
    :param number:
    :return:
    """
    return int(number) if is_whole_number(number) else number
