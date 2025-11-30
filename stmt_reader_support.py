import io
import msoffcrypto
import numpy as np
from pandas import DataFrame as DF
from typing import List
import pandas as pd
from dataclasses import dataclass
from enum import Enum
from typing import Any
import babel.dates as bbld
import datetime as dt
from mapped_schema import Column as msc
import os
import re
import pdfplumber
import numpy as np
from mapped_schema import MappedSchema as ms

@dataclass
class StmtFile:
  path:str
  password:str|None = None

class StmtColType(Enum):
  TEXT = 1
  DATE = 2
  REAL = 3
  INTEGER = 4
  
  @staticmethod
  def resolve(col_type_str:str) -> "StmtColType":
    match col_type_str:
      case 'TEXT': 
        return StmtColType.TEXT
      case 'DATE':
        return StmtColType.DATE
      case 'REAL':
        return StmtColType.REAL
      case 'INTEGER':
        return StmtColType.INTEGER
      case _:
        raise TypeError(f"Cannot resolve value '{col_type_str}' to any valid StmtColType")
      
class StmtMapper:
  def adapt_to_mapped_schema(self, df:pd.DataFrame, reader:"StmtReader") -> pd.DataFrame:
    pass
  
class DefaultMapper(StmtMapper):
  def adapt_to_mapped_schema(self, df, reader):
    mapped = df.rename(columns=reader.schema.column_mapping())
    mapped[msc.day_seq] = mapped.groupby([msc.date]).cumcount() + 1
    mapped[msc.net_amount] = mapped[msc.deposited] - mapped[msc.withdrawn]
    if msc.account_number not in mapped.columns:
      mapped[msc.account_number] = reader.account_no
    return mapped[ms.columns()]
  
class NetAmountOnlyMapper(StmtMapper):
  def adapt_to_mapped_schema(self, df, reader):
    mapped = df.rename(columns=reader.schema.column_mapping())
    mapped[msc.day_seq] = mapped.groupby([msc.date]).cumcount() + 1
    mapped[msc.deposited] = mapped[msc.net_amount].apply(lambda a: 0 if a < 0 else a)
    mapped[msc.withdrawn] = mapped[msc.net_amount].apply(lambda a: 0 if a >= 0 else a)
    mapped[msc.balance] = mapped[msc.net_amount].cumsum()
    if msc.account_number not in mapped.columns:
      mapped[msc.account_number] = reader.account_no
    return mapped[ms.columns()]
  
class DepositedOnlyMapper(StmtMapper):
  def adapt_to_mapped_schema(self, df, reader):
    mapped = df.rename(columns=reader.schema.column_mapping())
    mapped[msc.day_seq] = mapped.groupby([msc.date]).cumcount() + 1
    mapped[msc.withdrawn] = 0
    mapped[msc.net_amount] = mapped[msc.deposited] - mapped[msc.withdrawn]
    mapped[msc.balance] = mapped[msc.net_amount].cumsum()
    if msc.account_number not in mapped.columns:
      mapped[msc.account_number] = reader.account_no
    return mapped[ms.columns()]
  
class NetAmountAndBalanceMapper(StmtMapper):
  def adapt_to_mapped_schema(self, df, reader):
    mapped = df.rename(columns=reader.schema.column_mapping())
    mapped[msc.day_seq] = mapped.groupby([msc.date]).cumcount() + 1
    mapped[msc.deposited] = mapped[msc.net_amount].apply(lambda a: 0 if a < 0 else a)
    mapped[msc.withdrawn] = mapped[msc.net_amount].apply(lambda a: 0 if a >= 0 else a)
    if msc.account_number not in mapped.columns:
      mapped[msc.account_number] = reader.account_no
    return mapped[ms.columns()]
  
class StmtMapperType(Enum):
  def __new__(cls, *args, **kwds):
    value = len(cls.__members__) + 1
    obj = object.__new__(cls)
    obj._value_ = value
    return obj
  
  def __init__(self, mapper:StmtMapper):
    self.mapper = mapper
    
  @staticmethod
  def resolve(mapper_type_str:str) -> 'StmtMapperType':
    match mapper_type_str:
      case 'DEFAULT':
        return StmtMapperType.DEFAULT
      case 'NET_AMOUNT_ONLY':
        return StmtMapperType.NET_AMOUNT_ONLY
      case 'DEPOSITED_ONLY':
        return StmtMapperType.DEPOSITED_ONLY
      case 'NET_AMOUNT_AND_BALANCE':
        return StmtMapperType.NET_AMOUNT_AND_BALANCE
      case _:
        raise TypeError(f"Cannot resolve string '{mapper_type_str}' into any valid StmtMapperType")
    
  DEFAULT = DefaultMapper()
  NET_AMOUNT_ONLY = NetAmountOnlyMapper()
  DEPOSITED_ONLY = DepositedOnlyMapper()
  NET_AMOUNT_AND_BALANCE = NetAmountAndBalanceMapper()

