import sqlite3
import pandas as pd
DB_PATH = r"C:\Users\PC\Desktop\Masterarbeit\Code\articlesWSJ.db"
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql("""
Select link FROM articles_index 
""",conn)
conn.close()

print(df.link[1])
