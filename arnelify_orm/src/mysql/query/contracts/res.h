#ifndef ARNELIFY_ORM_MYSQL_QUERY_RES_H
#define ARNELIFY_ORM_MYSQL_QUERY_RES_H

#include <iostream>
#include <map>
#include <variant>

using MySQLRow =
    std::map<std::string, std::variant<std::nullptr_t, std::string>>;
using MySQLRes = std::vector<MySQLRow>;

#endif