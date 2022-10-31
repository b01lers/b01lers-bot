# https://stackoverflow.com/a/28688724 - CC-BY-SA 3.0

from datetime import date

Y = 2000  # dummy leap year to allow input X-02-29 (leap day)
seasons = [('winter', (date(Y, 1, 1), date(Y, 3, 20))),
           ('spring', (date(Y, 3, 21), date(Y, 6, 20))),
           ('summer', (date(Y, 6, 21), date(Y, 9, 22))),
           ('fall', (date(Y, 9, 23), date(Y, 12, 20))),
           ('winter', (date(Y, 12, 21), date(Y, 12, 31)))]


def get_current_season() -> str:
    now = date.today().replace(year=Y)
    return next(season for season, (start, end) in seasons
                if start <= now <= end)
