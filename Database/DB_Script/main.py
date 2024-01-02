import json
import psycopg2

# Connect to database
conn = psycopg2.connect(
    dbname="mydb", user="mcd0056", password="6060", host="localhost"
)
cur = conn.cursor()

# Open and read the JSON file
with open('Database\\DB_Script\\property_list.json', 'r') as file:
    properties = json.load(file)

# insert data into the database
for property in properties:
    cur.execute("""
        INSERT INTO properties (position, price, bedrooms, bathroom, area_sqft, description, address, other_info, image_url, detail_link)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, 
        (property['Position'], property['Price'], property['Bedroom(s)'], property['Bathroom'], property['Area (sqft)'], property['Description'], property['Address'], property['Other info'], property['Image'], property['Detail link'])
    )

conn.commit()
cur.close()
conn.close()
