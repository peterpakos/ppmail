# wdmail
A tool to send mail via Sendgrid

## Configuration
Sendgrid API key should be saved to WDMail.api file in the project's root directory.

~~~
$ tree
.
├── README.md    - README file
├── WDMail.api   - File containing Sendgrid API key
├── WDMail.py    - WDMail Python module
└── wdmail       - Python script using WDMail class to send mail

0 directories, 4 files
~~~

## Usage - wdmail tool

~~~
$ usage: wdmail [-h] [--version] [-f SENDER] -t RECIPIENTS [RECIPIENTS ...]
              [-c CC [CC ...]] -s SUBJECT [-H]

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
~~~

## Usage - WDMail Python module

~~~
import WDMail

wdmail = WDMail.WDMail()
response = mail.send('from@domain.com', ['to@domain.com'], 'subject', 'message', html=True, cc=['cc@domain.com'])

print(response)
~~~
