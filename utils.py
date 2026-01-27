from typing import Any
import babel.dates as bbld
import pandas as pd
import datetime as dt
import re

def strip_locale_formatting(number:Any) -> float:
  num_str = str(number).strip()
  if pd.isna(number) or number is None or len(num_str) == 0:
    return 0.0
  elif num_str == '-':
    return 0.0
  elif num_str.startswith('INR'):
    return strip_locale_formatting(num_str.lstrip('INR'))
  else:
    return float(str(number).replace(',', ''))
  
CLRD_TO_POSIX = {
  'yyyy': '%Y',
  'yy': '%Y',
  'MMMM': '%B',
  'MMM': '%b',
  'MM': '%m',
  'M': '%m',
  'dd': '%d',
  'd': '%d'
}

def parse_date(received:Any, format:str) -> dt.date:
  if pd.isna(received):
    return received
  date_str = str(received)
  if not any(delim in format for delim in [',','.','/',':']):
    clrd_tokens = sorted(CLRD_TO_POSIX.keys(), key=len, reverse=True)
    pattern = '|'.join(map(re.escape, clrd_tokens))
    posix_format = re.sub(pattern, lambda m: CLRD_TO_POSIX[m.group()], format)
    return dt.datetime.strptime(date_str, posix_format).date()
  else:
    return bbld.parse_date(date_str, format=format)