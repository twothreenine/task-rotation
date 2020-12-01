import os
from unittest import TestCase, mock
from mail_logger import get_logger_config, get_mail_handler, filter_log_level
import logging


class TestMailLogger(TestCase):
    expect = {'LOGGER_MAIL_SERVER': 'smtp:\\mailserver.net', 'LOGGER_MAIL_PORT':'8080', 'LOGGER_MAIL_USER': 'user', 'LOGGER_MAIL_PASS': 'secure_password', 'LOGGER_MAIL_SENDER': 'log@mailserver.net', 'LOGGER_MAIL_SUBJECT_PREFIX':'LOG: ', 'LOGGER_MAIL_SUBSCRIBORS': [{'mailadress':'subcribor1','level':'ERROR'},{'mailadress':'subcribor2','level':'INFO'},{'mailadress':'subcribor3','level':'ERROR'}]}
    @mock.patch.dict(os.environ, {'TR_LOG_MAIL_SERVER': expect['LOGGER_MAIL_SERVER']})
    @mock.patch.dict(os.environ, {'TR_LOG_MAIL_PORT': expect['LOGGER_MAIL_PORT']})
    @mock.patch.dict(os.environ, {'TR_LOG_MAIL_USER': expect['LOGGER_MAIL_USER']})
    @mock.patch.dict(os.environ, {'TR_LOG_MAIL_PASS': expect['LOGGER_MAIL_PASS']})
    @mock.patch.dict(os.environ, {'TR_LOG_MAIL_SENDER': expect['LOGGER_MAIL_SENDER']})
    @mock.patch.dict(os.environ, {'TR_LOG_MAIL_SUBJECT_PREFIX': expect['LOGGER_MAIL_SUBJECT_PREFIX']})
    @mock.patch.dict(os.environ, {'TR_LOG_MAIL_SUBSCRIBORS': 'subcribor1:ERROR;subcribor2:INFO;subcribor3:ERROR'})
    
    def test_get_logger_config(self):
        config = get_logger_config()
        self.assertDictEqual(self.expect, config)
    
    def test_get_mail_handler(self):
        mail_handler = get_mail_handler(self.expect, logging.INFO)
        self.assertEqual(getattr(mail_handler, 'secure', None), ())
        self.assertEqual(getattr(mail_handler, 'mailhost', None),'smtp:\\mailserver.net')
        self.assertEqual(getattr(mail_handler, 'fromaddr', None), 'log@mailserver.net')
        self.assertEqual(getattr(mail_handler, 'toaddrs', None),['subcribor2'])
        self.assertEqual(getattr(mail_handler, 'subject', None),'LOG:  Taskrotation-Log')

    def test_filter_log_level_error(self):
        self.assertTrue(filter_log_level('error', logging.ERROR))

    def test_filter_log_level_info(self):
        self.assertFalse(filter_log_level('ERROR', logging.INFO))


if __name__ == '__main__':
    unittest.main()