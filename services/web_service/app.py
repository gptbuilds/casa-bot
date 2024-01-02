from flask import Flask, jsonify
import psycopg2
import os


app = Flask(__name__)

import time

def get_db_connection():
    max_retries = 5
    retry_count = 0
    while retry_count < max_retries:
        try:
            conn = psycopg2.connect(dbname= "mydb", user= "mcd0056", password= "6060", host="db")
            return conn
        except psycopg2.OperationalError as e:
            time.sleep(2)  
            retry_count += 1
    raise Exception("Failed to connect to the database after several attempts")


@app.route('/properties', methods=['GET'])
def get_properties():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM properties;')
    properties = cur.fetchall()
    cur.close()
    conn.close()
    
    # list of dictionaries for JSON response
    property_list = []
    for property in properties:
        property_list.append({
            'id': property[0],
            'position': property[1],
            'price': property[2],
            'bedrooms': property[3],
            'bathroom': property[4],
            'area_sqft': property[5],
            'description': property[6],
            'address': property[7],
            'other_info': property[8],
            'image_url': property[9],
            'detail_link': property[10]
        })

    return jsonify(property_list)

if __name__ == '__main__':
    app.run(debug=False, port=8085)
