# RSSePub

Convert RSS feed posts into EPUB files automatically.

## Features

- Monitors RSS feeds for new posts
- Converts new posts to EPUB format
- Tracks processed posts to avoid duplicates
- Supports HTML content cleaning with BeautifulSoup4
- **NEW**: Support for multiple RSS feeds
- **NEW**: Long-running monitoring service
- **NEW**: Automatic feed list reloading
- **NEW**: Organized output directory

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

### Monitor Mode (Recommended)

Run as a long-running service that monitors multiple RSS feeds:

1. Create a `rss_feed.txt` file with one RSS feed URL per line:
```text
https://example.com/feed1.rss
https://example.com/feed2.rss
https://another-site.com/rss
```

2. Start the monitoring service:
```bash
python rss_to_epub.py --monitor
```

The service will:
- Load all feeds from `rss_feed.txt`
- Check each feed every 5 minutes (configurable)
- Convert new posts to EPUB files in the `output/` directory
- Automatically reload `rss_feed.txt` when it changes
- Continue running until stopped with Ctrl+C

**Options:**
- `--feed-list FILE`: Specify custom feed list file (default: `rss_feed.txt`)
- `--output DIR`: Specify output directory (default: `output`)
- `--interval SECONDS`: Set polling interval in seconds (default: 300)

**Example:**
```bash
python rss_to_epub.py --monitor --interval 600 --output my_books
```

### Single Feed Mode

For one-time conversion of a single feed:

```bash
python rss_to_epub.py <RSS_FEED_URL>
```

Example:
```bash
python rss_to_epub.py https://example.com/feed.rss
```

This will convert all new posts and save EPUB files to the `output/` directory.

## Files

- `rss_to_epub.py` - Main converter script
- `requirements.txt` - Python dependencies
- `rss_feed.txt` - List of RSS feeds to monitor (user-created)
- `seen_posts_*.txt` - Tracks processed post IDs per feed (auto-generated)
- `output/*.epub` - Generated EPUB files (auto-generated)

## Dependencies

- **feedparser** - Parse RSS and Atom feeds
- **EbookLib** - Create EPUB files
- **beautifulsoup4** - Clean and parse HTML content

## License

See LICENSE file for details.
