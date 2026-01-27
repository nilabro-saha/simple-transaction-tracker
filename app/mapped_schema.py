class Column:
  ACCOUNT_NUMBER = 'account_number'
  DATE = 'date'
  DAY_SEQ = 'day_seq'
  DESCRIPTION = 'description'
  DEPOSITED = 'deposited'
  WITHDRAWN = 'withdrawn'
  NET_AMOUNT = 'net_amount'
  BALANCE = 'balance'

class MappedSchema:
  @staticmethod
  def columns() -> list[str]:
    return [
      Column.ACCOUNT_NUMBER,
      Column.DATE,
      Column.DAY_SEQ,
      Column.DESCRIPTION,
      Column.DEPOSITED,
      Column.WITHDRAWN,
      Column.NET_AMOUNT,
      Column.BALANCE
    ]