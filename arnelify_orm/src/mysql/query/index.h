#ifndef ARNELIFY_ORM_MYSQL_QUERY_H
#define ARNELIFY_ORM_MYSQL_QUERY_H

#include <functional>
#include <future>
#include <iostream>
#include <map>
#include <vector>

#include <iomanip>
#include <random>
#include <sstream>
#include <string>
#include <optional>
#include <map>
#include <queue>
#include <variant>
#include <vector>

#include "json.h"

#include "contracts/res.h"

class MySQLQuery {
 private:
  bool hasHaving;
  bool hasOn;
  bool hasWhere;

  std::vector<std::string> bindings;
  std::string tableName;
  std::vector<std::string> columns;
  std::vector<std::string> indexes;
  std::string query;

  std::function<MySQLRes(const std::string&, const std::vector<std::string>&)>
      callback = [](const std::string& query,
                    const std::vector<std::string>& bindings) {
        MySQLRes res = {};
        std::cout << query << std::endl;
        return res;
      };

  const bool isOperator(
      const std::variant<std::nullptr_t, int, double, std::string> arg) {
    if (!std::holds_alternative<std::string>(arg)) return false;
    const std::vector<std::string> operators = {
        "=", "!=", "<=", ">=", "<", ">", "IN", "BETWEEN", "LIKE", "<>"};
    const std::string& operator_ = std::get<std::string>(arg);
    auto it = std::find(operators.begin(), operators.end(), operator_);
    if (it != operators.end()) return true;
    return false;
  }

  const void condition(
      const bool bind, const std::string& column,
      const std::variant<std::nullptr_t, int, double, std::string>& arg2,
      const std::variant<std::nullptr_t, int, double, std::string>& arg3) {
    if (this->isOperator(arg2)) {
      const std::string operator_ = std::get<std::string>(arg2);
      if (std::holds_alternative<std::nullptr_t>(arg3)) {
        this->query += column + " IS NULL";
        return;
      }

      if (std::holds_alternative<int>(arg3)) {
        const std::string value = std::to_string(std::get<int>(arg3));
        if (bind) {
          this->query += column + " " + operator_ + " ?";
          this->bindings.emplace_back(value);
          return;
        }

        this->query += column + " " + operator_ + " " + value;
        return;
      }

      if (std::holds_alternative<double>(arg3)) {
        const std::string value = std::to_string(std::get<double>(arg3));
        if (bind) {
          this->query += column + " " + operator_ + " ?";
          this->bindings.emplace_back(value);
          return;
        }

        this->query += column + " " + operator_ + " " + value;
      }

      const std::string value = std::get<std::string>(arg3);
      if (bind) {
        this->query += column + " " + operator_ + " ?";
        this->bindings.emplace_back(value);
        return;
      }

      this->query += column + " " + operator_ + " " + value;
    }

    if (std::holds_alternative<std::nullptr_t>(arg2)) {
      this->query += column + " IS NULL";
      return;
    }

    if (std::holds_alternative<int>(arg2)) {
      const std::string value = std::to_string(std::get<int>(arg2));
      if (bind) {
        this->query += column + " = ?";
        this->bindings.emplace_back(value);
        return;
      }

      this->query += column + " = " + value;
    }

    if (std::holds_alternative<double>(arg2)) {
      const std::string value = std::to_string(std::get<double>(arg2));
      if (bind) {
        this->query += column + " = ?";
        this->bindings.emplace_back(value);
        return;
      }

      this->query += column + " = " + value;
    }

    const std::string value = std::get<std::string>(arg2);
    if (bind) {
      this->query += column + " = ?";
      this->bindings.emplace_back(value);
    }

    this->query += column + " = " + value;
  }

 public:
  MySQLQuery() : hasHaving(false), hasOn(false), hasWhere(false) {}

  void alterTable(
      const std::string& tableName,
      const std::function<void(MySQLQuery*)>& condition =
          [](MySQLQuery* query) {}) {
    this->query = "ALTER TABLE " + tableName + " ";
    condition(this);

    for (size_t i = 0; this->columns.size() > i; i++) {
      if (i > 0) this->query += ", ";
      this->query += this->columns[i];
    }

    if (this->indexes.size()) this->query += ", ";
    for (size_t i = 0; this->indexes.size() > i; i++) {
      if (i > 0) this->query += ", ";
      this->query += this->indexes[i];
    }

    this->exec();
  }

