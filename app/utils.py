from typing import Any
import babel.dates as bbld
import pandas as pd
import datetime as dt
import re
from typing import cast
import pandas as pd
from statsmodels.regression.linear_model import RegressionResults
import statsmodels.formula.api as smf
from dataclasses import dataclass

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
  
def seek_target_headers(df:pd.DataFrame, target_headers:list[str]) -> pd.DataFrame | None:
  if all(col in df.columns for col in target_headers):
    return df
  normalized_tgt_hdrs = [h.strip().lower() for h in target_headers]
  ndf = df.reset_index(drop=True)
  start_row:int | None = None
  for i, row in ndf.iterrows():
    row_normalized = [str(cell).strip().lower() for cell in row]
    if all(header in row_normalized for header in normalized_tgt_hdrs):
      start_row = cast(int, i)
  if start_row is None:
    return None
  ndf = ndf.iloc[start_row:].reset_index(drop=True).T.drop_duplicates().T
  ndf.columns = ndf.iloc[0]
  ndf = ndf[1:][target_headers].reset_index(drop=True)
  return ndf

@dataclass
class LinearPrediction:
  x: list[Any]
  y: list[float]
  r_squared: float
  formula:str

def generate_linear_model(x:list[Any], y:list[float], extend:int) -> LinearPrediction:
  data = {'x': range(len(x)), 'y': y}
  model = smf.ols(formula='y ~ x', data=data)
  fitted = cast(RegressionResults, model.fit())
  params:pd.Series = fitted.params

  intercept = params.iloc[0]
  slope = params.iloc[1]

  pred_x = list(x)
  pred_x.extend([f'ext-{i+1}' for i in range(extend)])
  pred_y = [round(x * slope + intercept, 2) for x in range(len(pred_x))]

  return LinearPrediction(
    x=pred_x,
    y=pred_y,
    r_squared=round(fitted.rsquared, 6),
    formula=f'X*{round(slope, 2)} + {round(intercept, 2)}'
  )