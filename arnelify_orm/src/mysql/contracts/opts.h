#ifndef ARNELIFY_ORM_MYSQL_OPTS_H
#define ARNELIFY_ORM_MYSQL_OPTS_H

#include <iostream>

struct MySQLOpts final {
  const int ORM_MAX_CONNECTIONS;
  const std::string ORM_HOST;
  const std::string ORM_NAME;
  const std::string ORM_USER;
  const std::string ORM_PASS;
  const int ORM_PORT;

  MySQLOpts(const int m, const std::string& h, const std::string& n,
            const std::string& u, const std::string& pwd, const int p)
      : ORM_MAX_CONNECTIONS(m),
        ORM_HOST(h),
        ORM_NAME(n),
        ORM_USER(u),
        ORM_PASS(pwd),
        ORM_PORT(p) {};
};

#endif