  void column(const std::string& name, const std::string& type,
              const std::variant<std::nullptr_t, int, double, bool,
                                 std::string>& default_ = false,
              const std::optional<std::string>& after = std::nullopt,
              const std::optional<std::string>& collation = std::nullopt) {
    std::string query = name + " " + type;
    const bool isAlter = this->query.starts_with("ALTER");
    if (isAlter) query = "ADD COLUMN " + name + " " + type;
    if (std::holds_alternative<std::nullptr_t>(default_)) {
      query += " DEFAULT NULL";
    } else if (std::holds_alternative<bool>(default_)) {
      const bool value = std::get<bool>(default_);
      query += " " + std::string(value ? "DEFAULT NULL" : "NOT NULL");
    } else if (std::holds_alternative<double>(default_)) {
      query +=
          " NOT NULL DEFAULT " + std::to_string(std::get<double>(default_));
    } else if (std::holds_alternative<int>(default_)) {
      query += " NOT NULL DEFAULT " + std::to_string(std::get<int>(default_));
    } else if (std::holds_alternative<std::string>(default_)) {
      const std::string value = std::get<std::string>(default_);
      if (value == "CURRENT_TIMESTAMP") {
        query += " NOT NULL DEFAULT CURRENT_TIMESTAMP";
      } else {
        query += " NOT NULL DEFAULT '" + value + "'";
      }
    }

    if (collation.has_value()) query += " COLLATE " + collation.value();
    if (after.has_value()) query += " AFTER " + after.value();
    this->columns.emplace_back(query);
  }

  void createTable(
      const std::string& tableName,
      const std::function<void(MySQLQuery*)>& condition =
          [](MySQLQuery* query) {}) {
    this->query = "CREATE TABLE " + tableName + " (";
    condition(this);
    for (size_t i = 0; this->columns.size() > i; i++) {
      if (i > 0) this->query += ", ";
      this->query += this->columns[i];
    }

    if (this->indexes.size()) this->query += ", ";
    for (size_t i = 0; this->indexes.size() > i; i++) {
      if (i > 0) this->query += ", ";
      this->query += this->indexes[i];
    }

    this->query += ")";
    this->exec();
  }

  MySQLQuery* delete_() {
    this->query = "DELETE FROM " + this->tableName;
    return this;
  }

  MySQLQuery* distinct(const std::vector<std::string>& args = {}) {
    if (!args.size()) {
      this->query = "SELECT DISTINCT * FROM " + this->tableName;
      return this;
    }

    this->query = "SELECT DISTINCT ";
    for (size_t i = 0; args.size() > i; i++) {
      if (i > 0) this->query += ", ";
      this->query += args[i];
    }

    this->query += " FROM " + this->tableName;
    return this;
  }

  void dropColumn(const std::string& name,
                  const std::vector<std::string> args = {}) {
    std::string query = "DROP COLUMN " + name;
    for (size_t i = 0; args.size() > i; i++) {
      query += " " + args[i];
    }

    this->columns.emplace_back(query);
  }

  void dropConstraint(std::string& name) {
    this->query += "DROP CONSTRAINT " + name;
  }

  void dropIndex(const std::string& name) {
    this->query += "DROP INDEX " + name;
  }

  void dropTable(const std::string& tableName,
                 const std::vector<std::string> args = {}) {
    this->query = "DROP TABLE IF EXISTS " + tableName;
    for (size_t i = 0; args.size() > i; i++) {
      this->query += " " + args[i];
    }

    this->exec();
  }

  MySQLRes exec() {
    MySQLRes res = this->callback(this->query, this->bindings);

    this->hasHaving = false;
    this->hasOn = false;
    this->hasWhere = false;

    this->bindings.clear();
    this->tableName.clear();
    this->columns.clear();
    this->indexes.clear();
    this->query.clear();

    return res;
  }

