class Column:
  account_number = 'account_number'
  date = 'date'
  day_seq = 'day_seq'
  description = 'description'
  deposited = 'deposited'
  withdrawn = 'withdrawn'
  net_amount = 'net_amount'
  balance = 'balance'

class MappedSchema:
  @staticmethod
  def columns() -> list[str]:
    return [
      Column.account_number,
      Column.date,
      Column.day_seq,
      Column.description,
      Column.deposited,
      Column.withdrawn,
      Column.net_amount,
      Column.balance
    ]