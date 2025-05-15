import sqlite3
import os   
import pandas as pd

# load data from sqlite
db_path = r"C:\Users\PC\Desktop\Masterarbeit\Code\WSJ\2023\articleswsj_2023.db"
conn = sqlite3.connect(db_path)
# create a cursor object
c = conn.cursor()
# load article table
query = """
    SELECT *
    FROM article
"""
df = pd.read_sql_query(query, conn)
# close the connection
conn.close()
print(df.head())