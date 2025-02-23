import requests
import json
import os
from datetime import datetime

def get_lat_lon_from_plus_code(plus_code):
    api_key = os.getenv("GOOGLE_API_KEY")
    url = f'https://plus.codes/api?address={plus_code}&key={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'geometry' in data and 'location' in data['geometry']:
            lat = data['geometry']['location']['lat']
            lon = data['geometry']['location']['lng']
            return lat, lon
    return None, None

def normalize(value, min_value, max_value):
    return (value - min_value) / (max_value - min_value) if max_value > min_value else 0

def calculate_score(place, max_rating=5, min_rating=3.5):
    return normalize(place['rating'], min_rating, max_rating)

def filter_and_rank_places(places):
    filtered_places = [place for place in places if place.get('rating', 0) >= 3.5 and place.get('user_ratings_total', 0) >= 100]
    for place in filtered_places:
        place['score'] = calculate_score(place)
    return sorted(filtered_places, key=lambda x: x['score'], reverse=True)

def find_places_nearby(plus_code, radius):
    api_key = os.getenv("GOOGLE_API_KEY")
    lat, lon = get_lat_lon_from_plus_code(plus_code)
    if lat is None or lon is None:
        print("Error: Invalid Plus Code")
        return []
    types = ['bar', 'club', 'restaurant', 'pub', 'cabaret', 'nightlife', 'lounge', 'karaoke', 'brewery', 'speakeasy', 'strip_club', 'music', 'food', 'arcade', 'park', 'street_fair', 'beer']
    url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
    params = {'location': f'{lat},{lon}', 'radius': radius, 'keyword': '|'.join(types), 'key': api_key}
    response = requests.get(url, params=params)
    return response.json().get('results', [])

def fetch_popular_times(place_id):
    api_key = os.getenv("GOOGLE_API_KEY")
    url = f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=populartimes&key={api_key}'
    response = requests.get(url)
    result = response.json().get('result', {})
    return result.get('populartimes', {})

def generate_popular_times_report(plus_code, radius=6999):
    places = find_places_nearby(plus_code, radius)
    ranked_places = filter_and_rank_places(places)
    report_data = []
    max_requests = min(250, len(ranked_places))  # Limit requests to max 250 iterations
    for i in range(max_requests):
        place = ranked_places[i]
        place_id = place['place_id']
        popular_times = fetch_popular_times(place_id)
        top_days = sorted(popular_times.items(), key=lambda x: sum(x[1]), reverse=True)[:3] if popular_times else []
        report_data.append({
            'name': place['name'],
            'rating': place['rating'],
            'reviews': place['user_ratings_total'],
            'popular_times': popular_times,
            'top_days': top_days
        })
    timestamp = datetime.now().strftime('%d.%m.%Y_%H.%M')
    filename = f'{timestamp}_PopularTimes.txt'
    with open(filename, 'w') as file:
        json.dump(report_data, file, indent=4)
    print(f'Report saved as {filename}')

# Example usage
plus_code = 'V943+6Q'
generate_popular_times_report(plus_code)
