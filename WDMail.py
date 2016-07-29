#
# A class to send mail via sendgrid
#
# Author: Peter Pakos <peter.pakos@wandisco.com>

from __future__ import print_function
import sendgrid


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
