#ifndef ARNELIFY_ORM_TEST_CPP
#define ARNELIFY_ORM_TEST_CPP

#include <iostream>

#include "json.h"

#include "../index.h"

int main(int argc, char* argv[]) {

  MySQLOpts opts(10, "mysql", "test", "root", "pass", 3306);
  MySQL* db = new MySQL(opts);
  MySQLRes res;

  Json::StreamWriterBuilder writer;
  writer["indentation"] = "";
  writer["emitUTF8"] = true;

  db->connect();
  std::cout << "Connected." << std::endl;

  db->foreignKeyChecks(false);
  db->dropTable("users");
  db->dropTable("posts");
  db->foreignKeyChecks(true);

  db->createTable("users", [](MySQLQuery* query){
    query->column("id", "BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY");
    query->column("email", "VARCHAR(255) UNIQUE", nullptr);
    query->column("created_at", "DATETIME", "CURRENT_TIMESTAMP");
    query->column("updated_at", "DATETIME", nullptr);
  });

  db->createTable("posts", [](MySQLQuery* query){
    query->column("id", "BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY");
    query->column("user_id", "BIGINT UNSIGNED", nullptr);
    query->column("contents", "VARCHAR(2048)", nullptr);
    query->column("created_at", "DATETIME", "CURRENT_TIMESTAMP");
    query->column("updated_at", "DATETIME", "CURRENT_TIMESTAMP");

    query->index("INDEX", {"user_id"});
    query->reference("user_id", "users", "id", {"ON DELETE CASCADE"});
  });
  
  res = db->table("users")
    ->insert({{"email", "email@example.com"}});

  Json::Value insert = db->toJson(res);
  std::cout << "last inserted id: " << Json::writeString(writer, insert) << std::endl;

  res = db->table("users")
    ->select({"id", "email"})
    ->where("id", 1)
    ->limit(1);

  Json::Value select = db->toJson(res);
  std::cout << "inserted row: " << Json::writeString(writer, select) << std::endl;

  db->table("users")
    ->update({{"email", "user@example.com"}})
    ->where("id", 1)
    ->exec();

  db->table("users")
    ->delete_()
    ->where("id", 1)
    ->limit(1);

  db->close();
  std::cout << "Closed." << std::endl;
  delete db;

  return 0;
}

#endif