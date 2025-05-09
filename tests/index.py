from arnelify_orm import MySQL
from arnelify_orm import MySQLQuery

def main() -> int:
  
  res: list[dict] = []
  db: MySQL = MySQL({
    "ORM_MAX_CONNECTIONS": 10,
    "ORM_HOST": "mysql",
    "ORM_NAME": "test",
    "ORM_USER": "root",
    "ORM_PASS": "pass",
    "ORM_PORT": 3306
  })

  db.connect()
  print("Connected.")

  db.foreignKeyChecks(False)
  db.dropTable("users")
  db.dropTable("posts")
  db.foreignKeyChecks(True)

  def users(query: MySQLQuery):
    query.column("id", "BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY")
    query.column("email", "VARCHAR(255) UNIQUE", None)
    query.column("created_at", "DATETIME", "CURRENT_TIMESTAMP")
    query.column("updated_at", "DATETIME", None)
  
  db.createTable("users", users)

  def posts(query: MySQLQuery):
    query.column("id", "BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY")
    query.column("user_id", "BIGINT UNSIGNED", None)
    query.column("contents", "VARCHAR(2048)", None)
    query.column("created_at", "DATETIME", "CURRENT_TIMESTAMP")
    query.column("updated_at", "DATETIME", "CURRENT_TIMESTAMP")

    query.index("INDEX", ["user_id"])
    query.reference("user_id", "users", "id", ["ON DELETE CASCADE"])

  db.createTable("posts", posts)

  res = db.table("users").insert({ "email": "email@example.com" })
  insert: str = db.toJson(res)
  print(f"last inserted id: {insert}")

  res = db.table("users").select(["id", "email"]).where("id", 1).limit(1)
  select: str = db.toJson(res)
  print(f"Inserted row: {select}")
  
  db.table("users").update({ "email": "user@example.com" }).where("id", 1).exec()
  db.table("users").delete_().where("id", 1).limit(1)
  
  db.close()
  print("Closed.")

if __name__ == "__main__":
  main()