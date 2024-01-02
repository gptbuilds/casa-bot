from quart import Quart, jsonify
import asyncpg
import asyncio

app = Quart(__name__)

async def get_db_connection():
    max_retries = 5
    retry_count = 0
    while retry_count < max_retries:
        try:
            conn = await asyncpg.connect(database="mydb", user="mcd0056", password="6060", host="db")
            return conn
        except Exception as e:
            await asyncio.sleep(2)
            retry_count += 1
    raise Exception("Failed to connect to the database after several attempts")

@app.route('/properties', methods=['GET'])
async def get_properties():
    conn = await get_db_connection()
    try:
        
        properties = await conn.fetch('SELECT * FROM properties;')
        
        property_list = []
        for property in properties:
            property_list.append({
                'id': property['id'], 
                'position': property['position'],
                'price': property['price'],
                'bedrooms': property['bedrooms'],
                'bathroom': property['bathroom'],
                'area_sqft': property['area_sqft'],
                'description': property['description'],
                'address': property['address'],
                'other_info': property['other_info'],
                'image_url': property['image_url'],
                'detail_link': property['detail_link']
            })
        return jsonify(property_list)
    finally:
        await conn.close()


if __name__ == '__main__':
    app.run(debug=False, port=8085)
