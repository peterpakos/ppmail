#!/usr/bin/env python
#
# A tool to send mail via sendgrid
#
# Author: Peter Pakos <peter.pakos@wandisco.com>

from __future__ import print_function

import argparse
import json
import os
import platform
import sys

import sendgrid


class Main(object):
    _version = '16.7.29'
    _name = os.path.basename(sys.argv[0])

    def __init__(self):
        args = self._parse_args()
        print(args)

        self._cwd = os.path.dirname(os.path.abspath(sys.argv[0]))
        self._api_file = self._cwd + '/wdmailer.api'
        self._api_key = None

        if os.path.isfile(self._api_file):
            f = open(self._api_file)
            self._api_key = f.readline().strip()
        if self._api_key is None:
            print('API key not found in file %s' % self._api_file)
            exit(1)

        if args.sender:
            sender = args.sender
        else:
            sender = os.getenv('USER') + '@' + platform.node()
        message = ''
        for line in sys.stdin:
            message += line

        email = WDMail(api_key=self._api_key)
        status = email.send(sender, args.recipients, args.subject, message, args.html, args.cc)
        exit()
        if status < 300:
            exit()
        else:
            print('\nError: %s' % msg['errors'][0])
            exit(status)

    def _parse_args(self):
        parser = argparse.ArgumentParser(description='A tool to send mail via sendgrid')
        parser.add_argument('--version', action='version', version='%s %s' % (self._name, self._version))
        parser.add_argument('-f', '--from', dest='sender',
                            help='email From: field')
        parser.add_argument('-t', '--to', dest='recipients', nargs='+', required=True,
                            help='email To: field')
        parser.add_argument('-c', '--cc', dest='cc', nargs='+',
                            help='email Cc: field')
        parser.add_argument('-s', '--subject', dest='subject', required=True,
                            help='email Subject: field')
        parser.add_argument('-H', '--html', dest='html', action='store_true',
                            help='send HTML formatted email')
        args = parser.parse_args()
        return args

    def _display_version(self):
        print('%s %s' % (self._name, self._version))


class WDMail(object):
    def __init__(self, api_key):
        self._sg = sendgrid.SendGridAPIClient(apikey=api_key)

    def send(self, sender, recipients, subject, message, html=False, cc=None):
        content = ''
        if html:
            content += '''
<html>
<body>
<pre>
'''
        content += message

        if html:
            content += '''
</pre>
</body>
</html>
'''
        recipient_list = []
        for recipient in recipients:
            recipient_list.append({"email": recipient})
        data = {
            "personalizations": [
                {
                    "to": recipient_list,
                    "subject": subject
                }
            ],
            "from": {
                "email": sender
            },
            "content": [
                {
                    "type": "text/plain",
                    "value": content
                }
            ]
        }
#        if cc:
#            mail.add_cc(cc)
#        if html:
#            mail.set_html(body)
#        else:
#            mail.set_text(body)
        response = self._sg.client.mail.send.post(request_body=data)
        print(response.status_code)
        print(response.body)
        print(response.headers)
        return response.status_code

if __name__ == '__main__':
    try:
        main = Main()
    except KeyboardInterrupt:
        print('\nCancelling...')
