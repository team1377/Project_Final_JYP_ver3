# restaurant_visualizer.py
import matplotlib.pyplot as plt
import sqlite3

class RestaurantVisualizer:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def visualize_data(self):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # 평점 분포
        self.cursor.execute('SELECT rating FROM restaurants')
        ratings = [row[0] for row in self.cursor.fetchall()]
        ax1.hist(ratings, bins=10, edgecolor='black')
        ax1.set_title('레스토랑 평점 분포')
        ax1.set_xlabel('평점')
        ax1.set_ylabel('레스토랑 수')

        # 가격대 분포
        self.cursor.execute('SELECT price_range FROM restaurants')
        prices = [row[0] for row in self.cursor.fetchall() if row[0]]
        price_ranges = {'~¥1000': 0, '¥1000~¥2000': 0, '¥2000~¥3000': 0, '¥3000~': 0}
        for price in prices:
            amount = int(price.replace('¥', '').replace(',', '').split('~')[0])
            if amount < 1000:
                price_ranges['~¥1000'] += 1
            elif amount < 2000:
                price_ranges['¥1000~¥2000'] += 1
            elif amount < 3000:
                price_ranges['¥2000~¥3000'] += 1
            else:
                price_ranges['¥3000~'] += 1
        
        ax2.pie(price_ranges.values(), labels=price_ranges.keys(), autopct='%1.1f%%', startangle=90)
        ax2.set_title('레스토랑 가격대 분포')

        plt.tight_layout()
        return fig

    def close(self):
        self.conn.close()