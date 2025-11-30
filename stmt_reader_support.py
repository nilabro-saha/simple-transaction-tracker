import io
import msoffcrypto
import numpy as np
from pandas import DataFrame as DF
from typing import List
import pandas as pd
from dataclasses import dataclass
from enum import Enum
from typing import Any
import datetime as dt
from mapped_schema import Column as msc
import pdfplumber
import numpy as np
from mapped_schema import MappedSchema as ms
import json
from utils import get, parse_date, strip_locale_formatting

@dataclass
class StmtFile:
  from_inclusive:dt.date | None
  to_inclusive:dt.date | None
  path:str
  password:str | None = None
  
  @staticmethod
  def from_dict(file:dict[str, Any]) -> 'StmtFile':
    from_str = file['from_inclusive']
    to_str = file['to_inclusive']
    return StmtFile(
      from_inclusive=None if from_str is None else dt.date.fromisoformat(from_str),
      to_inclusive=None if to_str is None else dt.date.fromisoformat(to_str),
      path=file['path'],
      password=file.get('password')
    )

@dataclass
class Statements:
  institution:str
  account_type:str
  account_number:str
  reader_version:int
  files:list[StmtFile]
  
  @staticmethod
  def from_dict(statement:dict[str, Any]) -> 'Statements':
    Statements.__validate_files(statement['files'])
    files = [StmtFile.from_dict(file) for file in statement['files']]
    files = sorted(files, key=lambda f: (f.from_inclusive, f.to_inclusive))
    return Statements(
      institution=statement['institution'],
      account_type=statement['account_type'],
      account_number=statement['account_number'],
      reader_version=statement['reader_version'],
      files=files
    )
    
  @staticmethod
  def __validate_files(files:list[dict[str, Any]]):
    if len(files) == 1:
      return
    df = pd.DataFrame.from_records(files)
    df['overlap'] = (df['to_inclusive'].shift() > df['from_inclusive'])
    df = df[df['overlap']]
    if not df.empty:
      raise ValueError(f'Found overlapping statements {df}')
    
  def file_paths(self) -> list[str]:
    return [file.path for file in self.files]
  
@dataclass  
class StmtRegistry:
  statements:list[Statements]
  
  @staticmethod
  def load_from(file_path:str) -> 'StmtRegistry':
    with open(file_path, mode='r') as reg_file:
      reg:dict[str, Any] = json.load(reg_file)
    statements = [Statements.from_dict(stmt) for stmt in reg['statements']]
    return StmtRegistry(statements)
  
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
  def adapt_to_mapped_schema(self, df:pd.DataFrame, statements:Statements, schema:'StmtSchema') -> pd.DataFrame:
    pass
  
class DefaultMapper(StmtMapper):
  def adapt_to_mapped_schema(self, df, statements, schema):
    mapped = df.rename(columns=schema.column_mapping())
    mapped[msc.day_seq] = mapped.groupby([msc.date]).cumcount() + 1
    mapped[msc.net_amount] = mapped[msc.deposited] - mapped[msc.withdrawn]
    if msc.account_number not in mapped.columns:
      mapped[msc.account_number] = statements.account_number
    mapped = mapped[ms.columns()]
    mapped.columns = ms.columns()
    return mapped
  
class NetAmountOnlyMapper(StmtMapper):
  def adapt_to_mapped_schema(self, df, statements, schema):
    mapped = df.rename(columns=schema.column_mapping())
    mapped[msc.day_seq] = mapped.groupby([msc.date]).cumcount() + 1
    mapped[msc.deposited] = mapped[msc.net_amount].apply(lambda a: 0 if a < 0 else a)
    mapped[msc.withdrawn] = mapped[msc.net_amount].apply(lambda a: 0 if a >= 0 else a)
    mapped[msc.balance] = mapped[msc.net_amount].cumsum()
    if msc.account_number not in mapped.columns:
      mapped[msc.account_number] = statements.account_number
    mapped = mapped[ms.columns()]
    mapped.columns = ms.columns()
    return mapped
  
class DepositedOnlyMapper(StmtMapper):
  def adapt_to_mapped_schema(self, df, statements, schema):
    mapped = df.rename(columns=schema.column_mapping())
    mapped[msc.day_seq] = mapped.groupby([msc.date]).cumcount() + 1
    mapped[msc.withdrawn] = 0
    mapped[msc.net_amount] = mapped[msc.deposited] - mapped[msc.withdrawn]
    mapped[msc.balance] = mapped[msc.net_amount].cumsum()
    if msc.account_number not in mapped.columns:
      mapped[msc.account_number] = statements.account_number
    mapped = mapped[ms.columns()]
    mapped.columns = ms.columns()
    return mapped
  
