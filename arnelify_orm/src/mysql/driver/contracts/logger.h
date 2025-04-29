#ifndef ARNELIFY_ORM_MYSQL_DRIVER_LOGGER_H
#define ARNELIFY_ORM_MYSQL_DRIVER_LOGGER_H

#include <iostream>
#include <functional>

using MySQLLogger = std::function<void(const std::string&, const bool&)>;

#endif