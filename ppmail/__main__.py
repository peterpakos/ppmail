#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tool to send messages via Sendgrid/Slack

Author: Peter Pakos <peter.pakos@wandisco.com>

Copyright (C) 2017 WANdisco

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

from __future__ import absolute_import, print_function
import os
import sys
import argparse
import platform
from pplogger import get_logger

from .mailer import Mailer
from . import VERSION


class Main(object):
    def __init__(self):
        self._args = self._parse_args()
        self._log = get_logger(debug=self._args.debug, verbose=self._args.verbose)
        self._log.debug(self._args)
        self._log.debug('Initialising...')

    @staticmethod
    def _parse_args():
        parser = argparse.ArgumentParser(description='Tool to send messages via Sendgrid/Slack', add_help=False)
        parser.add_argument('--version', action='version', version='%s %s' % ('ppmail', VERSION))
        parser.add_argument('--help', action='help', help='show this help message and exit')
        parser.add_argument('--debug', action='store_true', dest='debug', help='debugging mode')
        parser.add_argument('--verbose', action='store_true', dest='verbose', help='verbose logging mode')
        parser.add_argument('-S', '--slack', action='store_true', help='Use Slack instead of Sendgrid')
        parser.add_argument('-f', '--from', dest='sender',
                            help='sender')
        parser.add_argument('-t', '--to', dest='recipients', nargs='+', required=True,
                            help='recipient', default=[])
        parser.add_argument('-c', '--cc', dest='cc', nargs='+',
                            help='carbon copy recipient')
        parser.add_argument('-s', '--subject', dest='subject', default='', help='subject')
        parser.add_argument('-H', '--code', dest='code', action='store_true',
                            help='send HTML formatted email/code block')
        parser.add_argument('-F', '--font-size', dest='font_size', type=int, default=None,
                            help='font size in px for HTML formatted email (use with -H)')
        args = parser.parse_args()
        return args

    def run(self):
        self._log.debug('Starting...')

        sender = self._args.sender if self._args.sender else os.getenv('USER') + '@' + platform.node()
        self._log.debug('Sender: %s' % sender)

        message = ''
        non_empty = 0

        for line in sys.stdin:
            line = line
            message += line
            if line != '' and line != '\n':
                non_empty += 1

        if non_empty == 0:
            self._log.critical('Nothing to send')
            exit(1)

        if not self._args.slack and not self._args.subject:
            self._log.critical('Sendgrid requires subject field to be set (-s)')
            exit(1)

        mailer = Mailer(slack=self._args.slack)
        if self._args.slack:
            status = mailer.send(
                sender=sender,
                recipients=self._args.recipients,
                subject=self._args.subject,
                message=message,
                code=self._args.code,
                cc=self._args.cc
            )
        else:
            status = mailer.send(
                sender=sender,
                recipients=self._args.recipients,
                subject=self._args.subject,
                message=message,
                code=self._args.code,
                cc=self._args.cc,
                font_size=self._args.font_size
            )

        self._log.debug('Finishing...')

        if status:
            exit()
        else:
            exit(1)


def main():
    try:
        Main().run()
    except KeyboardInterrupt:
        print('\nTerminating...')
        exit(130)


if __name__ == '__main__':
    main()
