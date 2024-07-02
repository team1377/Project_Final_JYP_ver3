# restaurant_database.py
import sqlite3
import json

class RestaurantDatabase:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS restaurants (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            rating REAL,
            reviews INTEGER,
            address TEXT,
            phone TEXT,
            hours TEXT,
            price_range TEXT,
            location TEXT,
            menu TEXT,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        self.conn.commit()

    def insert_restaurant(self, restaurant):
        self.cursor.execute('''
        INSERT OR REPLACE INTO restaurants 
        (name, rating, reviews, address, phone, hours, price_range, location, menu)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            restaurant['name'],
            float(restaurant['rating']),
            int(restaurant.get('reviews', '0').replace(',', '')),
            restaurant.get('address', ''),
            restaurant.get('phone', ''),
            restaurant.get('hours', ''),
            restaurant.get('price_range', ''),
            restaurant.get('location', ''),
            restaurant.get('menu', '')
        ))
        self.conn.commit()

    def load_from_json(self, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            restaurants = json.load(f)
        for restaurant in restaurants:
            self.insert_restaurant(restaurant)

    def get_total_restaurants(self):
        self.cursor.execute('SELECT COUNT(*) FROM restaurants')
        return self.cursor.fetchone()[0]

    def get_restaurant_stats(self):
        self.cursor.execute('''
        SELECT AVG(rating) as avg_rating, AVG(reviews) as avg_reviews
        FROM restaurants
        ''')
        result = self.cursor.fetchone()
        return {
            'avg_rating': result[0],
            'avg_reviews': result[1]
        }

    def get_location_distribution(self):
        self.cursor.execute('''
        SELECT location, COUNT(*) as count
        FROM restaurants
        GROUP BY location
        ''')
        return dict(self.cursor.fetchall())

    def get_menu_distribution(self):
        self.cursor.execute('''
        SELECT menu, COUNT(*) as count
        FROM restaurants
        GROUP BY menu
        ''')
        return dict(self.cursor.fetchall())

    def close(self):
        self.conn.close()