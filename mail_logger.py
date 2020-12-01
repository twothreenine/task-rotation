import os
import logging
from pprint import pprint
import smtplib
from logging.handlers import SMTPHandler
from email.message import EmailMessage
import email.utils
import email.mime.multipart
class CustomSMTPHandler(SMTPHandler):

    def emit(self, record):
        """
        Emit a record.
        """
        try:
            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            smtp = smtplib.SMTP(self.mailhost, port)
            msg = EmailMessage()
            msg['From'] = self.fromaddr
            msg['To'] = ','.join(self.toaddrs)
            msg['Subject'] = self.getSubject(record)
            msg['Date'] = email.utils.localtime()
            msg.set_content(self.format(record))
            if smtp.starttls()[0] == 220:
                smtp.login(self.username, self.password)
                smtp.send_message(msg, self.fromaddr, self.toaddrs)
                smtp.quit()
            else:
                raise ValueError('Server does not accept TLS')
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

def get_logger_config():
    server = os.environ['TR_LOG_MAIL_SERVER']  
    port = os.environ['TR_LOG_MAIL_PORT']  
    user = os.environ['TR_LOG_MAIL_USER']  
    password = os.environ['TR_LOG_MAIL_PASS']
    sender = os.environ['TR_LOG_MAIL_SENDER']
    subject_prefix = os.environ['TR_LOG_MAIL_SUBJECT_PREFIX']
    if (server == user == password == None):
        return None
    subscribors = os.environ['TR_LOG_MAIL_SUBSCRIBORS'].split(';')
    logger_mail_config = {'LOGGER_MAIL_SERVER': server, 'LOGGER_MAIL_PORT':port, 'LOGGER_MAIL_USER': user, 'LOGGER_MAIL_PASS': password, 'LOGGER_MAIL_SENDER': sender, 'LOGGER_MAIL_SUBJECT_PREFIX':subject_prefix, 'LOGGER_MAIL_SUBSCRIBORS':''}
    logger_mail_config['LOGGER_MAIL_SUBSCRIBORS'] = [{'mailadress':subscribor.split(':')[0], 'level':subscribor.split(':')[1]} for subscribor in subscribors]
    
    return logger_mail_config


def filter_log_level(subscribor_level, level):
    numeric_level = getattr(logging, subscribor_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    if numeric_level == level:
        return True
    else:
        return False    

def get_mail_handler(config, level):
    from logging.handlers import SMTPHandler

    credentials = (config['LOGGER_MAIL_USER'], config['LOGGER_MAIL_PASS'])
    pprint(credentials)
    secure = () #use TLS
    subscribors = [subscribor['mailadress'] for subscribor in config['LOGGER_MAIL_SUBSCRIBORS'] if filter_log_level(subscribor['level'], level)]
    if len(subscribors) > 0:
        mail_handler = CustomSMTPHandler(
            mailhost=(config['LOGGER_MAIL_SERVER'], int(config['LOGGER_MAIL_PORT'])),
            fromaddr=config['LOGGER_MAIL_SENDER'],
            toaddrs=subscribors,
            subject=str(config['LOGGER_MAIL_SUBJECT_PREFIX']) + ' Taskrotation-Log',
            credentials=credentials,
            secure=())#,timeout=10.0)
        mail_handler.setLevel(level)
        logging.debug('Add mail logger level: ' + str(level) + ', for: ' + str(*subscribors))
        return mail_handler
    else:
        return None

def get_mail_logger(logger):
    config = get_logger_config()
    logger.debug('Mail logger config: ' + str(config))
    if (config == None):
        logger.debug('No Mail logger config!')
        return

    config = get_logger_config()
    if (config == None):
        logger.debug('No Mail-Logger added')
        return

    mail_handler_info = get_mail_handler(config, logging.INFO)
    pprint(mail_handler_info)

    return mail_handler_info, get_mail_handler(config, logging.ERROR)
 #   logger.addHandler(get_mail_handler(config, logging.ERROR))
 #   logger.addHandler(mail_handler_info)
    
 #   return logger