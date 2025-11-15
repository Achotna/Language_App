import pandas as pd
from sqlalchemy import create_engine
import sqlite3

# chaange the path to the location of your Excel file
data = pd.read_excel('C:\\Users\\Eleve\\Downloads\\Language app\\english_french test.xlsx')
data.columns = ["english", "french"]
data["status"] = 1
print(data.head())


engine = create_engine("sqlite:///./vocab.db")
data.to_sql('vocab', con=engine, if_exists='append', index=False)

#new entry
new = {"english": "Thank you", "french": "Merci", "status": 1}
new_data = pd.DataFrame([new])
#check for duplicates
existing_data = pd.read_sql("SELECT * FROM vocab", engine)
new_data_to_insert = new_data[~new_data['english'].isin(existing_data['english'])]
#insert 
new_data_to_insert.to_sql("vocab", con=engine, if_exists="append", index=False)

#resultat verif
conn = sqlite3.connect("vocab.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM vocab")
rows = cursor.fetchall()
for row in rows:
    print(row)



#cursor.execute("DROP TABLE IF EXISTS vocab")
#conn.commit()

conn.close()
