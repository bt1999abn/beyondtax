import logging
import os
import re
import sys

from pathlib import PurePath as PathLike


Openable = (str, PathLike)

logger = logging.getLogger(__name__)


class ReadEnv:
    @classmethod
    def read_env(cls, env_file=None, encoding='utf8',
                 **overrides):
        r"""Read a .env file into os.environ.

        If not given a path to a dotenv path, does filthy magic stack
        backtracking to find the dotenv in the same directory as the file that
        called ``read_env``.

        Existing environment variables take precedent and are NOT overwritten
        by the file content. ``overwrite=True`` will force an overwrite of
        existing environment variables.

        Refs:

        * https://wellfire.co/learn/easier-12-factor-django

        :param env_file: The path to the ``.env`` file your application should
            use. If a path is not provided, `read_env` will attempt to import
            the Django settings module from the Django project root.
        :param overwrite: ``overwrite=True`` will force an overwrite of
            existing environment variables.
        :param encoding: The encoding to use when reading the environment file.
        :param \**overrides: Any additional keyword arguments provided directly
            to read_env will be added to the environment. If the key matches an
            existing environment variable, the value will be overridden.
        """
        if env_file is None:
            # pylint: disable=protected-access
            frame = sys._getframe()
            env_file = os.path.join(
                os.path.dirname(frame.f_back.f_code.co_filename),
                '.env'
            )
            if not os.path.exists(env_file):
                logger.info(
                    "%s doesn't exist - if you're not configuring your "
                    "environment separately, create one.", env_file)
                return

        try:
            if isinstance(env_file, Openable):
                # Python 3.5 support (wrap path with str).
                with open(str(env_file), encoding=encoding) as f:
                    content = f.read()
            else:
                with env_file as f:
                    content = f.read()
        except OSError:
            logger.info(
                "%s not found - if you're not configuring your "
                "environment separately, check this.", env_file)
            return

        logger.debug('Read environment variables from: %s', env_file)

        def _keep_escaped_format_characters(match):
            """Keep escaped newline/tabs in quoted strings"""
            escaped_char = match.group(1)
            if escaped_char in 'rnt':
                return '\\' + escaped_char
            return escaped_char

        for line in content.splitlines():
            m1 = re.match(r'\A(?:export )?([A-Za-z_0-9]+)=(.*)\Z', line)
            if m1:
                key, val = m1.group(1), m1.group(2)
                m2 = re.match(r"\A'(.*)'\Z", val)
                if m2:
                    val = m2.group(1)
                m3 = re.match(r'\A"(.*)"\Z', val)
                if m3:
                    val = re.sub(r'\\(.)', _keep_escaped_format_characters,
                                 m3.group(1))
                overrides[key] = str(val)
            elif not line or line.startswith('#'):
                # ignore warnings for empty line-breaks or comments
                pass
            else:
                logger.warning('Invalid line: %s', line)
        return overrides

