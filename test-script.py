import logging
from mail_logger import get_mail_logger
import time
import datetime
from pprint import pprint

def main():
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Enter Main()")
    logger = get_mail_logger(logging.getLogger('root'))


    #while True:
    start_time = datetime.datetime.now()
    #run_script()
    end_time = datetime.datetime.now()
    logger.info("Taskrotation script executed! Duration=" + str(end_time - start_time) + " ends at: " + str(end_time))
    renew_time = start_time + datetime.timedelta(weeks=1)
    renew_time = renew_time.replace(hour=12, minute=0, second=0, microsecond=0)
    #time.sleep((renew_time - start_time).total_seconds())


if __name__== "__main__":
    main()
