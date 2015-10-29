#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""generate_substituted_files.py

Generate multiple files from a number of template files and a rules file

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
import logging
import optparse
import re
import sys

from string import Template


__version__ = '0.3.0'


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

PARAMETER_FILE_NAME = 'file_name'
PARAMETER_DELIMITER = 'delimiter'
PARAMETER_TEMPLATE_NAME = 'template_name'
PARAMETER_TEMPLATE_VARIABLE = 'template_variable'

PRESET_FIELD_DELIMITER = '|'
PRESET_TEMPLATE_NAME = 'template'

PRX_IDENTIFIER_DISALLOWED = re.compile(r'[^a-z\d_]', re.I)

PRX_PARAMETER = re.compile(r'\A(?P<{0}>\w+?):\s*'
                           r'(?P<{1}>.+?)\s*\Z'.format(KEY_PARAMETER,
                                                       KEY_VALUE))

RC_ERROR = 1
RC_OK = 0


#
# Function definitions
#


def identifier_from_heading(heading):
    """Make a variable name from a heading:
    strip whitespace, uppercase, replace disallowed characters by underlines
    """
    return PRX_IDENTIFIER_DISALLOWED.sub(UNDERLINE,
                                         heading.strip().upper())


def get_command_line_options():
    """Parse command line options and return options and arguments"""
    option_parser = optparse.OptionParser(
        description=('Apply the rules from the given file and generate'
                     ' a number of target files from the template files'
                     ' with values from the substitution table in the'
                     ' rules file substituted.'),
        version=__version__)
    option_parser.set_defaults(help_rules_file=False,
                               rules_file=None,
                               verbose=False)
    option_parser.add_option('--help-rules', '--help-rules-file',
                             action='store_true',
                             dest='help_rules_file',
                             help='Show rules file syntax')
    option_parser.add_option('-r', '--rules', '--rules-file',
                             action='store',
                             dest='rules_file',
                             help='The name of the file containing the rules')
    option_parser.add_option('-v', '--verbose',
                             action='store_true',
                             dest='verbose',
                             help='Print debugging messages')
    return option_parser.parse_args()


def get_rules_from_file(rules_file_name):
    """Read the given rules file and return a list of
    (file name template, file content template) pairs
    and a list of substitutes
    """
    field_delimiter = PRESET_FIELD_DELIMITER
    template_name = PRESET_TEMPLATE_NAME
    template_variable = None
    file_name_templates_list = []
    raw_substitutes = collections.deque()
    with open(rules_file_name, mode=MODE_READ) as rules_file:
        for line in rules_file:
            line = line.strip()
            if line.startswith(COMMENT_SIGN) or not line:
                continue
            try:
                parameter_definition = PRX_PARAMETER.match(line).groupdict()
            except AttributeError:
                raw_substitutes.append(line)
            else:
                parameter = parameter_definition[KEY_PARAMETER]
                value = parameter_definition[KEY_VALUE]
                if parameter == PARAMETER_FILE_NAME:
                    file_name_templates_list.append(Template(value))
                elif parameter == PARAMETER_DELIMITER:
                    field_delimiter = value
                elif parameter == PARAMETER_TEMPLATE_NAME:
                    template_name = value
                elif parameter == PARAMETER_TEMPLATE_VARIABLE:
                    template_variable = value
                #
            #
        #
    #
    # Set field names from header lines
    field_names_list = [identifier_from_heading(field_name)
                        for field_name in
                        raw_substitutes.popleft().split(field_delimiter)]
    # Create the templates list as a list of tuples, each containing
    # the file name template and the file content template
    templates_list = []
    if template_variable is None:
        template_variable = field_names_list[FIRST_INDEX]
    for file_name_template in file_name_templates_list:
        template_file_name = file_name_template.safe_substitute(
            {template_variable: template_name})
        with open(template_file_name, mode=MODE_READ) as template_file:
            templates_list.append((file_name_template,
                                   Template(template_file.read())))
        #
    # Create the substitutes list as a list of dicts
    substitutes_list = []
    for substitutes_line in raw_substitutes:
        field_values_list = [field_value.strip() for field_value in
                             substitutes_line.split(field_delimiter)]
        substitutes_list.append(dict(zip(field_names_list,
                                         field_values_list)))
    #
    return (templates_list, substitutes_list)


def apply_rules_from_file(rules_file_name):
    """Read the given rules file and directly apply the rules"""
    templates_list, substitutes_list = get_rules_from_file(rules_file_name)
    for substitute_values in substitutes_list:
        for (file_name_template, file_content_template) in templates_list:
            output_file_name = \
                file_name_template.safe_substitute(substitute_values)
            logging.debug('Writing file {0!r}...'.format(output_file_name))
            with open(output_file_name, mode=MODE_WRITE) as output_file:
                output_file.write(file_content_template.safe_substitute(
                    substitute_values))
            #
        #
    #


