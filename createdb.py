import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os


# --------------------------------------------------
# Load environment variables from .env
# --------------------------------------------------

load_dotenv()


# --------------------------------------------------
# Read MySQL configuration
# --------------------------------------------------

MYSQL_HOST = os.getenv("sql_database_host", "localhost")
MYSQL_PORT = int(os.getenv("sql_database_port", 3306))
MYSQL_USER = os.getenv("sql_database_user", "root")
MYSQL_PASSWORD = os.getenv("sql_database_password")


# --------------------------------------------------
# Connect to MySQL Server
# --------------------------------------------------

medicine_db = None
cursor = None

try:

    medicine_db = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD
    )

    if medicine_db.is_connected():

        print("Connected to MySQL successfully.")


        # --------------------------------------------------
        # Create cursor
        # --------------------------------------------------

        cursor = medicine_db.cursor()


        # --------------------------------------------------
        # Create MediFind database
        # --------------------------------------------------

        cursor.execute(
            "CREATE DATABASE IF NOT EXISTS MediFind"
        )

        print("MediFind database created successfully.")


except Error as e:

    print("Error while connecting to MySQL:")
    print(e)


finally:

    # --------------------------------------------------
    # Close cursor
    # --------------------------------------------------

    if cursor is not None:
        cursor.close()


    # --------------------------------------------------
    # Close database connection
    # --------------------------------------------------

    if medicine_db is not None and medicine_db.is_connected():
        medicine_db.close()
        print("MySQL connection closed.")