class NetAmountAndBalanceMapper(StmtMapper):
  def adapt_to_mapped_schema(self, df, statements, schema):
    mapped = df.rename(columns=schema.column_mapping())
    mapped[msc.day_seq] = mapped.groupby([msc.date]).cumcount() + 1
    mapped[msc.deposited] = mapped[msc.net_amount].apply(lambda a: 0 if a < 0 else a)
    mapped[msc.withdrawn] = mapped[msc.net_amount].apply(lambda a: 0 if a >= 0 else a)
    if msc.account_number not in mapped.columns:
      mapped[msc.account_number] = statements.account_number
    mapped = mapped[ms.columns()]
    mapped.columns = ms.columns()
    return mapped
  
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
  day_sort_order:int | None = None
  index_by:bool = False
  mapped_column:str | None = None
  
  @staticmethod
  def from_dict(column:dict[str, Any]) -> 'StmtColumn':
    return StmtColumn(
      name=column['name'],
      data_type=StmtColType.resolve(column['data_type']),
      nullable=get(column, key='nullable', default=True),
      date_format=column.get('date_format'),
      day_sort_order=column.get('day_sort_order'),
      index_by=get(column, key='index_by', default=False),
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
  
@dataclass
class StmtReaderId:
  institution:str
  account_type:str
  version:int
  
  @staticmethod
  def from_dict(id:dict[str, Any]) -> 'StmtReaderId':
    return StmtReaderId(id['institution'], id['account_type'], id['version'])
    
class StmtReader:
  def __init__(self, id:StmtReaderId, schema:StmtSchema, file_format:str):
    self.id = id
    self.schema = schema
    self.file_format = file_format
    
  @staticmethod
  def from_dict(reader:dict[str, Any]) -> 'StmtReader':
    return StmtReader(
      id=StmtReaderId.from_dict(reader['id']),
      schema=StmtSchema.from_dict(reader['schema']),
      file_format=reader['file_format']
    )
    
  def read_statements(self, statements:Statements) -> pd.DataFrame:
    df = read_all_stmt_files_into_df(statements.files, self.schema, statements.account_number)
    df = self.__adapt_stmt_to_mapped_schema(statements, df)
    return df
  
  def __adapt_stmt_to_mapped_schema(self, statements:Statements, df:pd.DataFrame) -> pd.DataFrame:
    return self.schema.adapter_type.mapper.adapt_to_mapped_schema(df, statements, self.schema)

class StmtReaderFactory:
  def __init__(self, readers:dict[tuple, StmtReader]):
    self.readers = readers
    
  @staticmethod
  def load_from(file_path:str) -> 'StmtReaderFactory':
    with open(file_path, mode='r') as f:
      std_readers = json.load(f)
    list_of_readers = [StmtReader.from_dict(r) for r in std_readers['readers']]
    readers:dict[tuple, StmtReader] = {}
    for reader in list_of_readers:
      readers[(reader.id.account_type, reader.id.institution, reader.id.version)] = reader
    return StmtReaderFactory(readers)
  
  def find_reader_for_statements(self, statements:Statements) -> StmtReader:
    reader = self.readers[(statements.account_type, statements.institution, statements.reader_version)]
    if not all([file.endswith(reader.file_format) for file in statements.file_paths()]):
      raise TypeError(f'The reader allocated for the following files can only read {reader.file_format} files: {statements.file_paths()}')
    return reader

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
  start_row:int = -1
  for i, row in ndf.iterrows():
    row_normalized = [str(cell).strip().lower() for cell in row]
    if all(header in row_normalized for header in normalized_tgt_hdrs):
      start_row = i
  if start_row == -1:
    return None
  ndf = ndf.iloc[start_row:]
  ndf = ndf.reset_index(drop=True)
  ndf = ndf.T.drop_duplicates().T
  ndf.columns = ndf.iloc[0]
  ndf = ndf[1:]
  ndf = ndf[target_headers]
  ndf = ndf.reset_index(drop=True)
  return ndf

def adapt_value_to_column(value:Any, column:StmtColumn):
  match column.data_type:
    case StmtColType.TEXT:
      return value if pd.isna(value) else str(value)
    case StmtColType.DATE:
      if column.date_format is None:
        raise ValueError(f'Column {column.name} is of DATE type, but no date format was specified')
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
            table = [[cell.replace('\n', ' ') for cell in row if cell is not None] for row in table]
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