@dataclass
class StmtColumn:
  name:str
  data_type:StmtColType
  nullable:bool = True
  date_format:str | None = None
  day_sort_order:int = None
  index_by:bool = False
  mapped_column:str | None = None
  
  @staticmethod
  def from_dict(column:dict[str, Any]) -> 'StmtColumn':
    return StmtColumn(
      name=column['name'],
      data_type=StmtColType.resolve(column['data_type']),
      nullable=column.get('nullable', default=True),
      date_format=column.get('date_format'),
      day_sort_order=column.get('day_sort_order'),
      index_by=column.get('index_by', default=False),
      mapped_column=column.get('mapped_column')
    )
  
class StmtSchema:
  def __init__(
    self, 
    columns:list[StmtColumn],
    adapter_type:StmtMapperType = StmtMapperType.DEFAULT
  ):
    self.columns = columns
    self.adapter_type = adapter_type
    
  @staticmethod
  def from_dict(schema:dict[str, Any]) -> 'StmtSchema':
    return StmtSchema(
      adapter_type=StmtMapperType.resolve(schema['adapter_type']),
      columns=[StmtColumn.from_dict(column) for column in schema['columns']]
    )
    
  def get_column(self, column_name:str) -> StmtColumn | None:
    return next((col for col in self.columns if col.name == column_name), None)
  
  def column_names(self) -> list[str]:
    return [col.name for col in self.columns]
  
  def nullable_columns(self) -> list[StmtColumn]:
    return [col for col in self.columns if col.nullable]
  
  def nullable_column_names(self) -> list[str]:
    return [col.name for col in self.nullable_columns()]
  
  def non_nullable_columns(self) -> list[StmtColumn]:
    return [col for col in self.columns if not col.nullable]
  
  def non_nullable_column_names(self) -> list[str]:
    return [col.name for col in self.non_nullable_columns()]
  
  def order_columns(self) -> list[StmtColumn]:
    return sorted([col for col in self.columns if col.day_sort_order is not None], key=lambda c: c.day_sort_order)
  
  def order_column_names(self) -> list[str]:
    return [col.name for col in self.order_columns()]
  
  def index_columns(self) -> list[StmtColumn]:
    return [col for col in self.columns if col.index_by]
  
  def index_column_names(self) -> list[str]:
    return [col.name for col in self.index_columns()]
  
  def column_mapping(self) -> dict[str, str]:
    return {col.name : col.mapped_column for col in self.columns if col.mapped_column is not None}
  
  def account_number_column(self) -> StmtColumn | None:
    for col in self.columns:
      if col.mapped_column == msc.account_number:
        return col
    return None
  
class StmtReader:
  def __init__(
    self, 
    schema:StmtSchema, 
    account_no:str,
    src_data_dir:str, 
    file_name_contains:str, 
    file_format:str = '.xlsx', 
    password:str|None = None,
    stmt_mapper_type:StmtMapperType = StmtMapperType.DEFAULT
  ):
    self.schema = schema
    self.account_no = account_no
    self.src_data_dir = src_data_dir
    self.file_name_contains = file_name_contains
    self.file_format = file_format
    self.password = password
    self.stmt_mapper_type = stmt_mapper_type
  
  def read_stmt_as_df(self, src_data_file_paths:list[str]) -> pd.DataFrame:
    return read_all_stmt_files_into_df(
      [StmtFile(path, self.password) for path in src_data_file_paths],
      self.schema,
      self.account_no
    )
  
  def adapt_stmt_to_mapped_schema(self, df:pd.DataFrame) -> pd.DataFrame:
    return self.stmt_mapper_type.mapper.adapt_to_mapped_schema(df, self)
  
  def discover_stmts_and_read_all(self) -> pd.DataFrame:
    file_names = [file.decode('utf-8') for file in os.listdir(os.fsencode(self.src_data_dir))]
    file_names.sort()
    src_data_files = [os.path.join(self.src_data_dir, file_name) 
                      for file_name in file_names 
                      if (file_name.endswith(self.file_format) and self.file_name_contains in file_name)]
    return self.adapt_stmt_to_mapped_schema(self.read_stmt_as_df(src_data_files))

