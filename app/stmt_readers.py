import pandas as pd
import app.stmt_reader_support as srs
from app.mapped_schema import MappedSchema as ms
from app.mapped_schema import Column as msc
from app.stmt_reader_support import StmtColType as sct
from app.stmt_reader_support import StmtMapperType
import os
import camelot

class ICICIBankStmtReader(srs.StmtReader):
  """
  Reads ICICI Bank Account Statements
  """
  def __init__(self, account_no:str, src_data_dir:str, file_name_contains:str):
    super().__init__(
      schema=srs.StmtSchema(
        columns=[
          srs.StmtColumn('S No.',sct.INTEGER,False,day_sort_order=1),
          srs.StmtColumn('Value Date',sct.DATE,False,date_format='dd,MM,yyyy'),
          srs.StmtColumn('Transaction Date',sct.DATE,False,date_format='dd,MM,yyyy',day_sort_order=0,index_by=True,mapped_column=msc.DATE),
          srs.StmtColumn('Transaction Remarks',sct.TEXT,False,index_by=True,mapped_column=msc.DESCRIPTION),
          srs.StmtColumn('Withdrawal Amount (INR )',sct.REAL,False,mapped_column=msc.WITHDRAWN),
          srs.StmtColumn('Deposit Amount (INR )',sct.REAL,False,mapped_column=msc.DEPOSITED),
          srs.StmtColumn('Balance (INR )',sct.REAL,False,mapped_column=msc.BALANCE)
        ]  
      ),
      account_no=account_no,
      src_data_dir=src_data_dir, 
      file_name_contains=file_name_contains, 
      file_format='.xls'
    )
    
class ICICIPPFStmtReader(srs.StmtReader):
  """
  Reads ICICI Bank PPF Account Statements
  """
  def __init__(self, account_no:str, src_data_dir:str, file_name_contains:str):
    super().__init__(
      schema=srs.StmtSchema(
        columns=[
          srs.StmtColumn('Sr No.',sct.INTEGER,nullable=False),
          srs.StmtColumn('Transaction Date',sct.DATE,nullable=False,date_format='dd,MM,yyyy',mapped_column=msc.DATE,index_by=True,day_sort_order=0),
          srs.StmtColumn('Transaction Remarks',sct.TEXT,nullable=False,mapped_column=msc.DESCRIPTION,index_by=True),
          srs.StmtColumn('Withdrawal Amount (INR )',sct.REAL,nullable=False,mapped_column=msc.WITHDRAWN),
          srs.StmtColumn('Deposit Amount (INR )',sct.REAL,nullable=False,mapped_column=msc.DEPOSITED),
          srs.StmtColumn('Balance (INR )',sct.REAL,nullable=False,mapped_column=msc.BALANCE,index_by=True,day_sort_order=1)
        ]
      ),
      account_no=account_no,
      file_name_contains=file_name_contains,
      src_data_dir=src_data_dir,
      file_format='.xls'
    )

class ICICIFDStmtReader(srs.StmtReader):
  def __init__(self, account_no:str, src_data_dir:str, file_name_contains:str):
    super().__init__(
      schema=srs.StmtSchema(
        adapter_type=StmtMapperType.NET_AMOUNT_AND_BALANCE,
        columns=[
          srs.StmtColumn('Deposit Srl No',sct.INTEGER,nullable=False,day_sort_order=1),
          srs.StmtColumn('Deposit Date',sct.DATE,nullable=False,date_format='ddMMyyyy'),
          srs.StmtColumn('Deposit Amount',sct.REAL,nullable=True),
          srs.StmtColumn('Interest Amount',sct.REAL,nullable=True),
          srs.StmtColumn('Transaction Date',sct.DATE,date_format='ddMMyyyy',nullable=False,index_by=True,day_sort_order=0,mapped_column=msc.DATE),
          srs.StmtColumn('Transaction Amount',sct.REAL,nullable=False,mapped_column=msc.NET_AMOUNT),
          srs.StmtColumn('Transaction Type',sct.TEXT,nullable=False,index_by=True,mapped_column=msc.DESCRIPTION),
          srs.StmtColumn('Cumulative Balance',sct.REAL,nullable=False,index_by=True,mapped_column=msc.BALANCE)
        ]
      ),
      account_no=account_no,
      src_data_dir=src_data_dir,
      file_name_contains=file_name_contains,
      file_format='.xlsx'
    )
    
class INDBankStmtReader(srs.StmtReader):
  def __init__(self, account_no:str, src_data_dir:str, file_name_contains:str):
    super().__init__(
      schema=srs.StmtSchema(
        columns=[
          srs.StmtColumn('Date',sct.DATE,False,date_format='dd MMM yyyy',index_by=True,mapped_column=msc.DATE),
          srs.StmtColumn('Transaction Details',sct.TEXT,False,index_by=True,mapped_column=msc.DESCRIPTION),
          srs.StmtColumn('Debits',sct.REAL,False,mapped_column=msc.WITHDRAWN),
          srs.StmtColumn('Credits',sct.REAL,False,mapped_column=msc.DEPOSITED),
          srs.StmtColumn('Balance',sct.REAL,False,mapped_column=msc.BALANCE)
        ]
      ),
      account_no=account_no,
      src_data_dir=src_data_dir, 
      file_name_contains=file_name_contains, 
      file_format='.xlsx'
    )
    
