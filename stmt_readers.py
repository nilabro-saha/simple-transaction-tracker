import pandas as pd
import stmt_reader_support as srs
from mapped_schema import MappedSchema as ms
from mapped_schema import Column as msc
from stmt_reader_support import StmtColType as sct
from stmt_reader_support import StmtMapperType
import os

class ICICIBankStmtReader(srs.StmtReader):
  def __init__(self, account_no:str, src_data_dir:str, file_name_contains:str):
    super().__init__(
      schema=srs.StmtSchema(
        columns=[
          srs.StmtColumn('S No.',sct.INTEGER,False,day_sort_order=1),
          srs.StmtColumn('Value Date',sct.DATE,False,date_format='dd,MM,yyyy'),
          srs.StmtColumn('Transaction Date',sct.DATE,False,date_format='dd,MM,yyyy',day_sort_order=0,index_by=True,mapped_column=msc.date),
          srs.StmtColumn('Transaction Remarks',sct.TEXT,False,index_by=True,mapped_column=msc.description),
          srs.StmtColumn('Withdrawal Amount (INR )',sct.REAL,False,mapped_column=msc.withdrawn),
          srs.StmtColumn('Deposit Amount (INR )',sct.REAL,False,mapped_column=msc.deposited),
          srs.StmtColumn('Balance (INR )',sct.REAL,False,mapped_column=msc.balance)
        ]  
      ),
      account_no=account_no,
      src_data_dir=src_data_dir, 
      file_name_contains=file_name_contains, 
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
          srs.StmtColumn('Transaction Date',sct.DATE,date_format='ddMMyyyy',nullable=False,index_by=True,day_sort_order=0,mapped_column=msc.date),
          srs.StmtColumn('Transaction Amount',sct.REAL,nullable=False,mapped_column=msc.net_amount),
          srs.StmtColumn('Transaction Type',sct.TEXT,nullable=False,index_by=True,mapped_column=msc.description),
          srs.StmtColumn('Cumulative Balance',sct.REAL,nullable=False,index_by=True,mapped_column=msc.balance)
        ]
      ),
      account_no=account_no,
      src_data_dir=src_data_dir,
      file_name_contains=file_name_contains,
      file_format='.xlsx'
    )
    
class ICICIPPFStmtReader(srs.StmtReader):
  def __init__(self, account_no:str, src_data_dir:str, file_name_contains:str):
    super().__init__(
      schema=srs.StmtSchema(
        columns=[
          srs.StmtColumn('Sr No.',sct.INTEGER,nullable=False),
          srs.StmtColumn('Transaction Date',sct.DATE,nullable=False,date_format='dd,MM,yyyy',mapped_column=msc.date,index_by=True,day_sort_order=0),
          srs.StmtColumn('Transaction Remarks',sct.TEXT,nullable=False,mapped_column=msc.description,index_by=True),
          srs.StmtColumn('Withdrawal Amount (INR )',sct.REAL,nullable=False,mapped_column=msc.withdrawn),
          srs.StmtColumn('Deposit Amount (INR )',sct.REAL,nullable=False,mapped_column=msc.deposited),
          srs.StmtColumn('Balance (INR )',sct.REAL,nullable=False,mapped_column=msc.balance,index_by=True,day_sort_order=1)
        ]
      ),
      account_no=account_no,
      file_name_contains=file_name_contains,
      src_data_dir=src_data_dir,
      file_format='.xls'
    )
    
class INDBankStmtReader(srs.StmtReader):
  def __init__(self, account_no:str, src_data_dir:str, file_name_contains:str):
    super().__init__(
      schema=srs.StmtSchema(
        columns=[
          srs.StmtColumn('Date',sct.DATE,False,date_format='dd MMM yyyy',index_by=True,mapped_column=msc.date),
          srs.StmtColumn('Transaction Details',sct.TEXT,False,index_by=True,mapped_column=msc.description),
          srs.StmtColumn('Debits',sct.REAL,False,mapped_column=msc.withdrawn),
          srs.StmtColumn('Credits',sct.REAL,False,mapped_column=msc.deposited),
          srs.StmtColumn('Balance',sct.REAL,False,mapped_column=msc.balance)
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
          srs.StmtColumn('Acno',sct.TEXT,nullable=False,index_by=True,mapped_column=msc.account_number),
          srs.StmtColumn('TrDate',sct.DATE,nullable=False,date_format='dd/MM/yyyy',day_sort_order=0,index_by=True,mapped_column=msc.date),
          srs.StmtColumn('TrDesc',sct.TEXT,nullable=False,index_by=True,mapped_column=msc.description),
          srs.StmtColumn('Amount',sct.REAL,nullable=False,mapped_column=msc.deposited),
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
          srs.StmtColumn('Txn Date',sct.DATE,False,date_format='dd MMM yyyy',index_by=True,mapped_column=msc.date),
          srs.StmtColumn('Description',sct.TEXT,False,index_by=True,mapped_column=msc.description),
          srs.StmtColumn('Debit',sct.REAL,False,mapped_column=msc.withdrawn),
          srs.StmtColumn('Credit',sct.REAL,False,mapped_column=msc.deposited),
          srs.StmtColumn('Balance',sct.REAL,False,mapped_column=msc.balance)
        ]
      ),
      account_no=account_no,
      src_data_dir=src_data_dir, 
      file_name_contains=file_name_contains, 
      file_format='.pdf'
    )
    
class SBIMFStmtReader(srs.StmtReader):
  def __init__(self, account_no:str, src_data_dir:str, file_name_contains:str, password:str):
    super().__init__(
      schema=srs.StmtSchema(
        adapter_type=StmtMapperType.NET_AMOUNT_ONLY,
        columns=[
          srs.StmtColumn('Date',sct.DATE,False,date_format='dd/MM/yyyy',day_sort_order=0,index_by=True,mapped_column=msc.date),
          srs.StmtColumn('Transaction Type',sct.TEXT,False,index_by=True,mapped_column=msc.description),
          srs.StmtColumn('Amount',sct.REAL,False,mapped_column=msc.net_amount),
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