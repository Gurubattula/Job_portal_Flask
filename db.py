import mysql.connector
from mysql.connector import Error

def create_connection():
    """Create a connection to the MySQL database"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Kishorebv@123',
            database='flask_job_portal'
        )
        if connection.is_connected():
            print("Connection to MySQL successful")
        return connection
    except Error as e:
        print(f"Error: {e}")
        return None

def close_connection(connection):
    """Close the connection to the MySQL database"""
    if connection.is_connected():
        connection.close()
        print("MySQL connection closed")