class NIMFStmtReader(srs.StmtReader):
  def __init__(self, src_data_dir:str, file_name_contains:str, account_no:str):
    super().__init__(
      schema=srs.StmtSchema(
        adapter_type=StmtMapperType.DEPOSITED_ONLY,
        columns=[
          srs.StmtColumn('Acno',sct.TEXT,nullable=False,index_by=True,mapped_column=msc.ACCOUNT_NUMBER),
          srs.StmtColumn('TrDate',sct.DATE,nullable=False,date_format='dd/MM/yyyy',day_sort_order=0,index_by=True,mapped_column=msc.DATE),
          srs.StmtColumn('TrDesc',sct.TEXT,nullable=False,index_by=True,mapped_column=msc.DESCRIPTION),
          srs.StmtColumn('Amount',sct.REAL,nullable=False,mapped_column=msc.DEPOSITED),
          srs.StmtColumn('BalUnits',sct.REAL,nullable=False,day_sort_order=1,index_by=True)
        ]
      ),
      account_no=account_no,
      src_data_dir=src_data_dir, 
      file_name_contains=file_name_contains, 
      file_format='.xls'
    )
    
class SBIBankStmtReader(srs.StmtReader):
  def __init__(self, account_no:str, src_data_dir:str, file_name_contains:str):
    super().__init__(
      schema=srs.StmtSchema(
        columns=[
          srs.StmtColumn('Txn Date',sct.DATE,False,date_format='dd MMM yyyy',index_by=True,mapped_column=msc.DATE),
          srs.StmtColumn('Description',sct.TEXT,False,index_by=True,mapped_column=msc.DESCRIPTION),
          srs.StmtColumn('Debit',sct.REAL,False,mapped_column=msc.WITHDRAWN),
          srs.StmtColumn('Credit',sct.REAL,False,mapped_column=msc.DEPOSITED),
          srs.StmtColumn('Balance',sct.REAL,False,mapped_column=msc.BALANCE)
        ]
      ),
      account_no=account_no,
      src_data_dir=src_data_dir, 
      file_name_contains=file_name_contains, 
      file_format='.pdf'
    )
    
class SBIBankStmtReader2(srs.StmtReader):
  def __init__(self, account_no:str, src_data_dir:str, file_name_contains:str, password:str):
    super().__init__(
      schema=srs.StmtSchema(
        columns=[
          srs.StmtColumn('Date',sct.DATE,False,date_format='dd/MM/yyyy',index_by=True,mapped_column=msc.DATE),
          srs.StmtColumn('Details',sct.TEXT,False,index_by=True,mapped_column=msc.DESCRIPTION),
          srs.StmtColumn('Debit',sct.REAL,True,mapped_column=msc.WITHDRAWN),
          srs.StmtColumn('Credit',sct.REAL,True,mapped_column=msc.DEPOSITED),
          srs.StmtColumn('Balance',sct.REAL,False,mapped_column=msc.BALANCE)
        ]
      ),
      password=password,
      account_no=account_no,
      src_data_dir=src_data_dir, 
      file_name_contains=file_name_contains, 
      file_format='.xlsx'
    )
    
class SBIMFStmtReader(srs.StmtReader):
  def __init__(self, account_no:str, src_data_dir:str, file_name_contains:str, password:str):
    super().__init__(
      schema=srs.StmtSchema(
        adapter_type=StmtMapperType.NET_AMOUNT_ONLY,
        columns=[
          srs.StmtColumn('Date',sct.DATE,False,date_format='dd/MM/yyyy',day_sort_order=0,index_by=True,mapped_column=msc.DATE),
          srs.StmtColumn('Transaction Type',sct.TEXT,False,index_by=True,mapped_column=msc.DESCRIPTION),
          srs.StmtColumn('Amount',sct.REAL,False,mapped_column=msc.NET_AMOUNT),
          srs.StmtColumn('NAV in INR ( Rs.)',sct.REAL,False),
          srs.StmtColumn('Price in INR(Rs.)',sct.REAL,False),
          srs.StmtColumn('Number of Units',sct.REAL,False),
          srs.StmtColumn('Balance Unit',sct.REAL,False,day_sort_order=1,index_by=True),
        ]
      ),
      account_no=account_no, 
      src_data_dir=src_data_dir, 
      file_name_contains=file_name_contains, 
      file_format='.xlsx', 
      password=password
    )
    
