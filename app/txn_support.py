import pandas as pd
import sqlite3
from dataclasses import dataclass
import datetime as dt
from pandas import DataFrame as DF
from dataclasses import replace
import app.stmt_reader_support as srs
from dateutil.relativedelta import relativedelta
from typing import Any
import json
from typing import TypeVar
import numpy as np

@dataclass
class BankTransaction:
  date: dt.date
  day_seq: int
  description: str
  withdrawn: float
  deposited: float
  net_amount: float
  balance: float
  account_number: str
  category: str | None = None
  
@dataclass
class MonthlyAccountStats:
  year_month:str
  account_number:str
  cashflow:float
  month_end_balance:float
  
  @staticmethod
  def dataframe_from_list(stats:list['MonthlyAccountStats']) -> pd.DataFrame:
    return pd.DataFrame.from_records([s.to_dict() for s in stats])

  @staticmethod
  def list_from_dataframe(df:pd.DataFrame) -> list['MonthlyAccountStats']:
    return [MonthlyAccountStats.from_dict(item) for item in df.to_dict(orient='records')]
  
  @staticmethod
  def from_dict(map:dict[str, Any]) -> 'MonthlyAccountStats':
    return MonthlyAccountStats(
      year_month=map['year_month'],
      account_number=map['account_number'],
      cashflow=map['cashflow'],
      month_end_balance=map['month_end_balance']
    )
  
  def to_dict(self) -> dict[str, Any]:
    return {
      'year_month': self.year_month,
      'account_number': self.account_number,
      'cashflow': self.cashflow,
      'month_end_balance': self.month_end_balance
    }

@dataclass
class PivotRow:
  name:str
  data:list[Any]
  
  def to_dict(self) -> dict[str, Any]:
    return {'name': self.name, 'data': self.data}
  
  @staticmethod
  def from_dict(map:dict[str, Any]) -> 'PivotRow':
    return PivotRow(name=map['name'], data=map['data'])

def get_col_vals(df:pd.DataFrame, col:str) -> list[Any]:
  return [(None if np.isnan(val) else val) for val in df[col].tolist()]
    
@dataclass
class PivotTable:
  labels:list[str]
  series:list[PivotRow]
  
  @staticmethod
  def from_dataframe(pivot:pd.DataFrame, index_col:str) -> 'PivotTable':
    df = pivot.apply(pd.to_numeric, errors='coerce').reset_index()
    return PivotTable(
      labels = df[index_col].astype(str).tolist(),
      series = [PivotRow(col, get_col_vals(df, col)) for col in df.columns if col != index_col]
    )
  
  @staticmethod
  def from_dict(map:dict[str, Any]) -> 'PivotTable':
    return PivotTable(
      labels=map['labels'],
      series=[PivotRow.from_dict(s) for s in map['series']]
    )
    
  def to_dataframe(self, index_col:str) -> pd.DataFrame:
    data = {index_col: self.labels}
    for s in self.series:
      data[s.name] = s.data
    df = pd.DataFrame(data)
    df = df.set_index(index_col)
    return df
    
  def to_dict(self) -> dict[str, Any]:
    return {'labels': self.labels, 'series': [row.to_dict() for row in self.series]}
  
@dataclass
class OverallBalance:  
  year_month:str
  month_end_balance:float
  
  @staticmethod
  def from_dict(map:dict[str, Any]) -> 'OverallBalance':
    return OverallBalance(year_month=map['year_month'], month_end_balance=map['month_end_balance'])
  
  def to_dict(self) -> dict[str, Any]:
    return {'year_month': self.year_month, 'month_end_balance': self.month_end_balance}
  
@dataclass
class OverallCashflow:
  year_month:str
  cashflow:float
  rolling_avg:float|None
  
  @staticmethod
  def from_dict(map:dict[str, Any]) -> 'OverallCashflow':
    return OverallCashflow(
      year_month=map['year_month'],
      cashflow=map['cashflow'],
      rolling_avg=map.get('rolling_avg')
    )
  
  def to_dict(self) -> dict[str, Any]:
    return {
      'year_month': self.year_month,
      'cashflow': self.cashflow,
      'rolling_avg': self.rolling_avg
    }
  
