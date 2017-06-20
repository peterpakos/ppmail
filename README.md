# wdmail
A tool to send mail via Sendgrid

## Configuration
Sendgrid API key should be saved to WDMail.api file in the project's root directory.

## Usage - wdmail tool
~~~
$ ./wdmail -h
usage: wdmail [-h] [--version] [-f SENDER] -t RECIPIENTS [RECIPIENTS ...]
              [-c CC [CC ...]] -s SUBJECT [-H] [-F FONT_SIZE]

A tool to send mail via sendgrid

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -f SENDER, --from SENDER
                        email From: field
  -t RECIPIENTS [RECIPIENTS ...], --to RECIPIENTS [RECIPIENTS ...]
                        email To: field
  -c CC [CC ...], --cc CC [CC ...]
                        email Cc: field
  -s SUBJECT, --subject SUBJECT
                        email Subject: field
  -H, --html            send HTML formatted email
  -F FONT_SIZE, --font-size FONT_SIZE
                        font size in px for HTML formatted email (use with -H)
~~~

## Usage - WDMail Python module
~~~
import WDMail

wdmail = WDMail.WDMail()
response = mail.send(
    sender='from@domain.com',
    recipients=['to@domain.com'],
    subject='subject',
    message='message',
    html=True,
    cc=['cc@domain.com'],
    font_size=10
)

print(response)
~~~