class HDFCMFStmtReader(srs.StmtReader):
  def __init__(self, account_no:str, src_data_dir:str, file_name_contains:str):
    super().__init__(
      schema=srs.StmtSchema(
        adapter_type=StmtMapperType.NET_AMOUNT_AND_TXN_TYPE_ONLY,
        columns=[
          srs.StmtColumn('Date',sct.DATE,False,date_format='yyyy-MM-dd hh:mm:ss',day_sort_order=0,index_by=True,mapped_column=msc.DATE),
          srs.StmtColumn('Investment type',sct.TEXT,False,mapped_column=msc.DESCRIPTION),
          srs.StmtColumn('Transaction type',sct.TEXT,False,mapped_column=msc.DESCRIPTION),
          srs.StmtColumn('Scheme',sct.TEXT,False,mapped_column=msc.DESCRIPTION),
          srs.StmtColumn('Amount',sct.REAL,False,mapped_column=msc.NET_AMOUNT)
        ],
        txn_type_col='Transaction type',
        debit_txn_types=['REDEMPTION','SWITCH']
      ),
      account_no=account_no, 
      src_data_dir=src_data_dir, 
      file_name_contains=file_name_contains, 
      file_format='.xlsx'
    )
    
class EPFOStmtReader(srs.StmtReader):
  ALL_PDF_COLUMNS = [
    "wage month - txn date", 
    "txn type", 
    "particulars", 
    "wages/epf",
    "wages/eps", 
    "contribution/employee", 
    "contribution/employer", 
    "contribution/pension"
  ]
  
  def __init__(
    self, 
    account_no:str, 
    src_data_dir:str,
    file_name_contains:str
  ):
    super().__init__(
      schema=srs.StmtSchema(
        columns=[
          srs.StmtColumn('date', sct.DATE, False, 'dd-MM-yyyy', index_by=True, mapped_column=msc.DATE),
          srs.StmtColumn('txn type', sct.TEXT, True),
          srs.StmtColumn('particulars', sct.TEXT, False, index_by=True, mapped_column=msc.DESCRIPTION),
          srs.StmtColumn('starting_bal', sct.REAL, False),
          srs.StmtColumn('wages/epf', sct.REAL, True),
          srs.StmtColumn('wages/eps', sct.REAL, True),
          srs.StmtColumn('contribution/employee', sct.REAL, True, mapped_column=msc.DEPOSITED),
          srs.StmtColumn('contribution/employer', sct.REAL, True, mapped_column=msc.DEPOSITED),
          srs.StmtColumn('contribution/pension', sct.REAL, True, mapped_column=msc.DEPOSITED)
        ],
        adapter_type=StmtMapperType.DEPOSITED_AND_STARTING_BALANCE,
        starting_bal_col='starting_bal'
      ),
      account_no=account_no, 
      src_data_dir=src_data_dir, 
      file_name_contains=file_name_contains, 
      file_format='.pdf', 
    )
    
  def __normalize_pdf_data(self, pdf_df: pd.DataFrame, starting_bal:float) -> pd.DataFrame:
    # print(pdf_df)
    date_pattern = r'\b\d{2}-\d{2}-\d{4}\b'
    mask = pdf_df.apply(lambda r: r.astype(str).str.contains(date_pattern, regex=True).any(), axis=1)
    df = pdf_df[mask].copy()
    df = df.loc[:, ~(df == '').all()]
    df.columns = EPFOStmtReader.ALL_PDF_COLUMNS
    df[['wage month','date']] = df['wage month - txn date'].str.split(' ',n=1,expand=True)
    df['starting_bal'] = starting_bal
    return df[self.schema.column_names()]
  
  def __starting_balance(self, df:pd.DataFrame) -> float:
    bal_cols = ['employee bal','employer bal','pension bal']
    bal_mask = df.apply(lambda r: r.astype(str).str.contains('OB Int. Updated upto').any(), axis=1)
    bal_df:pd.DataFrame = df[bal_mask].copy()
    bal_df = bal_df.loc[:, ~(bal_df == '').all()]
    bal_df.columns = ['particulars','balances']
    bal_df[bal_cols] = bal_df['balances'].str.split('\n',n=2,expand=True)
    bal_df = bal_df.drop(columns=['balances'])
    bal_df[bal_cols] = bal_df[bal_cols].map(srs.strip_locale_formatting)
    bal_df['starting bal'] = bal_df[bal_cols].sum(axis=1)
    return bal_df['starting bal'].iloc[0]

  def read_stmt_as_df(self, src_data_file_paths: list[str]) -> pd.DataFrame:
    dfs = []
    for path in src_data_file_paths:
      df:pd.DataFrame = camelot.read_pdf(path, pages="1")[0].df
      starting_bal = self.__starting_balance(df)
      df = self.__normalize_pdf_data(df, starting_bal)
      for col in self.schema.columns:
        df[col.name] = df[col.name].apply(lambda value: srs.adapt_value_to_column(value, col))
      df = self.adapt_stmt_to_mapped_schema(df)
      dfs.append(df)
    return pd.concat(dfs, ignore_index=True)