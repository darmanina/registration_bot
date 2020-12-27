#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import re


def read_env(path='.env'):
    """
    Pulled from a gist by bennilope. https://gist.github.com/bennylope/2999704
    This is Honcho code with minor updates, it reads local default
    environment variables from a .env file located in the project root
    directory.
    """
    try:
        with open(path) as f:
            content = f.read()
    except IOError:
        content = ''

    for line in content.splitlines():
        m1 = re.match(r'\A([A-Za-z_0-9]+)=(.*)\Z', line)
        if m1:
            key, val = m1.group(1), m1.group(2)
            m2 = re.match(r"\A'(.*)'\Z", val)
            if m2:
                val = m2.group(1)
            m3 = re.match(r'\A"(.*)"\Z', val)
            if m3:
                val = re.sub(r'\\(.)', r'\1', m3.group(1))
            os.environ.setdefault(key, val)


def env_var(key, default=None):
    """
    Retrieves env vars and makes Python boolean replacements
    """
    val = os.environ.get(key, default)
    if val == 'True':
        val = True
    elif val == 'False':
        val = False
    return val


def with_env(fn):
    """
    Just a simple decorator to load env vars. sAnd set terminal title to currently called function.
    """
    read_env()

    #import sys
    #import inspect
    #
    #sys.stdout.write("\x1b]2;{0}\x07".format(inspect.stack()[0][3]))

    return fn


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chattree.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    read_env()
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
