# ppmail
Tool to send messages via Sendgrid/Slack

PyPI package: [ppmail](https://pypi.python.org/pypi/ppmail)

If you spot any problems or have any improvement ideas then feel free to open
an issue and I will be glad to look into it for you.

## Installation
A recommended way of installing the tool is pip install.

Once installed, a command line tool `ppmail` should be available in your
system's PATH.

### pip install
The tool is available in PyPI and can be installed using pip:
```
$ pip install --user ppmail
$ ppmail --help
```

## Configuration
By default, the tool reads its configuration from `~/.config/ppmail` file (the
location can be overridden by setting environment variable `XDG_CONFIG_HOME`).
If the config file (or directory) does not exist then it will be automatically
created and populated with sample config upon the next run.

## Usage - Help
```
$ ppmail --help
usage: __main__.py [--version] [--help] [--debug] [--verbose] [-S] [-f SENDER]
                   -t RECIPIENTS [RECIPIENTS ...] [-c CC [CC ...]]
                   [-s SUBJECT] [-H] [-F FONT_SIZE]

Tool to send messages via Sendgrid/Slack

optional arguments:
  --version             show program's version number and exit
  --help                show this help message and exit
  --debug               debugging mode
  --verbose             verbose logging mode
  -S, --slack           Use Slack instead of Sendgrid
  -f SENDER, --from SENDER
                        sender
  -t RECIPIENTS [RECIPIENTS ...], --to RECIPIENTS [RECIPIENTS ...]
                        recipient
  -c CC [CC ...], --cc CC [CC ...]
                        carbon copy recipient
  -s SUBJECT, --subject SUBJECT
                        subject
  -H, --code            send HTML formatted email/code block
  -F FONT_SIZE, --font-size FONT_SIZE
                        font size in px for HTML formatted email (use with -H)
```

## Usage - CLI
```
$ echo 'The king is dead, long live the king!' \
  | ppmail -SHf 'Jon Snow' \
  -t 'arya.stark@winterfell.com' \
  -c 'sansa.stark@winterfell.com' \
  -s 'Re: secret message'
```

## Usage - Python module
```
from ppmail import Mailer

mailer = Mailer(slack=True)

status = mailer.send(
    sender='Jon Snow',
    recipients=['arya.stark@winterfell.com'],
    cc=['sansa.stark@winterfell.com'],
    subject='Re: secret message',
    message='The king is dead, long live the king!',
    code=True
)
```
