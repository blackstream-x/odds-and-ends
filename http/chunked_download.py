#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""chunked_download.py

Download files from an HTTP server in chunks, display a progress bar
if requested, and calculate the specified checksums.

Copyright (C) 2015 Rainer Schwarzbach
                   <blackstream-x@users.noreply.github.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import collections
import hashlib
import logging
import optparse
import re
import sys
import urllib2


__version__ = '0.0.1'


BLANK = ' '
COMMA = ','
COMMA_BLANK = COMMA + BLANK
COMMENT_SIGN = '#'
EMPTY = ''
UNDERLINE = '_'

FIRST_INDEX = 0

FS_MESSAGE = '%(levelname)-8s | %(message)s'

KEY_PARAMETER = 'parameter'
KEY_VALUE = 'value'

MODE_READ = 'r'
MODE_WRITE = 'w'

RC_ERROR = 1
RC_OK = 0


#
# Function definitions
#


def get_command_line_options():
    """Parse command line options and return options and arguments"""
    option_parser = optparse.OptionParser(
        description=('Fetch a URL in chunks, display a progress bar'
                     ' and calculate checksums.'),
        version=__version__)
    option_parser.set_defaults(verbose=False)
    option_parser.add_option('-v', '--verbose',
                             action='store_true',
                             dest='verbose',
                             help='Print debugging messages')
    return option_parser.parse_args()


def main(command_line_options):
    """Main program function"""
    options, arguments = command_line_options
    if not options.verbose:
        logging.getLogger(None).setLevel(logging.INFO)
    #
    return RC_OK


#
# Main program call
#


if __name__ == '__main__':
    logging.basicConfig(format=FS_MESSAGE,
                        level=logging.DEBUG)
    RETURNCODE = main(get_command_line_options())
    logging.debug(MSG_SCRIPT_FINISHED.format(RETURNCODE)
    sys.exit(RETURNCODE)


# vim:autoindent ts=4 sw=4 sts=4 expandtab:
