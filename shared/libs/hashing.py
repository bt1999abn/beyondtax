import hashlib
import logging as lg
import math
from django.conf import settings


logger = lg.getLogger(__name__)


class AlphaId(object):
    ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-_0123456789'
    MINLEN = 8
    PRIME_NUMBER = 53897

    # For encoding ids in email address because email addresses are not case sensitive
    ALTERNATE_ALPHABET = 'abcdefghijklmnopqrstuvwxyz0123456789-_'

    @staticmethod
    def __jumble_alphabet(alphabet, passkey):
        passhash = hashlib.sha256(passkey).hexdigest()
        sorted_list = sorted([(passhash[var], alphabet[var]) for var in range(len(alphabet))])
        return u''.join([val[1] for val in sorted_list])

    @classmethod
    def encode(cls, number, passkey=settings.SECRET_KEY, use_alternate_alphabet=False, prime_number=None):
        cached_result = AlphaIdCollection.alpha_encoded_cache.get(number)
        if cached_result:
            return cached_result
        else:
            alphabet = cls.ALTERNATE_ALPHABET if use_alternate_alphabet else cls.ALPHABET
            if passkey:
                passkey = passkey.encode('utf-8')
                alphabet = cls.__jumble_alphabet(alphabet, passkey)
            base = len(alphabet)

            copy_number = number
            pad = cls.MINLEN - 1
            number = int(int(number) * (prime_number or cls.PRIME_NUMBER) + pow(base, pad))
            encoded_number = []
            t_log = int(math.log(number, base))

            while True:
                bcp = int(pow(base, t_log))
                reduced_number = (number // bcp) % base
                encoded_number.append(alphabet[reduced_number])
                number -= reduced_number * bcp
                t_log -= 1
                if t_log < 0:
                    break
            encoded_result = u"{}".format(u"".join(reversed(encoded_number)))

            AlphaIdCollection.set_encoded_value(copy_number, encoded_result)
            return encoded_result

    @classmethod
    def decode(cls, string, passkey=settings.SECRET_KEY, use_alternate_alphabet=False, prime_number=None):
        if string is None:
            return string
        cached_result = AlphaIdCollection.alpha_decoded_cache.get(string)
        if cached_result:
            return cached_result
        else:
            alphabet = cls.ALPHABET if not use_alternate_alphabet else cls.ALTERNATE_ALPHABET
            if passkey:
                passkey = passkey.encode('utf-8')
                alphabet = cls.__jumble_alphabet(alphabet, passkey)
            base = len(alphabet)
            copy_string = string
            string = u"".join(reversed(string))
            s_number = 0
            len_string = len(string) - 1
            t_number = 0

            while True:
                bcpow = int(pow(base, len_string - t_number))
                try:
                    s_number += alphabet.index(string[t_number:t_number + 1]) * bcpow
                except ValueError:
                    return -1
                t_number += 1
                if t_number > len_string:
                    break

            pad = cls.MINLEN - 1
            s_number = int(s_number - pow(base, pad))

            decoded_number = s_number // (prime_number or cls.PRIME_NUMBER)
            AlphaIdCollection.set_decoded_value(copy_string, decoded_number)
            return decoded_number

    @classmethod
    def decode_if_encoded(cls, string, *args, **kwargs):
        try:
            value = int(string)
        except ValueError:
            value = cls.decode(string, *args, **kwargs)

        return value

    @classmethod
    def decode_list(cls, string_list, passkey=settings.SECRET_KEY, use_alternate_alphabet=False, prime_number=None):
        return [AlphaId.decode(string, passkey, use_alternate_alphabet, prime_number) for string in string_list]

    @classmethod
    def encode_list(cls, number_list, passkey=settings.SECRET_KEY, use_alternate_alphabet=False, prime_number=None):
        return [AlphaId.encode(number, passkey, use_alternate_alphabet, prime_number) for number in number_list]


class AlphaIdCollection(object):
    """
    Class to keep the Encoded AlphaId in app memory
    """
    # variable to be used globally for the already calculated alpha ids.
    alpha_encoded_cache = {}
    alpha_decoded_cache = {}

    @classmethod
    def set_encoded_value(cls, key, value):
        """
        Class Method, used to update the encoded cache
        :param key
        :param value
        :type key : Type should be an integer value
        :type value : Type String
        """
        cls.alpha_encoded_cache[key] = value

    @classmethod
    def set_decoded_value(cls, key, value):
        """
        Class Method, used to update the decoded cache
        :param key
        :param value
        :type key : Type String
        :type value : Type should be an integer value
        """
        cls.alpha_decoded_cache[key] = value


# Added inline To load the Alpha ids at the time of server start or app initialization

for i in range(settings.PRELOAD_ALPHAID_LIMIT):
    encoded_val = AlphaId.encode(i)
    AlphaIdCollection.set_encoded_value(i, encoded_val)
    AlphaIdCollection.set_decoded_value(encoded_val, i)
