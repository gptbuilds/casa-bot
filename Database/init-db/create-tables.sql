CREATE TABLE IF NOT EXISTS properties (
    id SERIAL PRIMARY KEY,
    position INT,
    price VARCHAR(100),
    bedrooms VARCHAR(50),
    bathroom VARCHAR(50),
    area_sqft VARCHAR(100),
    description TEXT,
    address TEXT,
    other_info TEXT,
    image_url TEXT,
    detail_link TEXT
);
