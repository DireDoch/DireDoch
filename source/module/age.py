import datetime
from dateutil import relativedelta

from config import BIRTHDATE


def get_age() -> str:
    diff = relativedelta.relativedelta(datetime.datetime.today(), BIRTHDATE)
    years = f"{diff.years} year{'s' if diff.years != 1 else ''}"
    months = f"{diff.months} month{'s' if diff.months != 1 else ''}"
    days = f"{diff.days} day{'s' if diff.days != 1 else ''}"
    return f"{years}, {months}, {days}"