  MySQLRes exec(const std::string& query,
                const std::vector<std::string>& bindings = {}) {
    MySQLRes res = this->callback(query, bindings);

    this->hasHaving = false;
    this->hasOn = false;
    this->hasWhere = false;

    this->bindings.clear();
    this->tableName.clear();
    this->columns.clear();
    this->indexes.clear();
    this->query.clear();

    return res;
  }

  void foreignKeyChecks(const bool& on = true) {
    if (on) {
      this->exec("SET foreign_key_checks = 1;");
      return;
    }

    this->exec("SET foreign_key_checks = 0;");
  }

  const std::string getUuId() {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(10000, 19999);
    int random = dis(gen);
    const auto now = std::chrono::system_clock::now();
    const auto milliseconds =
        std::chrono::duration_cast<std::chrono::milliseconds>(
            now.time_since_epoch())
            .count();

    const std::string code =
        std::to_string(milliseconds) + std::to_string(random);
    std::hash<std::string> hasher;
    size_t v1 = hasher(code);
    size_t v2 = hasher(std::to_string(v1));
    unsigned char hash[16];
    for (int i = 0; i < 8; ++i) {
      hash[i] = (v1 >> (i * 8)) & 0xFF;
      hash[i + 8] = (v2 >> (i * 8)) & 0xFF;
    }

    std::stringstream ss;
    for (int i = 0; i < 16; ++i) {
      ss << std::hex << std::setw(2) << std::setfill('0')
         << static_cast<int>(hash[i]);
    }

    return ss.str();
  }

  MySQLQuery* groupBy(const std::vector<std::string>& args) {
    this->query += " GROUP BY ";
    for (size_t i = 0; args.size() > i; i++) {
      if (i > 0) this->query += ", ";
      this->query += args[i];
    }

    return this;
  }

  MySQLQuery* having(const std::function<void(MySQLQuery*)>& condition) {
    if (this->hasHaving) {
      const bool hasCondition = this->query.ends_with(")");
      if (hasCondition) this->query += " AND ";
    } else {
      this->query += " HAVING ";
      this->hasHaving = true;
    }

    this->query += "(";
    condition(this);
    this->query += ")";
    return this;
  }

  MySQLQuery* having(
      const std::string& column,
      const std::variant<std::nullptr_t, int, double, std::string>& arg2,
      const std::variant<std::nullptr_t, int, double, std::string>& arg3 =
          nullptr) {
    if (this->hasHaving) {
      const bool hasCondition = this->query.ends_with("?");
      if (hasCondition) this->query += " AND ";
    } else {
      this->query += " HAVING ";
      this->hasHaving = true;
    }

    this->condition(true, column, arg2, arg3);
    return this;
  }

  MySQLRes insert(const std::map<std::string,
                                 const std::variant<std::nullptr_t, int, double,
                                                    std::string>>& args) {
    this->query = "INSERT INTO " + this->tableName;
    std::stringstream columns;
    std::stringstream values;

    bool first = true;
    for (const auto& [key, value] : args) {
      if (first) {
        first = false;
      } else {
        columns << ", ";
        values << ", ";
      }

      columns << key;
      if (std::holds_alternative<std::nullptr_t>(value)) {
        values << "NULL";
        continue;
      }

      if (std::holds_alternative<int>(value)) {
        const std::string binding = std::to_string(std::get<int>(value));
        this->bindings.emplace_back(binding);
        values << "?";
        continue;
      }

      if (std::holds_alternative<double>(value)) {
        const std::string binding = std::to_string(std::get<double>(value));
        this->bindings.emplace_back(binding);
        values << "?";
        continue;
      }

      if (std::holds_alternative<std::string>(value)) {
        const std::string binding = std::get<std::string>(value);
        this->bindings.emplace_back(binding);
        values << "?";
        continue;
      }
    }

    this->query += " (" + columns.str() + ") VALUES (" + values.str() + ")";
    return this->exec();
  }

  void index(const std::string& type, const std::vector<std::string> args) {
    std::string query = type + " idx";
    const bool isAlter = this->query.starts_with("ALTER");
    if (isAlter) query = "ADD " + type + " idx";

    for (size_t i = 0; args.size() > i; i++) {
      query += "_" + args[i];
    }

    query += " (";
    for (size_t i = 0; args.size() > i; i++) {
      if (i > 0) query += ", ";
      query += args[i];
    }

    query += ")";
    this->indexes.emplace_back(query);
  }

  MySQLQuery* join(const std::string& tableName) {
    this->hasOn = false;
    this->query += " JOIN " + tableName;
    return this;
  }

  MySQLRes limit(const int& limit_, const int& offset = 0) {
    if (offset > 0) {
      this->query +=
          " LIMIT " + std::to_string(offset) + ", " + std::to_string(limit_);
      return this->exec();
    }

    this->query += " LIMIT " + std::to_string(limit_);
    return this->exec();
  }

  MySQLQuery* leftJoin(const std::string& tableName) {
    this->hasOn = false;
    this->query += " LEFT JOIN " + tableName;
    return this;
  }

  MySQLQuery* offset(const int& offset) {
    this->query += " OFFSET " + std::to_string(offset);
    return this;
  }

  MySQLQuery* on(const std::function<void(MySQLQuery*)>& condition) {
    if (this->hasOn) {
      const bool hasCondition = this->query.ends_with(")");
      if (hasCondition) this->query += " AND ";
    } else {
      this->query += " ON ";
      this->hasOn = true;
    }

    this->query += "(";
    condition(this);
    this->query += ")";
    return this;
  }

  MySQLQuery* on(
      const std::string& column,
      const std::variant<std::nullptr_t, int, double, std::string>& arg2,
      const std::variant<std::nullptr_t, int, double, std::string>& arg3 =
          nullptr) {
    if (this->hasOn) {
      const bool hasCondition = this->query.ends_with("?");
      if (hasCondition) this->query += " AND ";
    } else {
      this->query += " ON ";
      this->hasOn = true;
    }

    this->condition(false, column, arg2, arg3);
    return this;
  }

  void onQuery(std::function<MySQLRes(const std::string&,
                                      const std::vector<std::string>&)>
                   callback) {
    this->callback = callback;
  }

  MySQLQuery* orderBy(const std::string& column, const std::string& arg2) {
    this->query += " ORDER BY " + column + " " + arg2;
    return this;
  }

  MySQLQuery* orHaving(const std::function<void(MySQLQuery*)>& condition) {
    if (this->hasHaving) {
      const bool hasCondition = this->query.ends_with(")");
      if (hasCondition) this->query += " OR ";
    } else {
      this->query += " HAVING ";
      this->hasHaving = true;
    }

    this->query += "(";
    condition(this);
    this->query += ")";
    return this;
  }

  MySQLQuery* orHaving(
      const std::string& column,
      const std::variant<std::nullptr_t, int, double, std::string>& arg2,
      const std::variant<std::nullptr_t, int, double, std::string>& arg3 =
          nullptr) {
    if (this->hasHaving) {
      const bool hasCondition = this->query.ends_with("?");
      if (hasCondition) this->query += " OR ";
    } else {
      this->query += " HAVING ";
      this->hasHaving = true;
    }

    this->condition(true, column, arg2, arg3);
    return this;
  }

  MySQLQuery* orOn(const std::function<void(MySQLQuery*)>& condition) {
    if (this->hasOn) {
      const bool hasCondition = this->query.ends_with(")");
      if (hasCondition) this->query += " OR ";
    } else {
      this->query += " ON ";
      this->hasOn = true;
    }

    this->query += "(";
    condition(this);
    this->query += ")";
    return this;
  }

  MySQLQuery* orOn(
      const std::string& column,
      const std::variant<std::nullptr_t, int, double, std::string>& arg2,
      const std::variant<std::nullptr_t, int, double, std::string>& arg3 =
          nullptr) {
    if (this->hasOn) {
      const bool hasCondition = this->query.ends_with("?");
      if (hasCondition) this->query += " OR ";
    } else {
      this->query += " ON ";
      this->hasOn = true;
    }

    this->condition(false, column, arg2, arg3);
    return this;
  }

  MySQLQuery* orWhere(const std::function<void(MySQLQuery*)>& condition) {
    if (this->hasWhere) {
      const bool hasCondition = this->query.ends_with(")");
      if (hasCondition) this->query += " OR ";
    } else {
      this->query += " WHERE ";
      this->hasWhere = true;
    }

    this->query += "(";
    condition(this);
    this->query += ")";
    return this;
  }