def max_day_seq(tr:BankTransaction, conn:sqlite3.Connection) -> int | None:
  cursor = conn.cursor()
  res = cursor.execute(
    "SELECT max(day_seq) FROM transaction_history WHERE tr_date = ? AND account_number = ?", 
    (tr.date, tr.account_number))
  max_day_seq, = res.fetchone()
  return max_day_seq
  
def insert_transaction(tr:BankTransaction, conn:sqlite3.Connection) -> bool:
  try:
    if not transaction_exists(tr, conn):
      mds = max_day_seq(tr, conn)
      if mds is not None:
        tr = replace(tr, day_seq=mds + 1)
      insert_new_transaction(tr, conn)
      return True
    else:
      return False
  except Exception as e:
    conn.rollback()
    raise e

def insert_new_transaction(tr:BankTransaction, conn:sqlite3.Connection):
  cursor = conn.cursor()
  cursor.execute("""
    INSERT INTO transaction_history(
      tr_date,day_seq,tr_description,category,withdrawn,deposited,balance,net_amount,account_number
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
    (tr.date, tr.day_seq, tr.description, tr.category, 
     tr.withdrawn, tr.deposited, tr.balance, tr.net_amount, tr.account_number))
  conn.commit()

def transaction_exists(tr:BankTransaction, conn:sqlite3.Connection) -> bool:
  cursor = conn.cursor()
  res = cursor.execute(
    "SELECT count(*) FROM transaction_history WHERE tr_date = ? AND tr_description = ? AND account_number = ?", 
    (tr.date, tr.description, tr.account_number))
  count, = res.fetchone()
  return count > 0

def acct_disp_name(account_number:str, conn:sqlite3.Connection) -> str:
  cursor = conn.cursor()
  res = cursor.execute("SELECT display_name FROM accounts WHERE account_number = ?", (account_number,))
  disp_name, = res.fetchone()
  return disp_name

def transaction_date_range(conn:sqlite3.Connection) -> tuple[dt.date, dt.date]:
  cur = conn.cursor()
  res = cur.execute("select distinct min(t.tr_date), max(t.tr_date) from transaction_history t")
  min_date_str, max_date_str, = res.fetchone()
  return (srs.parse_date(min_date_str, 'yyyy-MM-dd'), srs.parse_date(max_date_str, 'yyyy-MM-dd'))

def year_months_in_range(min_date:dt.date, max_date:dt.date) -> list[str]:
  min_mo_dt = dt.date(min_date.year, min_date.month, 1)
  max_mo_dt = dt.date(max_date.year, max_date.month, 1)
  curr_dt = min_mo_dt
  year_months = []
  while curr_dt <= max_mo_dt:
    year_months.append(dt.date.strftime(curr_dt, '%Y-%m'))
    curr_dt = curr_dt + relativedelta(months=1)
  return year_months

def prep_monthly_stats_from_txn_history(conn:sqlite3.Connection) -> DF:
  cursor = conn.cursor()
  res = cursor.execute("""
    with sp as (SELECT 
                strftime('%Y-%m', t.tr_date) as year_month, 
                account_number,
                sum(t.net_amount) as cashflow
                from transaction_history t
                GROUP BY strftime('%Y-%m', t.tr_date), account_number),
        bal as (SELECT strftime('%Y-%m', tin.tr_date) as year_month, 
                       tin.account_number,
                       tin.balance as month_end_balance
                FROM (SELECT 
                      row_number() OVER (PARTITION BY strftime('%Y-%m', t.tr_date), account_number 
                                         ORDER BY t.tr_date DESC, t.day_seq DESC) TR_SEQ,
                      t.*
                      FROM transaction_history t
                      ORDER BY t.tr_date DESC) tin
                WHERE tr_seq = 1)
    SELECT sp.year_month, 
           sp.account_number, 
           ac.display_name as acct_disp_name, 
           sp.cashflow, 
           bal.month_end_balance
    FROM sp, bal, accounts ac
    WHERE sp.year_month = bal.year_month
    AND sp.account_number = bal.account_number
    AND sp.account_number = ac.account_number
    ORDER BY sp.year_month DESC
    """)
  columns = [col[0] for col in res.description]
  rows = res.fetchall()
  bal = DF(rows, columns=columns)
  bal['year_month'] = bal['year_month'].astype(str)
  bal['account_number'] = bal['account_number'].astype(str)
  bal['acct_disp_name'] = bal['acct_disp_name'].astype(str)
  
  min_date, max_date = transaction_date_range(conn)
  months:list[str] = year_months_in_range(min_date, max_date)
  accounts = bal['account_number'].unique().tolist()
  for month in months:
    for account in accounts:
      filter_exact:DF = bal[(bal['year_month']==month) & (bal['account_number']==account)]
      if not filter_exact.empty:
        continue
      filtered:DF = bal[(bal['year_month']<month) & (bal['account_number']==account)]
      if filtered.empty:
        continue
      latest_month = filtered['year_month'].max()
      latest_row = bal[(bal['year_month']==latest_month) & (bal['account_number']==account)].iloc[0]
      new_row = DF.from_records([{
        'year_month': month,
        'account_number': account,
        'acct_disp_name': acct_disp_name(account, conn),
        'cashflow': 0,
        'month_end_balance': latest_row['month_end_balance']
      }])
      bal = pd.concat([bal, new_row], ignore_index=True)
  return bal.sort_values(by=['year_month','account_number'], ascending=[False,True])

def monthly_acct_stat_exists(mas:MonthlyAccountStats, conn:sqlite3.Connection) -> bool:
  cur = conn.cursor()
  res = cur.execute(
    "select count(*) from MONTHLY_ACCOUNT_STATS ms where ms.YEAR_MONTH = ? and ms.ACCOUNT_NUMBER = ?", 
    (mas.year_month, mas.account_number))
  count, = res.fetchone()
  return count > 0

def upsert_monthly_acct_stat(mas:MonthlyAccountStats, conn:sqlite3.Connection):
  cur = conn.cursor()
  try:
    if not monthly_acct_stat_exists(mas, conn):
      cur.execute(
        """
        insert into MONTHLY_ACCOUNT_STATS
        (YEAR_MONTH, ACCOUNT_NUMBER, CASHFLOW, MONTH_END_BALANCE, CREATION_DATE, LAST_UPDATE_DATE)
        values (?, ?, ?, ?, ?, ?)
        """, (mas.year_month, mas.account_number, mas.cashflow, mas.month_end_balance, dt.datetime.today(), dt.datetime.today())
      )
    else:
      cur.execute(
        """
        update MONTHLY_ACCOUNT_STATS
        set CASHFLOW = ?, MONTH_END_BALANCE = ?, LAST_UPDATE_DATE = ?
        where YEAR_MONTH = ? and ACCOUNT_NUMBER = ?
        """, (mas.cashflow, mas.month_end_balance, dt.datetime.today(), mas.year_month, mas.account_number)
      )
    conn.commit()
  except Exception as e:
    conn.rollback()
    raise e
  
def refresh_monthly_account_stats(conn:sqlite3.Connection):
  for entry in MonthlyAccountStats.list_from_dataframe(prep_monthly_stats_from_txn_history(conn)):
    upsert_monthly_acct_stat(entry, conn)
    
def fetch_monthly_account_stats(
  conn:sqlite3.Connection,
  start_date:dt.date|None = None,
  end_date:dt.date|None = None,
  include_months:list[str] = []
) -> list[MonthlyAccountStats]:
  start_yr_mo = None if start_date is None else dt.date.strftime(start_date, '%Y-%m')
  end_yr_mo = None if end_date is None else dt.date.strftime(end_date, '%Y-%m')
  include_all = False
  if len(include_months) == 0:
    include_all = True
  cur = conn.cursor()
  res = cur.execute(
    """
    select ms.YEAR_MONTH, 
           ms.ACCOUNT_NUMBER,
           ms.CASHFLOW, 
           ms.MONTH_END_BALANCE 
    from MONTHLY_ACCOUNT_STATS ms
    where (ms.YEAR_MONTH >= :start_yr_mo or :start_yr_mo is null)
    and (ms.YEAR_MONTH <= :end_yr_mo or :end_yr_mo is null)
    and (:include_all or ms.YEAR_MONTH in (select value from json_each(:include_yr_mo)))
    order by YEAR_MONTH desc, ms.ACCOUNT_NUMBER
    """, ({
      'start_yr_mo': start_yr_mo, 
      'end_yr_mo': end_yr_mo, 
      'include_yr_mo': json.dumps(include_months), 
      'include_all': include_all
    })
  )
  return [MonthlyAccountStats(yr_mo, acct_no, cashflow, balance) 
          for yr_mo, acct_no, cashflow, balance in res.fetchall()]
  
def fetch_cashflow_by_account(
  conn:sqlite3.Connection,
  start_date:dt.date|None = None,
  end_date:dt.date|None = None,
  include_months:list[str] = []
) -> PivotTable:
  df = MonthlyAccountStats.dataframe_from_list(
    fetch_monthly_account_stats(conn, start_date, end_date, include_months))
  return PivotTable.from_dataframe(df.pivot_table(
    index='year_month',
    columns='account_number',
    values='cashflow',
    aggfunc='sum'
  ), index_col='year_month')
  
def fetch_balance_by_account(
  conn:sqlite3.Connection,
  start_date:dt.date|None = None,
  end_date:dt.date|None = None,
  include_months:list[str] = []
) -> PivotTable:
  df = MonthlyAccountStats.dataframe_from_list(
    fetch_monthly_account_stats(conn, start_date, end_date, include_months))
  return PivotTable.from_dataframe(df.pivot_table(
    index='year_month',
    columns='account_number',
    values='month_end_balance',
    aggfunc='sum'
  ), index_col='year_month')
  
def fetch_balance_overall(
  conn:sqlite3.Connection,
  start_date:dt.date|None = None,
  end_date:dt.date|None = None,
  include_months:list[str] = []
) -> list[OverallBalance]:
  start_yr_mo = None if start_date is None else dt.date.strftime(start_date, '%Y-%m')
  end_yr_mo = None if end_date is None else dt.date.strftime(end_date, '%Y-%m')
  include_all = False
  if len(include_months) == 0:
    include_all = True
  cur = conn.cursor()
  res = cur.execute(
    """
    select ms.YEAR_MONTH, sum(ms.MONTH_END_BALANCE)
    from MONTHLY_ACCOUNT_STATS ms
    where (:start_yr_mo is null or ms.YEAR_MONTH >= :start_yr_mo)
    and (:end_yr_mo is null or ms.YEAR_MONTH <= :end_yr_mo)
    and (:include_all or ms.YEAR_MONTH in (select value from json_each(:include_yr_mo)))
    group by ms.YEAR_MONTH
    order by ms.YEAR_MONTH desc
    """, ({
      'start_yr_mo': start_yr_mo,
      'end_yr_mo': end_yr_mo,
      'include_all': include_all,
      'include_yr_mo': json.dumps(include_months)
    }))
  return [OverallBalance(year_month, balance) for year_month, balance in res.fetchall()]

def fetch_cashflow_overall(
  conn:sqlite3.Connection,
  window_months:int = 6,
  start_date:dt.date|None = None,
  end_date:dt.date|None = None,
  include_months:list[str] = []
) -> list[OverallCashflow]:
  start_yr_mo = None if start_date is None else dt.date.strftime(start_date, '%Y-%m')
  end_yr_mo = None if end_date is None else dt.date.strftime(end_date, '%Y-%m')
  include_all = False
  if len(include_months) == 0:
    include_all = True
  cur = conn.cursor()
  res = cur.execute(
    """
    with cf as (select ms.YEAR_MONTH as year_month, sum(ms.CASHFLOW) as cashflow
                from MONTHLY_ACCOUNT_STATS ms
                group by ms.YEAR_MONTH
                order by ms.YEAR_MONTH)
    select cf.year_month, 
           cf.cashflow,
           avg(cf.cashflow) over (order by cf.year_month 
                                  rows between :window preceding and current row) as rolling_avg
    from cf
    where (:start_yr_mo is null or cf.year_month >= :start_yr_mo)
    and (:end_yr_mo is null or cf.year_month <= :end_yr_mo)
    and (:include_all or cf.year_month in (select value from json_each(:include_yr_mo)))
    order by cf.year_month desc
    """, ({
      'start_yr_mo': start_yr_mo,
      'end_yr_mo': end_yr_mo,
      'include_all': include_all,
      'include_yr_mo': json.dumps(include_months),
      'window': window_months
    }))
  return [OverallCashflow(ym, cf, ra) for ym, cf, ra in res.fetchall()]