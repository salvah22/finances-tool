import datetime
from dateutil.relativedelta import relativedelta

def parse_period(older_date, newer_date) -> relativedelta:
    years = newer_date.year - older_date.year
    months = newer_date.month - older_date.month
    days = newer_date.day - older_date.day
    #print(years,months,days)
    if days < 0:
        months -= 1
        days += int(str(newer_date + relativedelta(months=1) - newer_date).split(' ')[0]) #days in month
    if months < 0:
        years -= 1
        months += 12
    return relativedelta(years=years, months=months, days=days)
