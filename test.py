''' Tests for cron and dates '''
import datetime 
TEST_DELTA=datetime.timedelta(days=0)  

def utcnow():
    return datetime.datetime.utcnow()+TEST_DELTA