import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_source_connection():
    return mysql.connector.connect(
        host=os.getenv("SOURCE_DB_HOST"),
        user=os.getenv("SOURCE_DB_USER"),
        password=os.getenv("SOURCE_DB_PASSWORD"),
        database=os.getenv("SOURCE_DB_NAME")
    )


def get_local_connection():
    return mysql.connector.connect(
        host=os.getenv("LOCAL_DB_HOST"),
        user=os.getenv("LOCAL_DB_USER"),
        password=os.getenv("LOCAL_DB_PASSWORD"),
        database=os.getenv("LOCAL_DB_NAME")
    )