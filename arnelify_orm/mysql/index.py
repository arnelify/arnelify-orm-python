import cffi
import json
import os

from .query.index import MySQLQuery

class MySQL:
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
      "ORM_MAX_CONNECTIONS",
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

      void orm_free(cPtr);
      void orm_mysql_close();
      void orm_mysql_connect();
      void orm_mysql_create(cOpts);
      void orm_mysql_destroy();
      const char* orm_mysql_exec(cQuery, cBindings);
      const char* orm_mysql_get_uuid();
    """)

    self.opts: str = json.dumps(opts, separators=(',', ':'))
    cOpts = self.ffi.new("char[]", self.opts.encode('utf-8'))
    self.lib.orm_mysql_create(cOpts)

  def foreignKeyChecks(self, on: bool = True) -> None:
    builder: MySQLQuery = MySQLQuery()
    builder.setGetUuIdCallback(self.getUuId)
    
    def onQuery(query, bindings):
      return self.exec(query, bindings)
    
    builder.onQuery(onQuery)
    builder.foreignKeyChecks(on)

  def alterTable(self, tableName: str, condition: callable) -> None:
    builder: MySQLQuery = MySQLQuery()
    builder.setGetUuIdCallback(self.getUuId)
    
    def onQuery(query, bindings):
      return self.exec(query, bindings)
    
    builder.onQuery(onQuery)
    builder.alterTable(tableName, condition)

  def createTable(self, tableName: str, condition: callable) -> None:
    builder: MySQLQuery = MySQLQuery()
    builder.setGetUuIdCallback(self.getUuId)
    
    def onQuery(query, bindings):
      return self.exec(query, bindings)
    
    builder.onQuery(onQuery)
    builder.createTable(tableName, condition)

  def close(self):
    self.lib.orm_mysql_close()

  def connect(self):
    self.lib.orm_mysql_connect()

  def destroy(self) -> None:
    self.lib.orm_mysql_destroy()

  def dropTable(self, tableName: str, args: list[str] = []) -> None:
    builder: MySQLQuery = MySQLQuery()
    builder.setGetUuIdCallback(self.getUuId)
    
    def onQuery(query, bindings):
      return self.exec(query, bindings)
    
    builder.onQuery(onQuery)
    builder.dropTable(tableName, args)

  def exec(self, query: str | None = None, bindings: list[str] = []) -> list[dict]:
    res: list[dict] = {}
    fBindings: str = json.dumps(bindings, separators=(',', ':'))
    cQuery = self.ffi.new("char[]", query.encode('utf-8'))
    cBindings = self.ffi.new("char[]", fBindings.encode('utf-8'))
    cRes = self.lib.orm_mysql_exec(cQuery, cBindings)
    raw = self.ffi.string(cRes).decode('utf-8')

    try:
      res = json.loads(raw)
    except Exception:
      self.logger('Res must be a valid JSON.', True)

    self.lib.orm_free(cRes)
    return res
  
  def getUuId(self) -> str:
    cUuId = self.lib.orm_mysql_get_uuid()
    uuid: str = self.ffi.string(cUuId).decode('utf-8')
    self.lib.orm_free(cUuId)
    return uuid
  
  def logger(self, message: str, isError: bool) -> None:
    if isError:
        print(f"[Arnelify ORM]: Python error: {message}")
        return
    
    print(f"[Arnelify ORM]: {message}")

  def table(self, tableName: str) -> MySQLQuery:
    builder: MySQLQuery = MySQLQuery()
    builder.setGetUuIdCallback(self.getUuId)
    
    def onQuery(query, bindings):
      return self.exec(query, bindings)
    
    builder.onQuery(onQuery)
    return builder.table(tableName)

  def toJson(self, res: dict[str, str]) -> str:
    return json.dumps(res, separators=(',', ':'))