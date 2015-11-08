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
import timeit
import urllib2


__version__ = '0.1.0'


BLANK = ' '
COMMA = ','
COMMA_BLANK = COMMA + BLANK
COMMENT_SIGN = '#'
EMPTY = ''
UNDERLINE = '_'

FIRST_INDEX = 0

FS_MESSAGE = '%(levelname)-8s | %(message)s'
FS_PROGRESS_BAR = (r'[{bar_complete}{bar_remaining}]'
                   r' {percent_complete:5.1f}% complete'
                   r' | elapsed: {elapsed_time}'
                   r' | remaining: {estimated_time_remaining}\r')
FS_PROGRESS_SIMPLE = (r'{received_bytes} bytes received,'
                      r' elapsed time: {elapsed_time}\r')

# Progress bar items
ITEM_COMPLETE = '#'
ITEM_REMAINING = '-'

KEY_PARAMETER = 'parameter'
KEY_VALUE = 'value'

MODE_READ = 'r'
MODE_WRITE = 'w'

RC_ERROR = 1
RC_OK = 0


#
# Function definitions
#


def show_progress(received_bytes,
                  start_time,
                  bar_width=20,
                  stream=sys.stderr,
                  total_bytes=None):
    """Show progress.
    If total_bytes was provided, show a progress bar of the specified
    width in characters, with a percentage display and the elapsed and
    estimated remaining times.
    Else, just display the number of received bytes and the elapsed time.
    """
    elapsed_time = timeit.default_timer() - start_time
    if total_bytes:
        ratio_complete = float(received_bytes) / total_bytes
        estimated_time_remaining = \
            (1.0 - ratio_complete) / ratio_complete * elapsed_time
        bar_items_complete = int(ratio_complete * bar_width)
        bar_items_remaining = bar_width - bar_items_complete
        stream.write(FS_PROGRESS_BAR.format(
            bar_complete=bar_items_complete * ITEM_COMPLETE,
            bar_remaining=bar_items_remaining * ITEM_REMAINING,
            percent_complete=100 * ratio_complete,
            elapsed_time=time_display(elapsed_time),
            estimated_time_remaining=time_display(estimated_time_remaining))
    else:
        stream.write(FS_PROGRESS_SIMPLE.format(
            received_bytes=received_bytes,
            elapsed_time=time_display(elapsed_time)))
    #
    stream.flush()


def get_chunks(file_object, chunk_size=MINIMUM_CHUNK_SIZE):
    """Generator function yielding chunks of the specified size
    from the given file-like object (isable with a HTTP response).
    """
    chunk = file_object.read(chunk_size)
    while chunk:
        yield chunk
        chunk = file_object.read(chunk_size)
    #


def download_in_chunks(url,
                       calculate_checksums=None,
                       minimum_chunk_size=MINIMUM_CHUNK_SIZE,
                       maximum_chunks_number=MAXIMUM_CHUNKS_NUMBER,
                       target_directory=None,
                       target_file_name=None)
    """Download in chunks, show progress, calculate checksums,
    and save to the target directory
    """
    http_response = urllib2.open(url)
    try:
        total_bytes = ...
        chunk_size = \
            int(math.round(float(total_bytes) / maximum_chunks_number))
        if chunk_size < minimum_chunk_size:
            chunk_size = minimum_chunk_size
        #
    except (KeyError, ValueError):
        total_bytes = None
        chunk_size = minimum_chunk_size
    #
    start_time = timeit.default_timer()
    for chunk in get_chunks(http_response, chunk_size=chunk_size):
        # calculate checksums
        # write to target file
        # display progress
        pass
    sys.stderr.write(NEWLINE)


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
