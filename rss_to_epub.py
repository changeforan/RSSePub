#!/usr/bin/env python3
"""
RSS to EPUB Converter
Monitors an RSS feed and converts new posts into EPUB files.
"""

import os
import sys
import hashlib
import html
import time
import feedparser
from ebooklib import epub
from bs4 import BeautifulSoup


class RSSToEpubConverter:
    """Converts RSS feed posts to EPUB files."""
    
    def __init__(self, rss_url, history_file='seen_posts.txt', output_dir='output'):
        """
        Initialize the converter.
        
        Args:
            rss_url: URL of the RSS feed to monitor
            history_file: Path to file tracking seen post IDs
            output_dir: Directory to save EPUB files to
        """
        self.rss_url = rss_url
        self.history_file = history_file
        self.output_dir = output_dir
        self.seen_posts = self._load_history()
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def _load_history(self):
        """Load the history of seen post IDs from file."""
        if not os.path.exists(self.history_file):
            return set()
        
        with open(self.history_file, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    
    def _save_post_id(self, post_id):
        """Save a new post ID to the history file."""
        with open(self.history_file, 'a', encoding='utf-8') as f:
            f.write(f"{post_id}\n")
            f.flush()  # Ensure data is written to disk immediately
    
    def _clean_html_content(self, html_content):
        """Clean and extract text from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        return str(soup)
    
    def _create_epub(self, post):
        """
        Create an EPUB file from a post.
        
        Args:
            post: feedparser entry object containing post data
            
        Returns:
            Path to the created EPUB file
        """
        # Create a new EPUB book
        book = epub.EpubBook()
        
        # Extract post data
        title = post.get('title', 'Untitled')
        post_id = post.get('id', post.get('link', ''))
        
        # Get content from various possible fields
        content = ''
        if 'content' in post:
            content = post.content[0].value
        elif 'summary' in post:
            content = post.summary
        elif 'description' in post:
            content = post.description
        
        # Clean the content
        content = self._clean_html_content(content)
        
        # Set metadata
        book.set_identifier(post_id)
        book.set_title(title)
        book.set_language('en')
        
        # Add author if available
        if 'author' in post:
            book.add_author(post.author)
        else:
            book.add_author('Unknown')
        
        # Create chapter
        chapter = epub.EpubHtml(
            title=title,
            file_name='content.xhtml',
            lang='en'
        )
        # Escape title for HTML to prevent malformed content
        escaped_title = html.escape(title)
        chapter.content = f'<h1>{escaped_title}</h1>{content}'
        
        # Add chapter to book
        book.add_item(chapter)
        
        # Create table of contents
        book.toc = (chapter,)
        
        # Add navigation files
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # Define spine
        book.spine = ['nav', chapter]
        
        # Generate safe filename from title with unique identifier
        # Replace spaces with underscores, keep alphanumeric, hyphens, and underscores
        safe_title = "".join(
            c if c.isalnum() or c in ('-', '_') else '_' if c == ' ' else ''
            for c in title
        ).strip('_')
        safe_title = safe_title[:50]  # Limit length
        if not safe_title:
            safe_title = 'post'
        
        # Add hash of post_id to ensure uniqueness (16 chars for better collision resistance)
        id_hash = hashlib.sha256(post_id.encode('utf-8')).hexdigest()[:16]
        filename = f"{safe_title}_{id_hash}.epub"
        
        # Write EPUB file to output directory
        filepath = os.path.join(self.output_dir, filename)
        epub.write_epub(filepath, book)
        
        return filepath
    
    def process_feed(self):
        """
        Process the RSS feed and convert new posts to EPUB.
        
        Returns:
            Number of new posts processed
        """
        print(f"Fetching RSS feed from: {self.rss_url}")
        
        # Parse the RSS feed
        feed = feedparser.parse(self.rss_url)
        
        if feed.bozo:
            print(f"Warning: Feed parsing encountered errors")
            if hasattr(feed, 'bozo_exception'):
                print(f"Error: {feed.bozo_exception}")
        
        if not feed.entries:
            print("No entries found in feed")
            return 0
        
        print(f"Found {len(feed.entries)} entries in feed")
        
        new_posts_count = 0
        
        # Process each entry
        for entry in feed.entries:
            # Get unique ID for the post
            post_id = entry.get('id', entry.get('link', ''))
            
            if not post_id:
                print(f"Skipping entry without ID: {entry.get('title', 'Unknown')}")
                continue
            
            # Check if we've already processed this post
            if post_id in self.seen_posts:
                print(f"Already processed: {entry.get('title', 'Unknown')}")
                continue
            
            # Process new post
            print(f"Processing new post: {entry.get('title', 'Unknown')}")
            
            try:
                epub_file = self._create_epub(entry)
                print(f"Created EPUB: {epub_file}")
                
                # Update in-memory set first, then save to file for better consistency
                self.seen_posts.add(post_id)
                self._save_post_id(post_id)
                
                new_posts_count += 1
                
            except Exception as e:
                print(f"Error creating EPUB for post '{entry.get('title', 'Unknown')}' (ID: {post_id}): {e}")
                print(f"Skipping this post - it will be attempted again on the next run since it was not marked as processed.")
                continue
        
        print(f"\nProcessed {new_posts_count} new post(s)")
        return new_posts_count


class RSSFeedMonitor:
    """Long-running service that monitors multiple RSS feeds."""
    
    def __init__(self, feed_list_file='rss_feed.txt', output_dir='output', poll_interval=300):
        """
        Initialize the feed monitor.
        
        Args:
            feed_list_file: Path to file containing RSS feed URLs (one per line)
            output_dir: Directory to save EPUB files to
            poll_interval: Seconds to wait between feed checks (default: 300 = 5 minutes)
        """
        self.feed_list_file = feed_list_file
        self.output_dir = output_dir
        self.poll_interval = poll_interval
        self.converters = {}
        self.last_feed_list_mtime = None
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def _load_feed_list(self):
        """Load the list of RSS feed URLs from the feed list file."""
        if not os.path.exists(self.feed_list_file):
            print(f"Warning: Feed list file '{self.feed_list_file}' not found.")
            return []
        
        feeds = []
        with open(self.feed_list_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    feeds.append(line)
        
        return feeds
    
    def _check_feed_list_updated(self):
        """Check if the feed list file has been modified since last check."""
        if not os.path.exists(self.feed_list_file):
            return False
        
        current_mtime = os.path.getmtime(self.feed_list_file)
        
        # Initialize on first call, but don't consider it an update
        if self.last_feed_list_mtime is None:
            self.last_feed_list_mtime = current_mtime
            return False
        
        # Check if file has been modified
        if current_mtime > self.last_feed_list_mtime:
            self.last_feed_list_mtime = current_mtime
            return True
        
        return False
    
    def _update_converters(self):
        """Update the list of feed converters based on the feed list file."""
        feeds = self._load_feed_list()
        
        if not feeds:
            print(f"No feeds found in '{self.feed_list_file}'")
            return
        
        # Create a set of current feeds for comparison
        current_feeds = set(feeds)
        existing_feeds = set(self.converters.keys())
        
        # Add new feeds
        new_feeds = current_feeds - existing_feeds
        for feed_url in new_feeds:
            # Create a unique history file for each feed
            feed_hash = hashlib.sha256(feed_url.encode('utf-8')).hexdigest()[:16]
            history_file = f'seen_posts_{feed_hash}.txt'
            self.converters[feed_url] = RSSToEpubConverter(
                feed_url, 
                history_file=history_file,
                output_dir=self.output_dir
            )
            print(f"Added new feed: {feed_url}")
        
        # Remove feeds that are no longer in the list
        removed_feeds = existing_feeds - current_feeds
        for feed_url in removed_feeds:
            del self.converters[feed_url]
            print(f"Removed feed: {feed_url}")
    
    def run(self):
        """Start the monitoring service."""
        print(f"RSS Feed Monitor started")
        print(f"Feed list file: {self.feed_list_file}")
        print(f"Output directory: {self.output_dir}")
        print(f"Poll interval: {self.poll_interval} seconds")
        print("-" * 60)
        
        # Initial load of feeds and set up the mtime tracking
        if os.path.exists(self.feed_list_file):
            self.last_feed_list_mtime = os.path.getmtime(self.feed_list_file)
        self._update_converters()
        
        if not self.converters:
            print(f"\nError: No feeds to monitor. Please add RSS feed URLs to '{self.feed_list_file}'")
            print("Each URL should be on a separate line.")
            return
        
        print(f"\nMonitoring {len(self.converters)} feed(s)...")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Check if feed list has been updated and reload if needed
                if self._check_feed_list_updated():
                    print(f"\n{time.strftime('%Y-%m-%d %H:%M:%S')} - Feed list updated, reloading...")
                    self._update_converters()
                    
                    # Skip to next iteration if there are no feeds
                    if not self.converters:
                        print(f"No feeds to monitor. Waiting for feed list...")
                        time.sleep(self.poll_interval)
                        continue
                
                # Process each feed
                print(f"\n{time.strftime('%Y-%m-%d %H:%M:%S')} - Checking feeds...")
                for feed_url, converter in self.converters.items():
                    try:
                        converter.process_feed()
                    except Exception as e:
                        print(f"Error processing feed {feed_url}: {e}")
                
                # Wait before next check
                print(f"\nWaiting {self.poll_interval} seconds until next check...")
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")



def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("RSS to EPUB Converter")
        print("\nUsage:")
        print("  Single feed mode:  python rss_to_epub.py <RSS_FEED_URL>")
        print("  Monitor mode:      python rss_to_epub.py --monitor [options]")
        print("\nMonitor mode options:")
        print("  --feed-list FILE   Path to feed list file (default: rss_feed.txt)")
        print("  --output DIR       Output directory for EPUB files (default: output)")
        print("  --interval SECONDS Polling interval in seconds (default: 300)")
        print("\nExamples:")
        print("  python rss_to_epub.py https://example.com/feed.rss")
        print("  python rss_to_epub.py --monitor")
        print("  python rss_to_epub.py --monitor --interval 600")
        sys.exit(1)
    
    # Check if running in monitor mode
    if sys.argv[1] == '--monitor':
        # Parse monitor mode arguments
        feed_list_file = 'rss_feed.txt'
        output_dir = 'output'
        poll_interval = 300
        
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == '--feed-list' and i + 1 < len(sys.argv):
                feed_list_file = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == '--output' and i + 1 < len(sys.argv):
                output_dir = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == '--interval' and i + 1 < len(sys.argv):
                try:
                    poll_interval = float(sys.argv[i + 1])
                    if poll_interval <= 0:
                        print(f"Error: Interval must be a positive number, got '{poll_interval}'")
                        sys.exit(1)
                except ValueError:
                    print(f"Error: Invalid interval value '{sys.argv[i + 1]}'")
                    sys.exit(1)
                i += 2
            else:
                print(f"Error: Unknown argument '{sys.argv[i]}'")
                sys.exit(1)
        
        # Run monitor service
        monitor = RSSFeedMonitor(
            feed_list_file=feed_list_file,
            output_dir=output_dir,
            poll_interval=poll_interval
        )
        monitor.run()
    else:
        # Single feed mode (backward compatibility)
        rss_url = sys.argv[1]
        output_dir = 'output'
        
        converter = RSSToEpubConverter(rss_url, output_dir=output_dir)
        converter.process_feed()


if __name__ == '__main__':
    main()
