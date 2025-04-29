#ifndef ARNELIFY_ORM_MYSQL_H
#define ARNELIFY_ORM_MYSQL_H

#include <iostream>
#include <queue>

#include "json.h"

#include "driver/index.h"
#include "query/index.h"

#include "contracts/opts.h"

class MySQL {
 private:
  int connections;

  MySQLOpts opts;
  std::queue<MySQLDriver*> pool;
  std::vector<MySQLQuery*> trash;

  std::function<void(const std::string&, const bool&)> logger =
      [](const std::string& message, const bool& isError) {
        if (isError) {
          std::cout << "[Arnelify ORM]: Error" << message << std::endl;
          return;
        }

        std::cout << "[Arnelify ORM]: " << message << std::endl;
      };

  MySQLDriver* getDriver() {
    MySQLDriver* driver = nullptr;

    while (driver == nullptr) {
      if (!this->pool.empty()) {
        driver = this->pool.front();
        this->pool.pop();
      }
    }

    return driver;
  }

 public:
  MySQL(const MySQLOpts& o) : connections(0), opts(o) {}

  ~MySQL() { this->close(); }

  void alterTable(
      const std::string& tableName,
      const std::function<void(MySQLQuery*)>& condition =
          [](MySQLQuery* query) {}) {
    MySQLQuery* builder = new MySQLQuery();
    builder->onQuery([this, builder](const std::string& query,
                                     const std::vector<std::string>& bindings) {
      this->trash.push_back(builder);
      return this->exec(query, bindings);
    });

    builder->alterTable(tableName, condition);
  }

  void createTable(
      const std::string& tableName,
      const std::function<void(MySQLQuery*)>& condition =
          [](MySQLQuery* query) {}) {
    MySQLQuery* builder = new MySQLQuery();
    builder->onQuery([this, builder](const std::string& query,
                                     const std::vector<std::string>& bindings) {
      this->trash.push_back(builder);
      return this->exec(query, bindings);
    });

    builder->createTable(tableName, condition);
  }

  void close() {
    this->connections--;
    for (MySQLQuery* builder : this->trash) {
      delete builder;
    }

    this->trash.clear();
    const bool isLimit = this->connections >= this->opts.ORM_MAX_CONNECTIONS;
    if (!isLimit) {
      while (!this->pool.empty()) {
        MySQLDriver* driver = this->pool.front();
        delete driver;
        this->pool.pop();
        return;
      }
    }
  }

  void connect() {
    this->connections++;

    const bool isPoolLimit =
        this->pool.size() >= this->opts.ORM_MAX_CONNECTIONS;
    if (!isPoolLimit) {
      MySQLDriver* driver = new MySQLDriver(
          this->opts.ORM_HOST, this->opts.ORM_NAME, this->opts.ORM_USER,
          this->opts.ORM_PASS, this->opts.ORM_PORT);
      this->pool.push(driver);
    }
  }

  void dropTable(const std::string& tableName,
                 const std::vector<std::string> args = {}) {
    MySQLQuery* builder = new MySQLQuery();
    builder->onQuery([this, builder](const std::string& query,
                                     const std::vector<std::string>& bindings) {
      this->trash.push_back(builder);
      return this->exec(query, bindings);
    });

    builder->dropTable(tableName, args);
  }

  const MySQLRes exec(const std::string& query,
                      const std::vector<std::string>& bindings = {}) {
    MySQLRes res;
    MySQLDriver* driver = this->getDriver();
    res = driver->exec(query, bindings);
    this->pool.push(driver);
    return res;
  }

  const std::string getUuId() {
    MySQLQuery builder;
    return builder.getUuId();
  }

  MySQLQuery* table(const std::string& tableName) {
    MySQLQuery* builder = new MySQLQuery();
    builder->onQuery([this, builder](const std::string& query,
                                     const std::vector<std::string>& bindings) {
      this->trash.push_back(builder);
      return this->exec(query, bindings);
    });

    return builder->table(tableName);
  }

  const Json::Value toJson(const MySQLRes& res) {
    Json::Value json = Json::arrayValue;
    for (const MySQLRow& row : res) {
      Json::Value item;

      for (auto& [key, value] : row) {
        if (std::holds_alternative<std::nullptr_t>(value)) {
          item[key] = Json::nullValue;
          continue;
        }

        item[key] = std::get<std::string>(value);
      }

      json.append(item);
    }

    return json;
  }
};

#endif