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
import os
import sys
import timeit
import urllib2
import urlparse


__version__ = '0.4.2'


# Disable some pylint warnings
# pylint: disable=logging-format-interpolation

#
# Standard constants
#

BLANK = ' '
COMMA = ','
COMMA_BLANK = COMMA + BLANK
COMMENT_SIGN = '#'
DASH = '-'
EMPTY = ''
FIRST_INDEX = 0
LAST_INDEX = -1
NEWLINE = '\n'
SLASH = '/'
UNDERLINE = '_'
ZERO = 0

#
# Module specific constants
#

DEFAULT_SHOW_PROGRESS = False

DIRECTORY_INDEX = 'index.html'

FS_ATTRIBUTE_ERROR = '{0!r} object has no attribute {1!r}'
FS_CALCULATED_DIGEST = '{checksum_type} checksum: {hexdigest}'
FS_HOURS = '{0}h'
FS_MESSAGE = '%(levelname)-8s | %(message)s'
FS_MINUTES = '{0}m'
FS_PROGRESS_BAR = ('PROGRESS | {bar_complete}{bar_remaining}'
                   ' | {percent_complete:5.1f}% complete'
                   ' | elapsed: {elapsed_time}'
                   ' | remaining: {estimated_time_remaining}'
                   '       \r')
FS_PROGRESS_SIMPLE = ('PROGRESS | {received_bytes} bytes received,'
                      ' elapsed time: {elapsed_time}\r')
FS_REPR = '{0}({1})'
FS_SECONDS = '{0:3.1f}s'

# Progress bar items
ITEM_COMPLETE = '#'
ITEM_REMAINING = '-'

MAXIMUM_CHUNKS_NUMBER = 10000
MINIMUM_CHUNK_SIZE = 2**16

MODE_READ = 'r'
MODE_WRITE = 'w'
MODE_WRITE_BINARY = 'wb'

MSG_DOWNLOADING = 'Downloading {0!r} ...'
MSG_DOWNLOAD_COMPLETE = 'Received {0} bytes in {1}'
MSG_SAVED_TO = 'Saved {0} bytes to {1!r}'
MSG_SCRIPT_FINISHED = 'Script finished. Returncode: {0}'

RC_ERROR = 1
RC_OK = 0


#
# Class definitions
#


class SimpleNamespace(dict):

    """A dict subclass that exposes its items as attributes."""

    def __init__(self, mapping_=None, **kwargs):
        """Initialize like a dict"""
        super(SimpleNamespace, self).__init__(mapping_ or kwargs)

    def __dir__(self):
        """Return a list of the member names"""
        return list(self)

    def __repr__(self):
        """Object representation"""
        return FS_REPR.format(type(self).__name__,
                              super(SimpleNamespace, self).__repr__())

    def __getattribute__(self, name):
        """Return an existing dict member"""
        try:
            return self[name]
        except KeyError:
            raise AttributeError(
                FS_ATTRIBUTE_ERROR.format(type(self).__name__, name))
        #

    def __setattr__(self, name, value):
        """Set an attribute"""
        self[name] = value

    def __delattr__(self, name):
        """Delete an attribute"""
        del self[name]


#
# Function definitions
#


def format_duration(total_seconds):
    """Return a duration formatted like
    '[[<hours>h ]<minutes>m ]<seconds>s'
    """
    duration_display = collections.deque()
    total_minutes, seconds = divmod(total_seconds, 60)
    duration_display.appendleft(FS_SECONDS.format(seconds))
    if total_minutes:
        hours, minutes = divmod(int(total_minutes), 60)
        duration_display.appendleft(FS_MINUTES.format(minutes))
        if hours:
            duration_display.appendleft(FS_HOURS.format(hours))
        #
    #
    return BLANK.join(duration_display)


