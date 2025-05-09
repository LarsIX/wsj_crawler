import sqlite3
import pandas as pd    

link = r"C:\Users\PC\Desktop\Masterarbeit\Code\LATimes\articlesLAT.db"
querry = query = "SELECT * FROM article WHERE corpus != 'not found' AND corpus != ''"
#     conn = sqlite3.connect(link)
conn = sqlite3.connect(link)
df = pd.read_sql_query(querry, conn)
print(df.head(10))