#!/usr/bin/env python3
"""
Strategic Intelligence Feed Generator
Fetches RSS/JSON feeds and generates a combined RSS feed.
"""

import feedparser
from feedgen.feed import FeedGenerator
from datetime import datetime, timedelta
import pytz
import os
import json
import logging
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('feed_generator.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Constants
FEED_FILE = "strategic-feed.xml"
SOURCES_FILE = "sources.txt"
MAX_ITEMS = 200  # Limit feed size
TIMEZONE = pytz.timezone('Europe/Paris')

# Location mapping for geocoding
LOCATION_MAP = {
    'russia': {'lat': 60, 'lng': 100, 'zoom': 4, 'name': 'Russia'},
    'ukraine': {'lat': 48.3794, 'lng': 31.1656, 'zoom': 6, 'name': 'Ukraine'},
    'china': {'lat': 35.8617, 'lng': 104.1954, 'zoom': 4, 'name': 'China'},
    'usa': {'lat': 37.0902, 'lng': -95.7129, 'zoom': 4, 'name': 'USA'},
    'united states': {'lat': 37.0902, 'lng': -95.7129, 'zoom': 4, 'name': 'USA'},
    'uk': {'lat': 55.3781, 'lng': -3.4360, 'zoom': 5, 'name': 'UK'},
    'france': {'lat': 46.6034, 'lng': 1.8883, 'zoom': 5, 'name': 'France'},
    'germany': {'lat': 51.1657, 'lng': 10.4515, 'zoom': 5, 'name': 'Germany'},
    'estonia': {'lat': 58.5953, 'lng': 25.0136, 'zoom': 7, 'name': 'Estonia'},
    'moldova': {'lat': 47.4116, 'lng': 28.3699, 'zoom': 7, 'name': 'Moldova'},
    'kyiv': {'lat': 50.4501, 'lng': 30.5234, 'zoom': 10, 'name': 'Kyiv'},
    'moscow': {'lat': 55.7558, 'lng': 37.6173, 'zoom': 10, 'name': 'Moscow'},
    'washington': {'lat': 38.9072, 'lng': -77.0369, 'zoom': 10, 'name': 'Washington'},
    'london': {'lat': 51.5074, 'lng': -0.1278, 'zoom': 10, 'name': 'London'},
    'paris': {'lat': 48.8566, 'lng': 2.3522, 'zoom': 10, 'name': 'Paris'},
    'berlin': {'lat': 52.5200, 'lng': 13.4050, 'zoom': 10, 'name': 'Berlin'},
    'beijing': {'lat': 39.9042, 'lng': 116.4074, 'zoom': 10, 'name': 'Beijing'},
    'nato': {'lat': 50.8801, 'lng': 4.3832, 'zoom': 4, 'name': 'NATO HQ'},
    'eu': {'lat': 50.8801, 'lng': 4.3832, 'zoom': 4, 'name': 'EU HQ'},
    'baltic': {'lat': 57.5, 'lng': 20, 'zoom': 5, 'name': 'Baltic Sea'},
    'black sea': {'lat': 42.5, 'lng': 35, 'zoom': 6, 'name': 'Black Sea'},
    'middle east': {'lat': 31.4165, 'lng': 35, 'zoom': 5, 'name': 'Middle East'},
    'donbas': {'lat': 48.5, 'lng': 38, 'zoom': 7, 'name': 'Donbas'},
    'crimea': {'lat': 45, 'lng': 34, 'zoom': 7, 'name': 'Crimea'},
    'taiwan': {'lat': 23.5, 'lng': 121, 'zoom': 8, 'name': 'Taiwan'},
    'south china sea': {'lat': 15, 'lng': 115, 'zoom': 5, 'name': 'South China Sea'}
}

# Priority sources (marked with ⭐ in the dashboard)
PRIORITY_SOURCES = [
    "ODNI Annual Threat Assessment",
    "Estonian EFIS 2026",
    "BND Military Spending",
    "ACLED Conflict Data",
    "ISW Russia Reports",
    "CIA FOIA",
    "MI5",
    "DGSE Interview",
    "CISA Alerts",
    "MITRE ATT&CK"
]

# Load sources from file
def load_sources():
    try:
        with open(SOURCES_FILE, 'r') as f:
            sources = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return sources
    except Exception as e:
        logger.error(f"Error loading sources.txt: {e}")
        return []

# Clean HTML from descriptions
def clean_html(text):
    if not text:
        return ""
    soup = BeautifulSoup(text, features="html.parser")
    return soup.get_text().strip()

# Extract location from text
def extract_location(text):
    if not text:
        return None
    text_lower = text.lower()
    for key, loc in LOCATION_MAP.items():
        if key in text_lower:
            return loc
    return None

# Fetch and parse a feed
def fetch_feed(url):
    try:
        feed = feedparser.parse(url)
        if feed.bozo:  # If feed is malformed
            logger.warning(f"Malformed feed: {url} - {feed.bozo_exception}")
            return []

        items = []
        for entry in feed.entries:
            title = getattr(entry, 'title', 'No title')
            link = getattr(entry, 'link', '#')
            description = getattr(entry, 'description', '') or getattr(entry, 'summary', '')
            description = clean_html(description)

            pub_date = getattr(entry, 'published_parsed', None)
            if pub_date:
                pub_date = datetime(*pub_date[:6], tzinfo=TIMEZONE)
            else:
                pub_date = datetime.now(TIMEZONE)

            # Determine source name from URL
            source_name = url.split('/')[2].replace('www.', '') if '//' in url else url

            # Check if this is a priority source
            is_priority = source_name in PRIORITY_SOURCES

            # Extract location
            location = extract_location(title + description)

            items.append({
                'title': title,
                'link': link,
                'description': description,
                'pubDate': pub_date,
                'source': source_name,
                'priority': is_priority,
                'location': location
            })
        return items
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return []

# Generate the RSS feed
def generate_feed(entries):
    fg = FeedGenerator()
    fg.title('🌍 Worldwide Strategic & Geostrategic Intelligence Feed')
    fg.link(href='https://YOUR_USERNAME.github.io/strategic-intel-dashboard/strategic-feed.xml')
    fg.description('Aggregated feed of global strategic intelligence: official reports, think tank analyses, and geopolitical developments. Updated every 4 hours.')
    fg.language('en')
    fg.copyright(f'CC BY-NC-SA 4.0 – Auto-updated {datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M")} CET')
    fg.pubDate(datetime.now(TIMEZONE))
    fg.lastBuildDate(datetime.now(TIMEZONE))
    fg.docs('http://www.rssboard.org/rss-specification/')
    fg.generator('Strategic Intelligence Aggregator v2.0')

    # Add categories
    fg.category('Intelligence Reports')
    fg.category('Geopolitical Analysis')
    fg.category('Military & Defense')
    fg.category('Cyber & Technology')
    fg.category('Economic Intelligence')

    # Sort entries by date (newest first) and limit
    sorted_entries = sorted(entries, key=lambda x: x['pubDate'], reverse=True)[:MAX_ITEMS]

    for entry in sorted_entries:
        fe = fg.add_entry()
        fe.title(entry['title'])
        fe.link(href=entry['link'])
        fe.description(entry['description'])
        fe.pubDate(entry['pubDate'])
        fe.category(term=entry['source'], domain='source')
        if entry.get('priority'):
            fe.category(term='Priority', domain='priority')
        if entry.get('location'):
            fe.category(term=entry['location']['name'], domain='location')

    # Save to file
    fg.rss_file(FEED_FILE)
    logger.info(f"Generated feed with {len(sorted_entries)} items")

# Main function
def main():
    logger.info("Starting feed generation...")
    sources = load_sources()
    logger.info(f"Loaded {len(sources)} sources")

    all_entries = []
    for source in sources:
        try:
            logger.info(f"Fetching: {source}")
            entries = fetch_feed(source)
            all_entries.extend(entries)
        except Exception as e:
            logger.error(f"Error processing {source}: {e}")

    # Remove duplicates by link
    unique_entries = []
    seen_links = set()
    for entry in all_entries:
        if entry['link'] not in seen_links:
            seen_links.add(entry['link'])
            unique_entries.append(entry)

    generate_feed(unique_entries)

if __name__ == "__main__":
    main()