def display_progress(received_bytes,
                     start_time,
                     bar_width=20,
                     stream=sys.stderr,
                     total_bytes=None):
    """Display progress.
    If total_bytes was provided, display a progress bar of the specified
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
            elapsed_time=format_duration(elapsed_time),
            estimated_time_remaining=\
                format_duration(estimated_time_remaining)))
    else:
        stream.write(FS_PROGRESS_SIMPLE.format(
            received_bytes=received_bytes,
            elapsed_time=format_duration(elapsed_time)))
    #
    stream.flush()


def download_chunks(http_response,
                    checksums=None,
                    chunk_size=None,
                    output_file=None,
                    show_progress=DEFAULT_SHOW_PROGRESS):
    """Download chunks from the given HTTP response,
    feed all hash objects given in the checksums dict with the data
    (i.e. calculate the checksums gradually), show progress if specified,
    write the chunks to the file if a file handle was given.
    Return a result namespace with a 'checksums' attribute
    and an additional 'content' attribute if no output file was given.
    Modified from <http://stackoverflow.com/a/2030027>
    """
    if not checksums:
        checksums = {}
    saved_content = []
    try:
        total_bytes = \
            int(http_response.info().getheader('Content-Length').strip())
    except (AttributeError, ValueError):
        total_bytes = None
        chunk_size = MINIMUM_CHUNK_SIZE
    else:
        if chunk_size is None:
            chunk_size = \
                int(round(float(total_bytes) / MAXIMUM_CHUNKS_NUMBER))
        if chunk_size < MINIMUM_CHUNK_SIZE:
            chunk_size = MINIMUM_CHUNK_SIZE
        #
    #
    start_time = timeit.default_timer()
    received_bytes = ZERO
    # read first chunk
    chunk = http_response.read(chunk_size)
    while chunk:
        # calculate checksums
        for single_checksum in checksums.values():
            single_checksum.update(chunk)
        # write to output file
        if output_file:
            output_file.write(chunk)
        else:
            saved_content.append(chunk)
        # display progress
        received_bytes = received_bytes + len(chunk)
        if show_progress:
            display_progress(received_bytes,
                             start_time,
                             stream=sys.stderr,
                             total_bytes=total_bytes)
        # read next chunk
        chunk = http_response.read(chunk_size)
    #
    elapsed_time = timeit.default_timer() - start_time
    if show_progress:
        sys.stderr.write(NEWLINE)
    logging.debug(
        MSG_DOWNLOAD_COMPLETE.format(received_bytes,
                                     format_duration(elapsed_time)))
    return SimpleNamespace(checksums=checksums,
                           content=EMPTY.join(saved_content),
                           received_bytes=received_bytes,
                           returncode=RC_OK)


def display_directly(url):
    """Download in chunks and display directly."""
    logging.debug(MSG_DOWNLOADING.format(url))
    http_response = urllib2.urlopen(url)
    result = download_chunks(http_response,
                             output_file=sys.stdout,
                             show_progress=False)
    sys.stdout.flush()
    return result


def get_checksums_mapping(checksums_list):
    """Return a mapping of hash objects from the given
    checksum types list
    """
    checksums_mapping = {}
    if checksums_list:
        for checksum_type in checksums_list:
            try:
                checksums_mapping[checksum_type.upper()] = \
                    hashlib.new(checksum_type.lower())
            except ValueError as value_error:
                logging.warn(value_error)
            #
        #
    #
    return checksums_mapping


def get_content(url,
                calculate_checksums=None,
                show_progress=DEFAULT_SHOW_PROGRESS):
    """Download in chunks, show progress, calculate checksums,
    and return the content.
    """
    checksums = get_checksums_mapping(calculate_checksums)
    logging.debug(MSG_DOWNLOADING.format(url))
    http_response = urllib2.urlopen(url)
    return download_chunks(http_response,
                           checksums=checksums,
                           output_file=None,
                           show_progress=show_progress)
    #


def save_to_file(url,
                 calculate_checksums=None,
                 output_directory=None,
                 output_file_name=None,
                 show_progress=DEFAULT_SHOW_PROGRESS):
    """Download in chunks, show progress, calculate checksums,
    and save to the target directory.
    """
    # output file name '-' => direct output to stdout
    if output_file_name == DASH:
        return display_directly(url)
    #
    checksums = get_checksums_mapping(calculate_checksums)
    if not output_directory:
        output_directory = os.getcwd()
    if not output_file_name:
        output_path = urlparse.urlparse(url).path
        output_file_name = output_path.split(SLASH)[LAST_INDEX]
    if not output_file_name:
        # URL path ends in a slash
        output_file_name = DIRECTORY_INDEX
    output_file_path = os.path.join(output_directory, output_file_name)
    #
    logging.debug(MSG_DOWNLOADING.format(url))
    http_response = urllib2.urlopen(url)
    with open(output_file_path, MODE_WRITE_BINARY) as output_file:
        result = download_chunks(http_response,
                                 checksums=checksums,
                                 output_file=output_file,
                                 show_progress=show_progress)
    logging.debug(MSG_SAVED_TO.format(result.received_bytes,
                                      output_file_path))
    return result


def get_command_line_options():
    """Parse command line options and return options and arguments"""
    option_parser = optparse.OptionParser(
        description=('Fetch a URL in chunks, display a progress bar'
                     ' and calculate checksums.'),
        usage='%prog [options] url',
        version=__version__)
    option_parser.set_defaults(calculate_checksums=[],
                               output_path=None,
                               show_progress=DEFAULT_SHOW_PROGRESS,
                               verbose=False)
    option_parser.add_option('-c', '--checksum', '--calculate-checksum',
                             action='append',
                             dest='calculate_checksums',
                             metavar='CHECKSUM',
                             help='calculate the given checksum type,'
                             ' e.g. MD5 or SHA1 (may be specified'
                             ' multiple times to calculating different'
                             ' digest types).')
    option_parser.add_option('-o', '--output',
                             action='store',
                             dest='output_path',
                             help='output to OUTPUT_PATH.')
    option_parser.add_option('-p', '--progress', '--show_progress',
                             action='store_true',
                             dest='show_progress',
                             help='show progress while downloading.')
    option_parser.add_option('-v', '--verbose',
                             action='store_true',
                             dest='verbose',
                             help='print debugging messages.')
    return option_parser.parse_args()


def main(command_line_options):
    """Main program function"""
    options, arguments = command_line_options
    if not options.verbose:
        logging.getLogger(None).setLevel(logging.INFO)
    #
    output_file_name = None
    if options.output_path:
        if os.path.isdir(options.output_path):
            output_directory = options.output_path
        else:
            output_directory, output_file_name = \
                os.path.split(options.output_path)
            #
        #
    else:
        output_directory = None
    #
    download_result = save_to_file(
        arguments[FIRST_INDEX],
        calculate_checksums=options.calculate_checksums,
        output_directory=output_directory,
        output_file_name=output_file_name,
        show_progress=options.show_progress)
    #
    for checksum_type, single_checksum in download_result.checksums.items():
        logging.info(FS_CALCULATED_DIGEST.format(
            checksum_type=checksum_type.upper(),
            hexdigest=single_checksum.hexdigest()))
    return download_result.returncode


#
# Main program call
#


if __name__ == '__main__':
    logging.basicConfig(format=FS_MESSAGE,
                        level=logging.DEBUG)
    RETURNCODE = main(get_command_line_options())
    logging.debug(MSG_SCRIPT_FINISHED.format(RETURNCODE))
    sys.exit(RETURNCODE)


# vim:autoindent ts=4 sw=4 sts=4 expandtab:
