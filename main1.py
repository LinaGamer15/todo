from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

print(datetime.now().strftime('%Y %m %d, %H %M %S'))
date = datetime.now() + timedelta(days=1)
print(date.strftime('%Y %m %d, %H %M %S'))
date1 = datetime.now() + relativedelta(months=1)
print(date1.strftime('%Y %m %d, %H %M %S'))
print(datetime.now() < date1)