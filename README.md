# RSSePub

Convert RSS feed posts into EPUB files automatically.

## Features

- Monitors an RSS feed for new posts
- Converts new posts to EPUB format
- Tracks processed posts to avoid duplicates
- Supports HTML content cleaning with BeautifulSoup4

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/changeforan/RSSePub.git
cd RSSePub
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the converter with an RSS feed URL:

```bash
python rss_to_epub.py <RSS_FEED_URL>
```

Example:
```bash
python rss_to_epub.py https://example.com/feed.rss
```

The program will:
1. Download the RSS feed
2. Check each post against `seen_posts.txt` to identify new posts
3. Convert new posts to EPUB files
4. Save the EPUB files in the current directory
5. Update `seen_posts.txt` with processed post IDs

## Files

- `rss_to_epub.py` - Main converter script
- `requirements.txt` - Python dependencies
- `seen_posts.txt` - Tracks processed post IDs (auto-generated)
- `*.epub` - Generated EPUB files (auto-generated)

## Dependencies

- **feedparser** - Parse RSS and Atom feeds
- **EbookLib** - Create EPUB files
- **beautifulsoup4** - Clean and parse HTML content

## License

See LICENSE file for details.
