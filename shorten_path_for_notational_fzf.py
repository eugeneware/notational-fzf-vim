#!/usr/bin/env pypy3
# encoding: utf-8

# Supposedly, importing so that you don't need dots in names speeds up a
# script, and the point of this one is to run fast.

from os import pardir
from os.path import abspath, expanduser, join, sep, split, splitdrive
from pathlib import PurePath
from sys import platform, stdin


# These are floated to the top so they aren't recalculated every loop.  The
# most restrictive replacements should come earlier.
REPLACEMENTS = ("", pardir, "~")
old_paths = [abspath(expanduser(replacement)) for replacement in REPLACEMENTS]


def prettyprint_path(path: str, old_path: str, replacement: str) -> str:
    # Pretty print the path prefix
    path = path.replace(old_path, replacement, 1)
    # Truncate the rest of the path to a single character.
    short_path = join(replacement, *[x[0] for x in PurePath(path).parts[1:]])
    return short_path


def shorten(path: str):
    """Returns 2 strings, the shortened parent directory and the filename."""
    # We don't want to shorten the filename, just its parent directory, so we
    # `split()` and just shorten `path`.
    path, filename = split(path)

    # use empty replacement for current directory. it expands correctly

    for replacement, old_path in zip(REPLACEMENTS, old_paths):
        if path.startswith(old_path):
            short_path = prettyprint_path(path, old_path, replacement)
            # to avoid multiple replacements
            break

    # If no replacement was found, shorten the entire path.
    else:
        short_path = join(*[x[0] for x in PurePath(path).parts])

    return short_path, filename


GREEN = "\033[32m"
PURPLE = "\033[35m"  # looks pink to me
CYAN = "\033[36m"

RESET = "\033[0m"

# RED = '\033[31m'
# BLUE = '\033[34m'
# LIGHTRED = '\033[91m'
# YELLOW = '\033[93m'
# LIGHTBLUE = '\033[94m'
# LIGHTCYAN = '\033[96m'


def color(line, color):
    return color + line + RESET


def process_line(line: str) -> str:
    # Expected format is colon separated `name:line number:contents`

    if platform.startswith('win32'):
        # Windows paths may contain a colon, e.g. C:\Windows\ which messes up the split
        # splitdrive(string) results in the following:
        #   Windows drive letter, e.g. C:\Windows\Folder\Foo.txt -> ('C', '\Windows\Folder\Foo.txt')
        #   Windows UNC path, e.g. \\Server\Share\Folder\Foo.txt -> ('\\Server\Share', '\Folder\Foo.txt')
        #   *nix, e.g. /any/path/to/file.txt -> ('', '/any/path/to/file.txt')
        #  Replace the : with a _ because the : will cause problems with FZF's delimiters, too.
        drive, remainder = splitdrive(line)
        line = drive.replace(':', '_') + remainder
    filename, linenum, contents = line.split(sep=":", maxsplit=2)

    # Drop trailing newline.
    contents = contents.rstrip()

    # Normalize path for further processing.
    if not platform.startswith('win32'):
        # This prepends cwd in Windows which is unnecessary.
        filename = abspath(filename)

    shortened_parent, basename = shorten(filename)
    # The conditional is to avoid a leading slash if the parent is replaced
    # with an empty directory. The slash is manually colored because otherwise
    # `os.path.join` won't do it.
    if shortened_parent:
        colored_short_name = color(shortened_parent + sep, PURPLE) + color(
            basename, CYAN
        )
    else:
        colored_short_name = color(basename, CYAN)

    # Format is: long form, line number, short form, line number, rest of line. This is so Vim can process it.
    formatted_line = ":".join(
        [
            color(filename, CYAN),
            color(linenum, GREEN),
            colored_short_name,
            color(linenum, GREEN),
            contents,
        ]
    )
    return formatted_line

    # We print the long and short forms, and one form is picked in the Vim script that uses this.
    # print(formatted_line)


if __name__ == "__main__":
    for line in stdin:
        print(process_line(line))
