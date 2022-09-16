# encoding: utf-8
import logging
import smtplib
from email.mime.text import MIMEText
import email.utils
from datetime import datetime

_logger = logging.getLogger('utils.mailclient')
class MailClient(object):
  def __init__(self, host, port, user, pwd=''):
    self._host = host
    self._port = port
    self._user = user
    self._pwd = pwd
    self._smtp_server = None
    self._debug = False
    self._keepalive = True
  def set_keepalive(self, keepalive):
    self._keepalive = keepalive
  def set_debug(self, debug):
    self._debug = debug
    if self._smtp_server is not None:
      self._smtp_server.set_debuglevel(self._debug)
  def _connect(self):
    if self._smtp_server is None:
      _smtp_server = smtplib.SMTP(self._host, self._port)
      _smtp_server.ehlo()
      _smtp_server.starttls()
      _smtp_server.set_debuglevel(self._debug)
      if self._pwd:
        _smtp_server.login(self._user, self._pwd)
      self._smtp_server = _smtp_server
    return self._smtp_server
  def _dispose(self):
    if self._smtp_server is not None:
      self._smtp_server.quit()
      self._smtp_server = None
  def send(self, to_addrs, subject, content, isdispose=True):
    _smtp_server = self._connect()
    if not isinstance(to_addrs, list):
      to_addrs = [to_addrs]
    _msg = MIMEText(content, 'html', 'utf-8')
    _msg['Subject'] = subject
    _msg['From'] = self._user
    _msg['To'] = '; '.join(to_addrs)
    _msg['Date'] = datetime.now().strftime('%Y-%d-%m %H:%M:%S')
    _smtp_server.sendmail(self._user, to_addrs, _msg.as_string())
    isdispose and (not self._keepalive) and self._dispose()
  def send_mails(self, mails):
    _smtp_server = self._connect()
    for mail in mails:
      self._send_mail(mail.get('to'), mail.get('subject'), mail.get('content'), False)
    (not self._keepalive) and self._dispose()
  def close(self):
    self._dispose()
