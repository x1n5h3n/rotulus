import argparse
import sys

import psycopg2
import yaml

TABLES = [
    {"name": "usernames",
     "columns": [
         {"name": "id",
          "properties": "bigserial primary key"
          },
         {"name": "username",
          "properties": "bytea not null unique"
          }
     ],
     },
    {"name": "domains",
     "columns": [
         {"name": "id",
          "properties": "bigserial primary key"
          },
         {"name": "domain",
             "properties": "bytea not null unique"
          }
     ],
     },
    {"name": "passwords",
     "columns": [
         {"name": "id",
          "properties": "bigserial primary key"
          },
         {"name": "password",
             "properties": "bytea not null unique"
          }
     ],
     },
    {"name": "hashes_types",
     "columns": [
         {"name": "id",
          "properties": "serial primary key"
          },
         {"name": "hash_type",
             "properties": "char(50) not null unique"
          }
     ],
     },
    {"name": "hashes",
     "columns": [
         {"name": "id",
          "properties": "bigserial primary key"
          },
         {"name": "hash",
             "properties": "char(255) not null unique"
          },
         {"name": "hash_type_id",
          "properties": "int references rotulus.hashes_types(id)"
          }
     ],
     },
    {"name": "records",
     "columns": [
         {"name": "id",
          "properties": "bigserial primary key"
          },
         {"name": "username_id",
             "properties": "bigint not null references rotulus.usernames(id)"
          },
         {"name": "domain_id",
          "properties": "bigint references rotulus.domains(id)"
          },
         {"name": "password_id",
          "properties": "bigint references rotulus.passwords(id)"
          },
         {"name": "hash_id",
          "properties": "bigint references rotulus.hashes(id)"
          }
     ]
     }
]


def get_db_conf():
    conf_path = "../conf"
    db_conf = "database.yml"
    dbconf = "{}/{}".format(conf_path, db_conf)

    try:
        with open(dbconf, "r") as stream:
            return yaml.safe_load(stream)
    except:
        print("[!] Unable to read database configuration in {}".format(db_conf))
        return False


def db_connect():
    #print("[*] Connecting to PostgreSQL database")
    db_conf = get_db_conf()
    if db_conf != False:
        try:
            connection = psycopg2.connect(user=db_conf["psql"]["username"],
                                          password=db_conf["psql"]["password"],
                                          host=db_conf["psql"]["host"],
                                          port=db_conf["psql"]["port"],
                                          database=db_conf["psql"]["dbname"])
            return connection
        except (Exception, psycopg2.Error) as error:
            print("[!] Error while connecting to PostgreSQL", error)
            return False
    else:
        return False


def execute_query(connection, query):
    try:
        connection.cursor().execute(query)
        return True
    except (Exception, psycopg2.Error) as error:
        print("[!] Unable to execute '{}'".format(query))
        print(error)
        return False


def close_communication(connection):
    connection.cursor().close()
    connection.close()


def create_schema(connection):
    print("[*] Creating schema")
    query = "create schema rotulus;"
    return execute_query(connection, query)


def drop_schema(connection):
    print("[*] Dropping schema")
    query = "drop schema rotulus;"
    return execute_query(connection, query)


def create_tables(connection):
    print("[*] Creating tables")
    for table in TABLES:
        query = "create unlogged table rotulus.{}( ".format(table["name"])
        nb_colums = len(table["columns"])
        i = 0
        for column in table["columns"]:
            query += "{} {}".format(column["name"], column["properties"])
            i += 1
            if i != nb_colums:
                query += ", "
        query += ");"
        if execute_query(connection, query) == False:
            return False
    return True


def drop_tables(connection):
    print("[*] Dropping tables")
    for table in TABLES:
        query = "drop table rotulus.{} cascade;".format(table["name"])
        if execute_query(connection, query) == False:
            return False
    return True


def setup_database():
    connection = db_connect()
    if connection != False:
        if create_schema(connection):
            if create_tables(connection) == True:
                connection.commit()
                close_communication(connection)
                return True
            else:
                connection.rollback()
        close_communication(connection)
    return False


def remove_tables():
    connection = db_connect()
    if connection != False:
        if drop_tables(connection) == True:
            if drop_schema(connection) == True:
                connection.commit()
                close_communication(connection)
                return True
            else:
                connection.rollback()
        close_communication(connection)
    return False


def parse_cli():
    parser = argparse.ArgumentParser(description='Manage Rotulus database')
    parser.add_argument('-d', '--database', choices=[
                        'create', 'drop', 'reset'], required=True, help='Action against database tables')

    args = parser.parse_args()

    if args.database == "create":
        setup_database()
    elif args.database == "drop":
        remove_tables()
    elif args.database == "reset":
        remove_tables()
        setup_database()


if __name__ == "__main__":
    parse_cli()
