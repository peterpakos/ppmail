# -*- coding: utf-8 -*-
"""This module implements sending mail via Sendgrid/Slack

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
from ppconfig import Config

import os
import logging
from slackclient import SlackClient
import sendgrid
import cgi
from python_http_client import exceptions


class Mailer(object):
    def __init__(self, slack=False):
        self._app_name = os.path.splitext(__name__)[0].lower()
        self._log = logging.getLogger(__name__)

        try:
            self._config = Config(self._app_name)
        except IOError as e:
            self._log.critical(e)
            exit(1)

        try:
            self._email_domain = self._config.get('email_domain')
            self._sendgrid_key = self._config.get('sendgrid_key')
            self._slack_key = self._config.get('slack_key')
        except NameError as e:
            self._log.critical(e)
            exit(1)

        self._log.debug('Preparing provider (%s)' % ('Slack' if slack else 'Sendgrid'))
        self._slack = slack

        if slack:
            self._slack_client = SlackClient(self._slack_key)
        else:
            os.environ['SENDGRID_API_KEY'] = self._sendgrid_key
            self._sendgrid_client = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))

    def send(self, *args, **kwargs):
        if self._slack:
            r = self._send_slack(*args, **kwargs)
        else:
            r = self._send_mail(*args, **kwargs)
        return r

    def _send_slack(self, sender, recipients, subject, message, code=False, cc=None):
        if type(recipients) is not list:
            recipientsl = []
            if recipients is not None:
                recipientsl.append(recipients)
            recipients = recipientsl

        if type(cc) is not list:
            ccl = []
            if cc is not None:
                ccl.append(cc)
            cc = recipients + ccl

        for c in cc:
            if c not in recipients:
                recipients.append(c)

        if subject:
            subject = '*%s*\n' % subject.strip()

        if code:
            message = "```%s```" % message

        text = '%s%s' % (subject, message)

        if code:
            text = text.splitlines(True)

        failed = 0

        for recipient in recipients:
            recipient_id = None

            if '@%s' % self._email_domain in recipient:
                r = self._slack_client.api_call('users.lookupByEmail', email=recipient)
                if r.get('ok'):
                    recipient_id = r.get('user').get('id')
            elif str(recipient).startswith('@'):
                r = self._slack_client.api_call('users.lookupByEmail',
                                                email=str(recipient).strip('@') + '@%s' % self._email_domain)
                if r.get('ok'):
                    recipient_id = r.get('user').get('id')
            else:
                if str(recipient).startswith('#'):
                    recipient = str(recipient).lstrip('#')
                recipient_id = self._find_channel_id(recipient)

            if not recipient_id:
                failed += 1
                self._log.error('Recipient %s not found' % recipient)
                continue

            if code:
                to_print = []
                length = 0

                for i, line in enumerate(text):
                    to_print += text[i]
                    length += len(line)

                    if i == (len(text) - 1) or (length + len(text[i+1])) > 3800:
                        to_print = ''.join(to_print)

                        if not str(to_print).startswith('```') and not (subject and subject in to_print):
                            to_print = '```' + to_print
                        if not str(to_print).endswith('```'):
                            to_print = to_print + '```'

                        r = self._slack_client.api_call(
                            'chat.postMessage',
                            username=sender,
                            channel=recipient_id,
                            text=to_print,
                            as_user=False,
                            link_names=True
                        )

                        if not r.get('ok'):
                            failed += 1

                        to_print = []
                        length = 0
            else:
                r = self._slack_client.api_call(
                    'chat.postMessage',
                    username=sender,
                    channel=recipient_id,
                    text=text,
                    as_user=False,
                    link_names=True
                )

                if not r.get('ok'):
                    failed += 1

        if failed:
            return False
        else:
            return True

    def _find_channel_id(self, channel):
        r = self._slack_client.api_call('channels.list')
        channels = r.get('channels')
        for c in channels:
            if c.get('name') == channel:
                channel_id = c.get('id')
                self._log.debug('Public channel name: %s, ID: %s' % (c.get('name'), c.get('id')))
                return channel_id

        r = self._slack_client.api_call('groups.list')
        private_channels = r.get('groups')
        for c in private_channels:
            if c.get('name') == channel:
                channel_id = c.get('id')
                self._log.debug('Private channel name: %s, ID: %s' % (c.get('name'), c.get('id')))
                return channel_id

        return False

    def _send_mail(self, sender, recipients, subject, message, code=False, cc=None, font_size=None):
        if code:
            message = cgi.escape(message)

        if font_size:
            style = ' style="font-size:%spx"' % font_size
        else:
            style = ''

        if type(recipients) is not list:
            recipientsl = []
            if recipients is not None:
                recipientsl.append(recipients)
            recipients = recipientsl

        if type(cc) is not list:
            ccl = []
            if cc is not None:
                ccl.append(cc)
            cc = ccl

        recipients = ['%s@%s' % (e, self._email_domain) if '@' not in e else e for e in recipients]
        cc = ['%s@%s' % (e, self._email_domain) if '@' not in e else e for e in cc]

        content = ''
        content_type = 'text/plain'
        if code:
            content_type = 'text/html'
            content += '''
<html>
<body%s>
<pre>
''' % style
        content += message

        if code:
            content += '''
</pre>
</body>
</html>
'''
        recipient_list = []
        for recipient in recipients:
            if recipient in cc:
                cc.remove(recipient)
            recipient_list.append({"email": recipient})
        data = {
            'personalizations': [
                {
                    'to': recipient_list,
                    'subject': subject
                }
            ],
            'from': {
                'email': sender
            },
            'content': [
                {
                    'type': content_type,
                    'value': content
                }
            ]
        }
        if len(cc) > 0:
            cc_list = []
            for c in cc:
                cc_list.append({'email': c})
            data['personalizations'][0]['cc'] = cc_list

        try:
            response = self._sendgrid_client.client.mail.send.post(request_body=data)
        except exceptions.BadRequestsError as e:
            self._log.critical(e.body)
            exit(1)
        else:
            if response.status_code < 300:
                return True
            else:
                return False
