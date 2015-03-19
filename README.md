# Cryptoletter

This is a simple Python script to send an encrypted email to a list of recipients.
In case you need a moderately secure way to keep a number of people informed about
a project.

# Install

You need two dependencies:

    # pip install gnupg pysocks

Obviously if you need it, install Tor.

# Usage

You need to either modify or create a YAML config file. Each file contains the details
of the mail account and the recipients. You can make one config file for each "newsletter"
so to speak. Here's an example:

    tor: yes
    host: yourmailserver.com
    port: 587
    user: your@email.com
    pwd: yourpassword
    from: noreply@email.com
    recipients:
        - someone@youknow.com
        - someone.else@youknow.com

Then you need to create an email file:

    Subject: This is the email subject

    This is the email body, starts after a line break.

You can now send the emails like this:

    $ python cryptoletter.py --config news.yaml /tmp/email.txt

If no --config is specified, it will attempt to use `config.yaml` in the local folder.

