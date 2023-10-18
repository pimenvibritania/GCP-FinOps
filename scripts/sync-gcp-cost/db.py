import os

import mysql.connector.pooling
from dotenv import load_dotenv

load_dotenv()

db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_user = os.getenv("DB_USERNAME")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")

# Create a connection pool

db_config = {
    "pool_name": "mysql_pool",
    "pool_size": 5,  # Adjust the pool size as needed
    "host": db_host,
    "port": db_port,
    "user": db_user,
    "password": db_password,
    "database": db_name,
}


def get_connection():
    return mysql.connector.connect(**db_config)


# def get_pool_connection():
#     connection_pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)
#     return connection_pool.get_connection()


def execute_query(query):
    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(query)

        rows = cursor.fetchall()

        cursor.close()

        return rows
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if connection:
            connection.close()


def commit_query(query, data):
    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(query, data)
        rows = connection.commit()

        cursor.close()

        return rows
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if connection:
            connection.close()