def read_encrypted_xlsx_bytes(password:str, encrypted_file_path:str) -> io.BytesIO:
  temp = io.BytesIO()
  with open(encrypted_file_path, mode='r+b') as f:
    excel = msoffcrypto.OfficeFile(f)
    excel.load_key(password)
    excel.decrypt(temp)
  return temp

def split_at_nan_rows(df:DF) -> List[DF]: return np.split(df, df[df.isnull().all(axis=1)].index)

def seek_target_headers(df:DF, target_headers:list[str]) -> DF | None:
  if all([col in df.columns for col in target_headers]):
    return df
  normalized_tgt_hdrs = [h.strip().lower() for h in target_headers]
  ndf = df.reset_index(drop=True)
  start_row:int = None
  for i, row in ndf.iterrows():
    row_normalized = [str(cell).strip().lower() for cell in row]
    if all(header in row_normalized for header in normalized_tgt_hdrs):
      start_row = i
  if start_row is None:
    return None
  ndf = ndf.iloc[start_row:]
  ndf = ndf.reset_index(drop=True)
  ndf = ndf.T.drop_duplicates().T
  ndf.columns = ndf.iloc[0]
  ndf = ndf[1:]
  ndf = ndf[target_headers]
  ndf = ndf.reset_index(drop=True)
  return ndf

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
  
clrd_to_posix = {
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
    clrd_tokens = sorted(clrd_to_posix.keys(), key=len, reverse=True)
    pattern = '|'.join(map(re.escape, clrd_tokens))
    posix_format = re.sub(pattern, lambda m: clrd_to_posix[m.group()], format)
    return dt.datetime.strptime(date_str, posix_format).date()
  else:
    return bbld.parse_date(date_str, format=format)

def adapt_value_to_column(value:Any, column:StmtColumn):
  match column.data_type:
    case StmtColType.TEXT:
      return value if pd.isna(value) else str(value)
    case StmtColType.DATE:
      return parse_date(value, format=column.date_format)
    case StmtColType.REAL:
      return strip_locale_formatting(value)
    case StmtColType.INTEGER:
      return value if pd.isna(value) else int(str(value))
    case _:
      raise TypeError(f"Unhandled column type '{column.data_type}'")
    
def read_stmt_file_as_df(file:StmtFile, schema:StmtSchema) -> DF:
  try:
    if file.path.endswith('.xls') or file.path.endswith('.xlsx'):
      if file.password is None:
        return pd.read_excel(file.path, header=None)
      else:
        with read_encrypted_xlsx_bytes(file.password, file.path) as iobuf:
          return pd.read_excel(iobuf, header=None)
    elif file.path.endswith('.pdf'):
      dfs = []
      with pdfplumber.open(file.path, password=file.password) as pdf_file:
        for page in pdf_file.pages:
          for table in page.extract_tables():
            table = [[cell.replace('\n', ' ') for cell in row] for row in table]
            df = pd.DataFrame(table)
            df = seek_target_headers(df, target_headers=schema.column_names())
            if df is not None:
              dfs.append(df)
      return pd.concat(dfs, ignore_index=True)[schema.column_names()]
    else:
      raise NotImplementedError(f"Read functionality for this file type is yet to be implemented. Path: '{file.path}'")
  except Exception as e:
    raise ImportError(f"Failed to read file into dataframe. Path: '{file.path}'") from e
  
def read_all_stmt_files_into_df(files:list[StmtFile], schema:StmtSchema, account: str|None = None) -> pd.DataFrame:
  src_data: pd.DataFrame = pd.DataFrame()
  for file in files:
    df = read_stmt_file_as_df(file, schema)
    # print(df)
    df = df.dropna(axis=1,how='all') # drop all null columns
    single_file_data:pd.DataFrame = pd.DataFrame()
    for ndf in split_at_nan_rows(df):
      ndf = ndf.dropna(axis=0,how='all').reset_index(drop=True)
      ndf = seek_target_headers(ndf, schema.column_names())
      if ndf is None:
        continue
      single_file_data = pd.concat([single_file_data, ndf],ignore_index=True)
    src_data = pd.concat([src_data, single_file_data],ignore_index=True)
  # print(src_data)
  src_data = src_data.dropna(subset=schema.non_nullable_column_names(),how='any')
  for col in schema.columns:
    src_data[col.name] = src_data[col.name].apply(lambda value: adapt_value_to_column(value, col))
  acct_col = schema.account_number_column()
  if acct_col is not None and acct_col.name in list(src_data.columns):
    src_data = src_data[src_data[acct_col.name]==account]
  src_data = src_data\
    .drop_duplicates(subset=schema.index_column_names())\
    .sort_values(by=schema.order_column_names())\
    .reset_index(drop=True)
  return src_data[schema.column_names()]