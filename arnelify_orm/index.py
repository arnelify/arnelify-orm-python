import cffi
import json
import os

class ArnelifyORM:
  def __init__(self, opts: dict):
    srcDir: str = os.walk(os.path.abspath('venv/lib64'))
    libPaths: list[str] = []
    for root, dirs, files in srcDir:
      for file in files:
        if file.startswith('arnelify-orm') and file.endswith('.so'):
          libPaths.append(os.path.join(root, file))

    self.ffi = cffi.FFI()
    self.lib = self.ffi.dlopen(libPaths[0])

    required: list[str] = [
      "ORM_DRIVER",
      "ORM_HOST",
      "ORM_NAME",
      "ORM_USER",
      "ORM_PASS",
      "ORM_PORT"
    ]

    for key in required:
      if key not in opts:
        print(f"[ArnelifyORM FFI]: Python error: '{key}' is missing")
        exit(1)

    self.ffi.cdef("""
      typedef const char* cOpts;
      typedef const char* cQuery;
      typedef const char* cBindings;
      typedef const char* cPtr;

      void orm_create(cOpts);
      void orm_destroy();
      const char* orm_exec(cQuery, cBindings);
      void orm_free(cPtr);
    """)

    self.opts: str = json.dumps(opts, separators=(',', ':'))
    cOpts = self.ffi.new("char[]", self.opts.encode('utf-8'))

    self.hasHaving: bool = False
    self.hasOn: bool = False
    self.hasWhere: bool = False
    
    self.bindings: list = []
    self.columns: list = []
    self.indexes: list = []
    self.lib.orm_create(cOpts)
    self.query: str = ""

  def condition(self, column: str, arg2: None | int | float | str = None, arg3: None | int | float | str = None) -> None:
    if self.isOperator(arg2):
      operator_ = str(arg2)
      if arg3 is None:
        self.query += f"{column} IS NULL"
        return

      if isinstance(arg3, (int, float)):
        self.query += f"{column} {operator_} {arg3}"
        self.bindings.append(str(arg3))
        return

      self.query += f"{column} {operator_} ?"
      self.bindings.append(arg3)
      return

    if arg2 is None:
      self.query += f"{column} IS NULL"
      return

    if isinstance(arg2, (int, float)):
      self.query += f"{column} = ?"
      self.bindings.append(str(arg2))
      return

    self.query += f"{column} = ?"
    self.bindings.append(arg2)

  def isOperator(self, operator_: str | int | None) -> bool:
    if not isinstance(operator_, str):
      return False
    
    operators = ['=', '!=', '<=', '>=', '<', '>', 'IN', 'BETWEEN', 'LIKE', '<>']
    return operator_ in operators

  def logger(self, message: str, isError: bool) -> None:
    if isError:
        print(f"[Arnelify ORM]: Python error: {message}")
        return
    
    print(f"[Arnelify ORM]: {message}")

  def alertTable(self, tableName: str, condition: callable) -> None:
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
      query += f"{default_}"

    elif isinstance(default_, str):
      if default_ == 'CURRENT_TIMESTAMP':
        query += ' DEFAULT CURRENT_TIMESTAMP'
      else:
        query += f"'{default_}'"

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

  def delete_(self) -> 'ArnelifyORM':
    self.query = f"DELETE FROM {self.tableName}"
    return self

  def destroy(self) -> None:
    self.lib.orm_destroy()

  def distinct(self, args: list[str] = []) -> 'ArnelifyORM':
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
    self.raw('SET foreign_key_checks = 0;')
    self.query = f"DROP TABLE IF EXISTS {tableName}"
    for arg in args:
        self.query += f" {arg}"

    self.exec()
    self.raw('SET foreign_key_checks = 1;')

  def exec(self, query: str | None = None, bindings: list[str] = []) -> list[dict]:
    res: list[dict] = {}
    if query is None:
      serialized: str = json.dumps(self.bindings, separators=(',', ':'))
      cQuery = self.ffi.new("char[]", self.query.encode('utf-8'))
      cBindings = self.ffi.new("char[]", serialized.encode('utf-8'))
      cRes = self.lib.orm_exec(cQuery, cBindings)
      raw = self.ffi.string(cRes).decode('utf-8')

      try:
        res = json.loads(raw)
      except Exception:
        self.logger('Res must be a valid JSON.', True)

      self.lib.orm_free(cRes)

    else:
      serialized: str = json.dumps(bindings, separators=(',', ':'))
      cQuery = self.ffi.new("char[]", query.encode('utf-8'))
      cBindings = self.ffi.new("char[]", serialized.encode('utf-8'))
      cRes = self.lib.orm_exec(cQuery, cBindings)
      raw = self.ffi.string(cRes).decode('utf-8')

      try:
        res = json.loads(raw)
      except Exception:
        self.logger('Res must be a valid JSON.', True)

      self.lib.orm_free(cRes)

    self.hasHaving = False
    self.hasOn = False
    self.hasWhere = False

    self.bindings = []
    self.tableName = ''
    self.columns = []
    self.indexes = []
    self.query = ''

    return res

  def groupBy(self, args: list[str] = []) -> 'ArnelifyORM':
    self.query += " GROUP BY "
    for i, arg in enumerate(args):
        if i > 0:
            self.query += ', '
        self.query += arg

    return self

  def having(self, arg1, arg2: None | int | float | str = None, arg3: None | int | float | str = None) -> 'ArnelifyORM':
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

    self.condition(arg1, arg2, arg3)
    return self

  def insert(self, args: dict[str, any]) -> dict[str, str]:
    self.query = f"INSERT INTO {self.tableName}"
    columns = ''
    values = ''

    first: bool = True
    for key, value in args.items():
      if not first:
        columns += ', '
        values += ', '
        first = False

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

  def join(self, table_name: str) -> 'ArnelifyORM':
    self.query += f" JOIN {table_name}"
    return self

  def limit(self, limit_: int, offset: int = 0) -> list[dict]:
    if offset > 0:
      self.query += f" LIMIT {offset}, {limit_}"
    else:
      self.query += f" LIMIT {limit_}"
    return self.exec()

  def leftJoin(self, table_name: str) -> 'ArnelifyORM':
    self.query += f" LEFT JOIN {table_name}"
    return self

  def on(self, arg1, arg2: None | int | float | str = None, arg3: None | int | float | str = None) -> 'ArnelifyORM':
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

    self.condition(arg1, arg2, arg3)
    return self

  def offset(self, offset: int) -> 'ArnelifyORM':
    self.query += f" OFFSET {offset}"
    return self

  def orderBy(self, column: str, arg2: str) -> 'ArnelifyORM':
    self.query += f" ORDER BY {column} {arg2}"
    return self

  def orHaving(self, arg1, arg2: None | int | float | str = None, arg3: None | int | float | str = None) -> 'ArnelifyORM':
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

    self.condition(arg1, arg2, arg3)
    return self

  def orOn(self, arg1, arg2: None | int | float | str = None, arg3: None | int | float | str = None) -> 'ArnelifyORM':
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

    self.condition(arg1, arg2, arg3)
    return self

  def orWhere(self, arg1, arg2: None | int | float | str = None, arg3: None | int | float | str = None) -> 'ArnelifyORM':
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
      if self.query.endswith('?'):
        self.query += ' OR '
    else:
      self.query += ' WHERE '
      self.hasWhere = True

    self.condition(arg1, arg2, arg3)
    return self

  def raw(self, query: str) -> dict[str, str]:
    self.query = query
    return self.exec()

  def reference(self, column: str, table_name: str, foreign: str, args: list[str] = []) -> None:
    query: str = f"CONSTRAINT fk_{table_name} FOREIGN KEY ({column}) REFERENCES {table_name}({foreign})"

    isAlter: bool = self.query.startswith('ALTER')
    if isAlter:
        query = f"ADD CONSTRAINT fk_{table_name} FOREIGN KEY ({column}) REFERENCES {table_name}({foreign})"

    for arg in args:
        query += f" {arg}"

    self.indexes.append(query)

  def rightJoin(self, table_name: str) -> 'ArnelifyORM':
    self.query += f" RIGHT JOIN {table_name}"
    return self

  def select(self, args: list[str] = []) -> 'ArnelifyORM':
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

  def table(self, table_name: str) -> 'ArnelifyORM':
    self.tableName = table_name
    return self

  def toJson(self, res: dict[str, str]) -> str:
    return json.dumps(res, separators=(',', ':'))

  def update(self, args: dict[str, any]) -> 'ArnelifyORM':
    self.query = f"UPDATE {self.tableName} SET "
    
    first: bool = True
    for key, value in args.items():
      if not first:
        self.query += ', '
        first = False

      if value is None:
        self.query += f"{key} IS NULL"
      elif isinstance(value, (int, float)):
        self.bindings.append(str(value))
        self.query += f"{key} = ?"
      elif isinstance(value, str):
        self.bindings.append(value)
        self.query += f"{key} = ?"

    return self

  def where(self, arg1, arg2: str | int | None = None, arg3: str | int | None = None) -> 'ArnelifyORM':
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
      if self.query.endswith('?'):
        self.query += ' AND '
    else:
      self.query += ' WHERE '
      self.hasWhere = True

    self.condition(arg1, arg2, arg3)
    return self