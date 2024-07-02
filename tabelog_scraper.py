# tabelog_scraper.py
import requests
from bs4 import BeautifulSoup
import time
import random
import json

class TabelogScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'CustomBot/1.0 (https://example.com/bot; bot@example.com)'
        }
        self.base_url = 'https://tabelog.com'

    def scrape_area(self, area, cuisine, num_pages=2):
        all_restaurants = []
        for page in range(1, num_pages + 1):
            url = f"{self.base_url}/tokyo/{area}/rstLst/{page}/?vs=1&sa={area}&sk={cuisine}"
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            restaurants = self._parse_restaurant_list(soup)
            all_restaurants.extend(restaurants)
            
            time.sleep(random.uniform(1, 3))  # 요청 간 딜레이
        
        return all_restaurants

    def _parse_restaurant_list(self, soup):
        restaurants = []
        for item in soup.select('.list-rst__item'):
            name = item.select_one('.list-rst__rst-name-target').text.strip()
            rating = item.select_one('.c-rating__val').text.strip()
            url = item.select_one('.list-rst__rst-name-target')['href']
            restaurants.append({
                'name': name,
                'rating': rating,
                'url': self.base_url + url
            })
        return restaurants

    def save_to_json(self, data, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)