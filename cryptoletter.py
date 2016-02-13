#!/usr/bin/env python
# This file is part of Cryptoletter - https://github.com/botherder/cryptoletter
# See the file 'LICENSE' for copying permission.

import os
import sys
import yaml
import gnupg
import socks
import getpass
import smtplib
import datetime
import argparse
from email.mime.text import MIMEText

# This will contain the parsed YAML config.
CFG = None

class Email(object):

    def __init__(self, recipient, subject, body):
        self.gpg = gnupg.GPG(homedir='~/.gnupg')
        self.smtp = None
        self.recipient = recipient
        self.subject = subject
        self.body = body

    def connect(self):
        # Unless it's disabled in the config, let's proxy the SMTP connections
        # through Tor.
        if CFG['tor']:
            socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', 9050, True)
            socks.wrapmodule(smtplib)

        # Connecto the mail server.
        self.smtp = smtplib.SMTP(CFG['host'], CFG['port'])
        # Initiate TLS connection.
        self.smtp.starttls()
        # Authenticate.
        self.smtp.login(CFG['user'], CFG['pwd'])

    def find_keyid(self):
        # We need the keyid to encrypt the message to the recipient.
        # Let's walk through all keys in the keyring and find the
        # appropriate one.
        keys = self.gpg.list_keys()
        for key in keys:
            for uid in key['uids']:
                if self.recipient in uid:
                    return key['keyid']

        return None

    def send(self):
        # Look for the key.
        keyid = self.find_keyid()
        # If there is no key, we abort sending the message as we don't want
        # to have the newsletter going out unencrypted.
        if not keyid:
            print("ERROR: Haven't found a key for {0}".format(self.recipient))
            return

        # Encrypt the message body.
        encrypted_data = self.gpg.encrypt(self.body, keyid)
        encrypted_body = str(encrypted_data)

        # Setup MIME message.
        msg = MIMEText(encrypted_body)
        msg['Subject'] = self.subject
        msg['From'] =  CFG['from']
        msg['To'] = self.recipient
        msg['Date'] = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')

        # Connect to the SMTP server.
        self.connect()
        # Send the email.
        self.smtp.sendmail(CFG['from'], [self.recipient], msg.as_string())

class Scheduler(object):

    def run(self, email_path):
        # Check if the mail file exists.
        if not os.path.exists(email_path):
            print("ERROR: the email file does not exist")
            return

        with open(email_path, 'r') as handle:
            data = handle.read()

        # Get headers and message body.
        headers_raw, body = data.split("\n\n", 1)
        # The header should mostly just contain the subject for now.
        # Example:
        #
        # Subject: This is the email subject
        #
        # This is the email body.
        headers = yaml.load(headers_raw)

        # We send an encrypted email for each recipient specified in the
        # configuration file.
        for recipient in CFG['recipients']:
            print("Sending to " + recipient)
            eml = Email(recipient, headers['Subject'], body)
            eml.send()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('mail', metavar='MAIL', help="Specify the file containing the mail subject and body")
    parser.add_argument('-c', '--config', action='store', default='config.yaml', help="Specify which config you want to use (default: config.yaml)")
    args = parser.parse_args()

    # Select configuration file.
    # This could be one for each "newsletter" you need to maintain.
    if args.config:
        arg_cfg = args.config
    else:
        arg_cfg = 'config.yaml'

    # Check if the config file exists or not.
    if not os.path.exists(arg_cfg):
        print("ERROR: The specified config file does not exist")
        sys.exit(-1)

    # Load the configuration from the specified file.
    with open(arg_cfg, 'r') as handle:
        CFG = yaml.load(handle.read())

    # Input password.
    CFG['pwd'] = getpass.getpass("Please insert the password for {}: " .format(CFG['user']))

    # Launch the scheduler.
    s = Scheduler()
    s.run(args.mail)
