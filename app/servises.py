import email
import email.mime.application
import logging
import imaplib
import smtplib
from email.mime.multipart import MIMEMultipart

from django.conf import settings

logger = logging.getLogger(__name__)


class EmailService(object):
    def __init__(self, username=None, password=None):
        self.s = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        self.s.starttls()
        if not username:
            username = settings.EMAIL_HOST_USER
        if not password:
            password = settings.EMAIL_HOST_PASSWORD
        self.s.login(username, password)

    # html_msg = render_to_string('email/admin_inventory_alert.html', {"inventory": inventory})

    def send_email(self, receiver, subject, html_msg, files=list(), filename=None, quite_needed=True):

        msg = MIMEMultipart()
        msg['Subject'] = email.header.Header(subject, 'utf-8')
        msg['From'] = settings.EMAIL_HOST_USER
        msg['To'] = receiver

        body = email.mime.text.MIMEText(html_msg.encode('utf-8'), 'html', 'utf-8')
        msg.attach(body)

        for file in files:
            att = email.mime.application.MIMEApplication(file, _subtype="csv")
            att.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(att)

        self.s.sendmail(settings.EMAIL_HOST_USER, [msg['To']], msg.as_string())

        if quite_needed:
            self.quite()

    def quite(self):
        self.s.quit()
