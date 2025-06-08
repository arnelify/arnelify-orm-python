class MySQLQuery:

  def __init__(self):

    def callback(query: str, bindings: list) -> list[dict]:
      res: list[dict] = []
      print(query)
      return res

    def getUuIdCallback() -> str:
      return ''

    self.hasHaving: bool = False
    self.hasOn: bool = False
    self.hasWhere: bool = False
      
    self.bindings: list = []
    self.columns: list = []
    self.indexes: list = []
    self.query: str = ""

    self.callback = callback
    self.getUuIdCallback = getUuIdCallback

  def condition(self, bind: bool, column: str, arg2: None | int | float | str = None, arg3: None | int | float | str = None) -> None:
    if self.isOperator(arg2):
      operator_ = str(arg2)
      if arg3 is None:
        self.query += f"{column} IS NULL"
        return

      if isinstance(arg3, (int, float)):
        if bind:
          self.query += f"{column} {operator_} ?"
          self.bindings.append(str(arg3))
          return
        
        self.query += f"{column} {operator_} {arg3}"
        return

      if bind:
        self.query += f"{column} {operator_} ?"
        self.bindings.append(arg3)
        return
      
      self.query += f"{column} {operator_} {arg3}"
      return

    if arg2 is None:
      self.query += f"{column} IS NULL"
      return

    if isinstance(arg2, (int, float)):
      if bind:
        self.query += f"{column} = ?"
        self.bindings.append(str(arg2))
        return
      
      self.query += f"{column} = {arg2}"
      return

    if bind:
      self.query += f"{column} = ?"
      self.bindings.append(arg2)
      return
    
    self.query += f"{column} = {arg2}"

  def isOperator(self, operator_: str | int | None) -> bool:
    if not isinstance(operator_, str):
      return False
    
    operators = ['=', '!=', '<=', '>=', '<', '>', 'IN', 'BETWEEN', 'LIKE', '<>']
    return operator_ in operators

  def alterTable(self, tableName: str, condition: callable) -> None:
    self.query = f"ALTER TABLE {tableName} "
    condition(self)

    for i, column in enumerate(self.columns):
      if i > 0:
        self.query += ', '
      self.query += column

    if self.indexes:
      self.query += ', '
    for i, index in enumerate(self.indexes):
      if i > 0:
        self.query += ', '
      self.query += index

    self.exec()

  def column(self, name: str, type_: str, default_: None | int | float | bool | str = False, after: str | None = None, collation: str | None = None) -> None:

    query: str = f"{name} {type_}"
    isAlter: str = self.query.startswith('ALTER')
    if isAlter:
      query = f"ADD COLUMN {name} {type_}"

    if default_ is None:
      query += ' DEFAULT NULL'

    if isinstance(default_, bool):
      if default_:
        query += ' DEFAULT NULL'
      else:
        query += ' NOT NULL'

    elif isinstance(default_, (int, float)):
      query += f" NOT NULL DEFAULT {default_}"

    elif isinstance(default_, str):
      if default_ == 'CURRENT_TIMESTAMP':
        query += ' NOT NULL DEFAULT CURRENT_TIMESTAMP'
      else:
        query += f" NOT NULL DEFAULT '{default_}'"

    if collation:
        query += f" COLLATE {collation}"

    if after:
        query += f" AFTER {after}"

    self.columns.append(query)

  def createTable(self, table_name: str, condition: callable) -> None:
    self.query += f"CREATE TABLE {table_name} ("
    condition(self)

    for i, column in enumerate(self.columns):
      if i > 0:
        self.query += ', '
      self.query += column

    if self.indexes:
      self.query += ', '
    for i, index in enumerate(self.indexes):
      if i > 0:
        self.query += ', '
      self.query += index

    self.query += ')'
    self.exec()

  def delete_(self) -> 'MySQLQuery':
    self.query = f"DELETE FROM {self.tableName}"
    return self

  def distinct(self, args: list[str] = []) -> 'MySQLQuery':
    if not args:
        self.query = f"SELECT DISTINCT * FROM {self.tableName}"
        return self

    self.query = "SELECT DISTINCT "
    for i, arg in enumerate(args):
        if i > 0:
            self.query += ', '
        self.query += arg

    self.query += f" FROM {self.tableName}"
    return self

  def dropColumn(self, name: str, args: list[str] = []) -> None:
    query = f"DROP COLUMN {name}"
    for arg in args:
      query += f" {arg}"

    self.columns.append(query)

  def dropConstraint(self, name: str) -> None:
    self.query += f"DROP CONSTRAINT {name}"

  def dropIndex(self, name: str) -> None:
    self.query += f"DROP INDEX {name}"

  def dropTable(self, tableName: str, args: list[str] = []) -> None:
    self.query = f"DROP TABLE IF EXISTS {tableName}"
    for arg in args:
        self.query += f" {arg}"

    self.exec()

  def exec(self, query: str | None = None, bindings: list[str] = []) -> list[dict]:
    res: list[dict] = []
    if query:
      res = self.callback(query, bindings)

    else:
      res = self.callback(self.query, self.bindings)

    self.hasHaving = False
    self.hasOn = False
    self.hasWhere = False

    self.bindings = []
    self.tableName = ''
    self.columns = []
    self.indexes = []
    self.query = ''

    return res

  def foreignKeyChecks(self, on: bool = True) -> None:
    if on:
      self.exec('SET foreign_key_checks = 1;')
      return
    
    self.exec('SET foreign_key_checks = 0;')

  def getUuId(self) -> str:
    return self.getUuIdCallback()
  
  def groupBy(self, args: list[str] = []) -> 'MySQLQuery':
    self.query += " GROUP BY "
    for i, arg in enumerate(args):
        if i > 0:
            self.query += ', '
        self.query += arg

    return self

  def having(self, arg1, arg2: None | int | float | str = None, arg3: None | int | float | str = None) -> 'MySQLQuery':
    if callable(arg1):
      if self.hasHaving:
        if self.query.endswith(')'):
          self.query += ' AND '
      else:
        self.query += ' HAVING '
        self.hasHaving = True

      self.query += '('
      arg1(self)
      self.query += ')'
      return self

    if self.hasHaving:
      if self.query.endswith('?'):
        self.query += ' AND '
    else:
      self.query += ' HAVING '
      self.hasHaving = True

    self.condition(True, arg1, arg2, arg3)
    return self

  def insert(self, args: dict[str, any]) -> dict[str, str]:
    self.query = f"INSERT INTO {self.tableName}"
    columns = ''
    values = ''

    first: bool = True
    for key, value in args.items():
      if first:
        first = False
      else:
        columns += ', '
        values += ', '

      columns += key
      if value is None:
        values += 'NULL'

      elif isinstance(value, (int, float)):
        self.bindings.append(str(value))
        values += '?'

      elif isinstance(value, str):
        self.bindings.append(value)
        values += '?'

    self.query += f" ({columns}) VALUES ({values})"
    return self.exec()

  def index(self, type_: str, args: list[str] = []) -> None:
    query: str = f"{type_} idx"
    isAlter: bool = self.query.startswith('ALTER')
    if isAlter:
      query = f"ADD {type_} idx"

    for arg in args:
      query += f"_{arg}"

    query += ' ('
    for i, arg in enumerate(args):
      if i > 0:
        query += ', '
      query += arg

    query += ')'
    self.bindings.append(query)

  def join(self, table_name: str) -> 'MySQLQuery':
    self.hasOn = False
    self.query += f" JOIN {table_name}"
    return self

  def limit(self, limit_: int, offset: int = 0) -> list[dict]:
    if offset > 0:
      self.query += f" LIMIT {offset}, {limit_}"
    else:
      self.query += f" LIMIT {limit_}"
    return self.exec()

  def leftJoin(self, table_name: str) -> 'MySQLQuery':
    self.hasOn = False
    self.query += f" LEFT JOIN {table_name}"
    return self

  def offset(self, offset: int) -> 'MySQLQuery':
    self.query += f" OFFSET {offset}"
    return self
  
  def on(self, arg1, arg2: None | int | float | str = None, arg3: None | int | float | str = None) -> 'MySQLQuery':
    if callable(arg1):
      if self.hasOn:
        if self.query.endswith(')'):
          self.query += ' AND '
      else:
        self.query += ' ON '
        self.hasOn = True

      self.query += '('
      arg1(self)
      self.query += ')'
      return self

    if self.hasOn:
        if self.query.endswith('?'):
            self.query += ' AND '
    else:
        self.query += ' ON '
        self.hasOn = True

    self.condition(False, arg1, arg2, arg3)
    return self

  def onQuery(self, callback: callable) -> None:
    self.callback = callback

  def orderBy(self, column: str, arg2: str) -> 'MySQLQuery':
    self.query += f" ORDER BY {column} {arg2}"
    return self

  def orHaving(self, arg1, arg2: None | int | float | str = None, arg3: None | int | float | str = None) -> 'MySQLQuery':
    if callable(arg1):
      if self.hasHaving:
        if self.query.endswith(')'):
          self.query += ' OR '
      else:
        self.query += ' HAVING '
        self.hasHaving = True

      self.query += '('
      arg1(self)
      self.query += ')'
      return self

    if self.hasHaving:
      if self.query.endswith('?'):
        self.query += ' OR '
    else:
      self.query += ' HAVING '
      self.hasHaving = True

    self.condition(True, arg1, arg2, arg3)
    return self

  def orOn(self, arg1, arg2: None | int | float | str = None, arg3: None | int | float | str = None) -> 'MySQLQuery':
    if callable(arg1):
      if self.hasOn:
        if self.query.endswith(')'):
          self.query += ' OR '
      else:
        self.query += ' ON '
        self.hasOn = True

      self.query += '('
      arg1(self)
      self.query += ')'
      return self

    if self.hasOn:
      if self.query.endswith('?'):
        self.query += ' OR '
    else:
      self.query += ' ON '
      self.hasOn = True

    self.condition(False, arg1, arg2, arg3)
    return self

  def orWhere(self, arg1, arg2: None | int | float | str = None, arg3: None | int | float | str = None) -> 'MySQLQuery':
    if callable(arg1):
      if self.hasWhere:
        if self.query.endswith(')'):
          self.query += ' OR '
      else:
        self.query += ' WHERE '
        self.hasWhere = True

      self.query += '('
      arg1(self)
      self.query += ')'
      return self

    if self.hasWhere:
      if self.query.endswith('?') or self.query.endswith('IS NULL'):
        self.query += ' OR '
    else:
      self.query += ' WHERE '
      self.hasWhere = True

    self.condition(True, arg1, arg2, arg3)
    return self

  def reference(self, column: str, table_name: str, foreign: str, args: list[str] = []) -> None:
    query: str = f"CONSTRAINT fk_{table_name}_{self.getUuId()} FOREIGN KEY ({column}) REFERENCES {table_name}({foreign})"

    isAlter: bool = self.query.startswith('ALTER')
    if isAlter:
        query = f"ADD CONSTRAINT fk_{table_name}_{self.getUuId()} FOREIGN KEY ({column}) REFERENCES {table_name}({foreign})"

    for arg in args:
        query += f" {arg}"

    self.indexes.append(query)

  def rightJoin(self, table_name: str) -> 'MySQLQuery':
    self.hasOn = False
    self.query += f" RIGHT JOIN {table_name}"
    return self

  def select(self, args: list[str] = []) -> 'MySQLQuery':
    if not args:
        self.query = f"SELECT * FROM {self.tableName}"
        return self

    self.query = 'SELECT '
    for i, arg in enumerate(args):
        if i > 0:
            self.query += ', '
        self.query += arg

    self.query += f" FROM {self.tableName}"
    return self

  def setGetUuIdCallback(self, callback: callable) -> None:
    self.getUuIdCallback = callback

  def table(self, table_name: str) -> 'MySQLQuery':
    self.tableName = table_name
    return self

  def update(self, args: dict[str, any]) -> 'MySQLQuery':
    self.query = f"UPDATE {self.tableName} SET "
    
    first: bool = True
    for key, value in args.items():
      if first:
        first = False
      else:
        self.query += ', '

      if value is None:
        self.query += f"{key} = NULL"
      elif isinstance(value, (int, float)):
        self.bindings.append(str(value))
        self.query += f"{key} = ?"
      elif isinstance(value, str):
        self.bindings.append(value)
        self.query += f"{key} = ?"

    return self

  def where(self, arg1, arg2: str | int | None = None, arg3: str | int | None = None) -> 'MySQLQuery':
    if callable(arg1):
      if self.hasWhere:
        if self.query.endswith(')'):
          self.query += ' AND '
      else:
        self.query += ' WHERE '
        self.hasWhere = True

      self.query += '('
      arg1(self)
      self.query += ')'
      return self

    if self.hasWhere:
      if self.query.endswith('?') or self.query.endswith('IS NULL'):
        self.query += ' AND '
    else:
      self.query += ' WHERE '
      self.hasWhere = True

    self.condition(True, arg1, arg2, arg3)
    return self