  MySQLQuery* orWhere(
      const std::string& column,
      const std::variant<std::nullptr_t, int, double, std::string>& arg2,
      const std::variant<std::nullptr_t, int, double, std::string>& arg3 =
          nullptr) {
    if (this->hasWhere) {
      const bool hasCondition =
          this->query.ends_with("?") || this->query.ends_with("IS NULL");
      if (hasCondition) this->query += " OR ";
    } else {
      this->query += " WHERE ";
      this->hasWhere = true;
    }

    this->condition(true, column, arg2, arg3);
    return this;
  }

  void reference(const std::string& column, const std::string& tableName,
                 const std::string& foreign,
                 const std::vector<std::string> args) {
    std::string query = "CONSTRAINT fk_" + tableName + "_" + this->getUuId() +
                        " FOREIGN KEY (" + column + ") REFERENCES " +
                        tableName + "(" + foreign + ")";

    const bool isAlter = this->query.starts_with("ALTER");
    if (isAlter) {
      query = "ADD CONSTRAINT fk_" + tableName + "_" + this->getUuId() +
              " FOREIGN KEY (" + column + ") REFERENCES " + tableName + "(" +
              foreign + ")";
    }

    for (size_t i = 0; args.size() > i; i++) {
      query += " " + args[i];
    }

    this->indexes.emplace_back(query);
  }

  MySQLQuery* rightJoin(const std::string& tableName) {
    this->hasOn = false;
    this->query += " RIGHT JOIN " + tableName;
    return this;
  }

  MySQLQuery* select(const std::vector<std::string>& args = {}) {
    if (!args.size()) {
      this->query = "SELECT * FROM " + this->tableName;
      return this;
    }

    this->query = "SELECT ";
    for (size_t i = 0; args.size() > i; i++) {
      if (i > 0) this->query += ", ";
      this->query += args[i];
    }

    this->query += " FROM " + this->tableName;
    return this;
  }

  MySQLQuery* table(const std::string& tableName) {
    this->tableName = tableName;
    return this;
  }

  MySQLQuery* update(
      const std::map<
          std::string,
          const std::variant<std::nullptr_t, int, double, std::string>>& args) {
    this->query = "UPDATE ";
    this->query += this->tableName;
    this->query += " SET ";

    bool first = true;
    for (const auto& [key, value] : args) {
      if (first) {
        first = false;
      } else {
        this->query += ", ";
      }

      if (std::holds_alternative<std::nullptr_t>(value)) {
        this->query += key + " = NULL";
        continue;
      }

      if (std::holds_alternative<int>(value)) {
        const std::string binding = std::to_string(std::get<int>(value));
        this->bindings.emplace_back(binding);
        this->query += key + " = ?";
        continue;
      }

      if (std::holds_alternative<double>(value)) {
        const std::string binding = std::to_string(std::get<double>(value));
        this->bindings.emplace_back(binding);
        this->query += key + " = ?";
        continue;
      }

      if (std::holds_alternative<std::string>(value)) {
        const std::string binding = std::get<std::string>(value);
        this->bindings.emplace_back(binding);
        this->query += key + " = ?";
        continue;
      }
    }

    return this;
  }

  MySQLQuery* where(const std::function<void(MySQLQuery*)>& condition) {
    if (this->hasWhere) {
      const bool hasCondition = this->query.ends_with(")");
      if (hasCondition) this->query += " AND ";
    } else {
      this->query += " WHERE ";
      this->hasWhere = true;
    }

    this->query += "(";
    condition(this);
    this->query += ")";
    return this;
  }

  MySQLQuery* where(
      const std::string& column,
      const std::variant<std::nullptr_t, int, double, std::string>& arg2,
      const std::variant<std::nullptr_t, int, double, std::string>& arg3 =
          nullptr) {
    if (this->hasWhere) {
      const bool hasCondition =
          this->query.ends_with("?") || this->query.ends_with("IS NULL");
      if (hasCondition) this->query += " AND ";
    } else {
      this->query += " WHERE ";
      this->hasWhere = true;
    }

    this->condition(true, column, arg2, arg3);
    return this;
  }
};

#endif