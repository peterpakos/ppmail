# -*- coding: utf-8 -*-
"""This module implements sending mail via Sendgrid/Slack

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

from __future__ import print_function
import os
import logging
from slackclient import SlackClient
import sendgrid
import cgi
from python_http_client import exceptions

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


class Mailer(object):
    def __init__(self, slack=False):
        self._log = logging.getLogger()
        self._log.debug('Preparing provider (%s)' % ('Slack' if slack else 'Sendgrid'))
        self._slack = slack
        self._email_domain = None
        self._sendgrid_key = None
        self._slack_key = None
        self._config_dir = os.path.expanduser(os.environ.get('XDG_CONFIG_HOME', '~/.config'))
        self._config_file = os.path.splitext(__name__)[0].lower()
        self._config_path = os.path.join(
            self._config_dir,
            self._config_file
        )
        self._load_config()

        if (slack and not self._email_domain) or (slack and not self._slack_key) \
                or (not slack and not self._sendgrid_key):
            self._log.critical('Please edit config file %s' % self._config_path)
            exit(1)

        if slack:
            self._slack_client = SlackClient(self._slack_key)
        else:
            os.environ['SENDGRID_API_KEY'] = self._sendgrid_key
            self._sendgrid_client = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))

    def _load_config(self):
        config = configparser.ConfigParser()

        if not os.path.exists(self._config_dir):
            self._log.debug('Config directory %s does not exist, creating' % self._config_dir)
            os.makedirs(self._config_dir)

        if not os.path.isfile(self._config_path):
            self._log.debug('Config file not found at %s' % self._config_path)
            config.add_section('PPMAIL')
            config.set('PPMAIL', 'EMAIL_DOMAIN', 'changeme')
            config.set('PPMAIL', 'SENDGRID_KEY', 'changeme')
            config.set('PPMAIL', 'SLACK_KEY', 'changeme')

            with open(self._config_path, 'w') as cfgfile:
                config.write(cfgfile)
            self._log.info('Initial config saved to %s - PLEASE EDIT IT!' % self._config_path)
            return

        self._log.debug('Loading configuration file %s' % self._config_path)

        if 'changeme' in open(self._config_path).read():
            self._log.debug('Initial config found in %s - PLEASE EDIT IT!' % self._config_path)
            return

        config.read(self._config_path)

        if not config.has_section('PPMAIL'):
            self._log.debug('Config file has no PPMAIL section')
            return

        if config.has_option('PPMAIL', 'EMAIL_DOMAIN'):
            self._email_domain = config.get('PPMAIL', 'EMAIL_DOMAIN')
            self._log.debug('EMAIL_DOMAIN = %s' % self._email_domain)
        else:
            self._log.debug('PPMAIL.EMAIL_DOMAIN not set')

        if config.has_option('PPMAIL', 'SENDGRID_KEY'):
            self._sendgrid_key = config.get('PPMAIL', 'SENDGRID_KEY')
            self._log.debug('SENDGRID_KEY = ********')
        else:
            self._log.debug('PPMAIL.SENDGRID_KEY not set')

        if config.has_option('PPMAIL', 'SLACK_KEY'):
            self._slack_key = config.get('PPMAIL', 'SLACK_KEY')
            self._log.debug('SLACK_KEY = ********')
        else:
            self._log.debug('PPMAIL.SLACK_KEY not set')

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

                    if i == (len(text) - 1) or (length + len(text[i+1])) > 4030:
                        to_print = ''.join(to_print)
                        if not str(to_print).startswith('```') and subject and subject not in to_print:
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