def show_rules_file_syntax(wrap_width=76):
    """Write a summary for the rules file syntax"""
    import textwrap
    list_prefix = ' * '
    continuation_prefix = '   '
    normal_wrapper = textwrap.TextWrapper(width=wrap_width)
    indented_wrapper = textwrap.TextWrapper(
        width=wrap_width,
        subsequent_indent=continuation_prefix)
    example_file_name = Template('main_data.${STAGE}.txt')
    example_header = ('Stage', 'Full name', 'other variable')
    example_substitutes = (('integ', 'Integration', 'dummy content'),
                           ('qa', 'Quality Assurance', 'random content'),
                           ('at', 'Acceptance Test', 'testing content'),
                           ('prod', 'Production', 'productive content'))
    example_variables = [identifier_from_heading(heading)
                         for heading in example_header]
    example_template_file_name = \
        example_file_name.substitute(STAGE=PRESET_TEMPLATE_NAME)
    example_output_file_names = [
        example_file_name.substitute(STAGE=substitute_values[FIRST_INDEX])
        for substitute_values in example_substitutes]
    # example_first_substitutes_set = dict(
    #     zip(example_variables, example_substitutes[FIRST_INDEX]))
    fs_substitutes_table_line = PRESET_FIELD_DELIMITER.join((
        '{0[0]:<6} ', ' {0[1]:<30} ', ' {0[2]:<30}'))
    output_list = [
        'Syntax for rules files',
        '----------------------',
        'The rules file is a plain text file defining file name templates'
        ' for the template file and the output files, as well as the'
        ' substitute values to be applied to each single output file.',
        '',
        'Comment lines starting with {0} are ignored.'.format(COMMENT_SIGN),
        '',
        'File name templates are defined by setting the parameter {0!r}'
        ' as shown in the following example:'.format(PARAMETER_FILE_NAME),
        '',
        '{0}: {1}'.format(PARAMETER_FILE_NAME, example_file_name.template),
        '',
        'Please note:',
        ' * The template must contain at least one variable in string.'
        'Template() syntax, see'
        ' https://docs.python.org/library/string.html#template-strings',
        '   The ${...} syntax is preferred for better readability.',
        ' * The variable name(s) must be in UPPER CASE.',
        ' * You need to define at least one file name template, and'
        ' you can define as many as you need.',
        '',
        'Additionally, you can override the following parameters in the'
        ' same way:',
        ' * {0!r} (default value: {1!r})'.format(PARAMETER_DELIMITER,
                                                 PRESET_FIELD_DELIMITER),
        '   The character used as delimiter in the substitutes table',
        ' * {0!r} (default value: {1!r})'.format(PARAMETER_TEMPLATE_NAME,
                                                 PRESET_TEMPLATE_NAME),
        '   The value substituted for the template file name',
        ' * {0!r} (not set)'.format(PARAMETER_TEMPLATE_VARIABLE),
        '   If this parameter is set, it defines the variable name used for'
        ' substituting the value defined above in the template file name.',
        '   If it is not set, the first variable name determined from'
        ' the substitutes header line -see explanation below- will be'
        ' used.',
        '',
        'The substitutes values for the target files are defined in a'
        ' simple table like the following example (the first line is'
        ' always the header):',
        '']
    output_list.extend([fs_substitutes_table_line.format(example_data_row)
                        for example_data_row in
                        (example_header,) + example_substitutes])
    output_list.extend([
        '',
        'The column headings will be translated to the variable names'
        ' {0[0]}, {0[1]} and {0[2]}. Placeholders in the template having'
        ' these identifiers will be substituted by the respective value'
        ' from each table row so there will be one result document per'
        ' table row.'.format(example_variables),
        '',
        'These example rules lead to the following results:',
        ' * The template file {0!r} will be read, and a string.Template()'
        ' will be generated from it.'.format(example_template_file_name),
        ' * The following output files will be generated:'
        ' {0}'.format(COMMA_BLANK.join(('{0!r}'.format(output_file)
                                        for output_file in
                                        example_output_file_names))),
        ' * For each output file, the template will be substituted as'
        ' described in the paragraph above, and the result document'
        ' will be written to the file.',
        ''])
    #
    for line in output_list:
        if line.startswith(list_prefix) or \
                line.startswith(continuation_prefix):
            wrapped_lines = indented_wrapper.wrap(line)
        elif not line:
            wrapped_lines = [EMPTY]
        else:
            wrapped_lines = normal_wrapper.wrap(line)
        #
        for single_line in wrapped_lines:
            print(single_line)
        #
    #


#
# Main script
#


if __name__ == '__main__':
    logging.basicConfig(format=FS_MESSAGE,
                        level=logging.DEBUG)
    OPTIONS, ARGUMENTS = get_command_line_options()
    del ARGUMENTS
    if OPTIONS.help_rules_file:
        show_rules_file_syntax()
        sys.exit(RC_OK)
    elif not OPTIONS.rules_file:
        logging.error('Please specify a rules file name!')
        sys.exit(RC_ERROR)
    if not OPTIONS.verbose:
        logging.getLogger(None).setLevel(logging.INFO)
    #
    apply_rules_from_file(OPTIONS.rules_file)
    sys.exit(RC_OK)


# vim:autoindent ts=4 sw=4 sts=4 expandtab:
