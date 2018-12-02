# -*- coding: utf-8 -*-
"""Tool to send messages via Sendgrid/Slack

Author: Peter Pakos <peter.pakos@wandisco.com>

Copyright (C) 2018 WANdisco

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

from __future__ import print_function
from . import __version__
from .mailer import Mailer

import os
import sys
import argparse
import platform
from pplogger import get_logger

__app_name__ = os.path.splitext(__name__)[0].lower()

parser = argparse.ArgumentParser(description='Tool to send messages via Sendgrid/Slack', add_help=False)
parser.add_argument('--version', action='version', version='%s %s' % (__app_name__, __version__))
parser.add_argument('--help', action='help', help='show this help message and exit')
parser.add_argument('--debug', action='store_true', dest='debug', help='debugging mode')
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
# noinspection PyTypeChecker
parser.add_argument('-F', '--font-size', dest='font_size', type=int, default=None,
                    help='font size in px for HTML formatted email (use with -H)')
args = parser.parse_args()

log = get_logger(name='ppmail.mailer', debug=args.debug)


def main():
    log.debug(args)

    sender = args.sender if args.sender else os.getenv('USER') + '@' + platform.node()
    log.debug('Sender: %s' % sender)

    message = ''
    non_empty = 0

    for line in sys.stdin:
        line = line
        message += line
        if line != '' and line != '\n':
            non_empty += 1

    if non_empty == 0:
        log.critical('Nothing to send')
        exit(1)

    if not args.slack and not args.subject:
        log.critical('Sendgrid requires subject field to be set (-s)')
        exit(1)

    mailer = Mailer(slack=args.slack)
    if args.slack:
        status = mailer.send(
            sender=sender,
            recipients=args.recipients,
            subject=args.subject,
            message=message,
            code=args.code,
            cc=args.cc
        )
    else:
        status = mailer.send(
            sender=sender,
            recipients=args.recipients,
            subject=args.subject,
            message=message,
            code=args.code,
            cc=args.cc,
            font_size=args.font_size
        )

    if status:
        exit()
    else:
        exit(1)
