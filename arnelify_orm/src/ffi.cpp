#ifndef ARNELIFY_ORM_FFI_CPP
#define ARNELIFY_ORM_FFI_CPP

#include "index.h"

extern "C" {

MySQL* mysql = nullptr;

void orm_free(const char* cPtr) {
  if (cPtr) delete[] cPtr;
}

void orm_mysql_close() {
  mysql->close();
}

void orm_mysql_connect() {
  mysql->connect();
}

void orm_mysql_create(const char* cOpts) {
  Json::Value json;
  Json::CharReaderBuilder reader;
  std::string errors;

  std::istringstream iss(cOpts);
  if (!Json::parseFromStream(reader, iss, &json, &errors)) {
    std::cout << "[ArnelifyORM FFI]: C error: Invalid cOpts." << std::endl;
    exit(1);
  }

  const bool hasMaxConnections = json.isMember("ORM_MAX_CONNECTIONS") &&
                                 json["ORM_MAX_CONNECTIONS"].isInt();
  if (!hasMaxConnections) {
    std::cout << "[ArnelifyORM FFI]: C error: 'ORM_MAX_CONNECTIONS' is missing."
              << std::endl;
    exit(1);
  }

  const bool hasHost = json.isMember("ORM_HOST") && json["ORM_HOST"].isString();
  if (!hasHost) {
    std::cout << "[ArnelifyORM FFI]: C error: 'ORM_HOST' is missing."
              << std::endl;
    exit(1);
  }

  const bool hasName = json.isMember("ORM_NAME") && json["ORM_NAME"].isString();
  if (!hasName) {
    std::cout << "[ArnelifyORM FFI]: C error: 'ORM_NAME' is missing."
              << std::endl;
    exit(1);
  }

  const bool hasUser = json.isMember("ORM_USER") && json["ORM_USER"].isString();
  if (!hasUser) {
    std::cout << "[ArnelifyORM FFI]: C error: 'ORM_USER' is missing."
              << std::endl;
    exit(1);
  }

  const bool hasPass = json.isMember("ORM_PASS") && json["ORM_PASS"].isString();
  if (!hasPass) {
    std::cout << "[ArnelifyORM FFI]: C error: 'ORM_PASS' is missing."
              << std::endl;
    exit(1);
  }

  const bool hasPort = json.isMember("ORM_PORT") && json["ORM_PORT"].isInt();
  if (!hasPort) {
    std::cout << "[ArnelifyORM FFI]: C error: 'ORM_PORT' is missing."
              << std::endl;
    exit(1);
  }

  MySQLOpts opts(json["ORM_MAX_CONNECTIONS"].asInt(),
                 json["ORM_HOST"].asString(), json["ORM_NAME"].asString(),
                 json["ORM_USER"].asString(), json["ORM_PASS"].asString(),
                 json["ORM_PORT"].asInt());

  mysql = new MySQL(opts);
}

void orm_mysql_destroy() {
  delete mysql;
  mysql = nullptr;
}

const char* orm_mysql_exec(const char* cQuery, const char* cSerialized) {
  Json::Value cBindings;
  Json::CharReaderBuilder reader;
  std::string errors;

  std::istringstream iss(cSerialized);
  if (!Json::parseFromStream(reader, iss, &cBindings, &errors)) {
    std::cout << "[ArnelifyORM FFI]: C error: Invalid cBindings." << std::endl;
    exit(1);
  }

  std::vector<std::string> bindings;
  for (int i = 0; cBindings.size() > i; ++i) {
    const Json::Value& value = cBindings[i];
    bindings.emplace_back(value.asString());
  }

  MySQLRes res = mysql->exec(cQuery, bindings);
  Json::Value json = mysql->toJson(res);

  Json::StreamWriterBuilder writer;
  writer["indentation"] = "";
  writer["emitUTF8"] = true;

  const std::string out = Json::writeString(writer, json);
  char* cRes = new char[out.length() + 1];
  std::strcpy(cRes, out.c_str());
  return cRes;
}

const char* orm_mysql_get_uuid() {
  const std::string uuid = mysql->getUuId();
  char* cUuId = new char[uuid.length() + 1];
  std::strcpy(cUuId, uuid.c_str());
  return cUuId;
}
}

#endif