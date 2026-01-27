import pandas as pd
import os
import sqlite3
import txn_support as ts
import stmt_readers as sr
import datetime as dt
from stmt_reader_support import StmtReader

nilsaha_drive_path = '/Users/nilsaha/Library/CloudStorage/GoogleDrive-sahafamily03@gmail.com/My Drive/IMPORTANT DOCUMENTS/3. NILABRO SAHA/'
db_path = os.path.join(nilsaha_drive_path, 'Databases/nilsaha_personal.db')
src_data_dir = os.path.join(nilsaha_drive_path, '8. EXPENSE TRACKING/Transaction History/')
output_data_dir = os.path.join(nilsaha_drive_path, '8. EXPENSE TRACKING/Reports/')

def row_to_transaction(row: pd.Series) -> ts.BankTransaction:
  return ts.BankTransaction(
    date=row['date'],
    day_seq=row['day_seq'],
    description=row['description'],
    withdrawn=row['withdrawn'],
    deposited=row['deposited'],
    balance=row['balance'],
    net_amount=row['net_amount'],
    account_number=row['account_number']
  )
  
def discover_txn_hist_and_save(reader:StmtReader, conn:sqlite3.Connection):
  try:
    print('======================\n')
    txn_df = reader.discover_stmts_and_read_all()
    print(txn_df)
    txns: list[ts.BankTransaction] = txn_df.apply(row_to_transaction, axis=1).tolist()
    ins_results = [ts.insert_transaction(txn, conn) for txn in txns]
    ins_count = len([res for res in ins_results if res])
    skip_count = len([res for res in ins_results if not res])
    print(f'Inserted {ins_count} transactions. Skipped {skip_count} transactions.')
  except Exception as e:
    raise RuntimeError(f'Failed to read using {reader}') from e

with sqlite3.connect(db_path) as conn:
  readers:list[StmtReader] = [
    sr.ICICIBankStmtReader(file_name_contains='icici-4675-txn-hist',src_data_dir=src_data_dir,account_no='090001004675'),
    sr.ICICIPPFStmtReader(file_name_contains='icici-5741-txn-hist',src_data_dir=src_data_dir,account_no='627818005741'),
    sr.NIMFStmtReader(file_name_contains='nimf-2765-txn-hist', src_data_dir=src_data_dir, account_no='499287502765'),
    sr.NIMFStmtReader(file_name_contains='nimf-1131-txn-hist', src_data_dir=src_data_dir, account_no='477284971131'),
    sr.SBIMFStmtReader(file_name_contains='sbimf-4231-txn-hist', src_data_dir=src_data_dir,account_no='34014231',password='KIUPS2232C'),
    sr.ICICIFDStmtReader(file_name_contains='icicifd-9002-txn-hist',src_data_dir=src_data_dir,account_no='090013009002'),
    sr.ICICIFDStmtReader(file_name_contains='icicifd-9003-txn-hist',src_data_dir=src_data_dir,account_no='090013009003'),
    sr.EPFOStmtReader(file_name_contains='BGBNG00423570000311747',src_data_dir=src_data_dir,account_no='BGBNG00423570000311747'),
    # sr.SBIBankStmtReader(file_name_contains='sbi-7582-txn-hist',src_data_dir=src_data_dir,account_no='00000038189267582'),
    sr.SBIBankStmtReader2(file_name_contains='sbi-7582-txn-hist',src_data_dir=src_data_dir,account_no='00000038189267582',password='NILAB28022000'),
    sr.INDBankStmtReader(file_name_contains='ind-1135-txn-hist',src_data_dir=src_data_dir,account_no='50248401135'),
    sr.HDFCMFStmtReader(file_name_contains='hdfc-mf-7382-txn-hist',src_data_dir=src_data_dir,account_no='29277389')
  ]
  for reader in readers:
    discover_txn_hist_and_save(reader, conn)
  
  print('\n---Month end balances and monthly cash flow by account---')
  mend_bal = ts.prep_monthly_stats_from_txn_history(conn)
  print(mend_bal)
  
  print('\n---Balances by acct over time---')
  bal_by_acct_over_time = mend_bal.pivot_table(
    index='year_month',
    columns='acct_disp_name',
    values='month_end_balance',
    aggfunc='sum'
  )
  # bal_by_acct_over_time['Total'] = bal_by_acct_over_time.sum(axis=1)
  print(bal_by_acct_over_time)
  
  print('\n---Cashflow by acct over time---')
  flo_by_acct_over_time = mend_bal.pivot_table(
    index='year_month',
    columns='acct_disp_name',
    values='cashflow',
    aggfunc='sum'
  )
  # flo_by_acct_over_time['Total'] = flo_by_acct_over_time.sum(axis=1)
  print(flo_by_acct_over_time)
  
  net_bal_over_time = mend_bal.groupby(by='year_month').agg({'month_end_balance':'sum'})
  net_flo_over_time = mend_bal.groupby(by='year_month').agg({'cashflow':'sum'})
  
  net_flo_over_time['cashflow_6mo_avg'] = net_flo_over_time['cashflow'].rolling(window=6).mean()
  
  today_str = dt.datetime.today().strftime('%Y%m%d')
  out_file_path = os.path.join(output_data_dir, f'month-end-balances-report-{today_str}.xlsx')
  print(f'{out_file_path=}')
  # with pd.ExcelWriter(out_file_path, engine='openpyxl') as w:
  #   mend_bal.to_excel(w, sheet_name='Month end balances', index=False)
  #   bal_by_acct_over_time.to_excel(w, sheet_name='Balances by acct over time')
  #   flo_by_acct_over_time.to_excel(w, sheet_name='Cashflow by acct over time')
  #   net_bal_over_time.to_excel(w, sheet_name='Net balance over time')
  #   net_flo_over_time.to_excel(w, sheet_name='Net cashflow over time')
  #   print(f'Transaction stats saved to file {out_file_path}')