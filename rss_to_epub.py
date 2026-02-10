#!/usr/bin/env python3
"""
RSS to EPUB Converter
Monitors an RSS feed and converts new posts into EPUB files.
"""

import os
import sys
import hashlib
import html
import feedparser
from ebooklib import epub
from bs4 import BeautifulSoup


class RSSToEpubConverter:
    """Converts RSS feed posts to EPUB files."""
    
    def __init__(self, rss_url, history_file='seen_posts.txt'):
        """
        Initialize the converter.
        
        Args:
            rss_url: URL of the RSS feed to monitor
            history_file: Path to file tracking seen post IDs
        """
        self.rss_url = rss_url
        self.history_file = history_file
        self.seen_posts = self._load_history()
    
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
        safe_title = "".join(
            c for c in title if c.isalnum() or c in (' ', '-', '_')
        ).strip()
        safe_title = safe_title[:50]  # Limit length
        if not safe_title:
            safe_title = 'post'
        
        # Add hash of post_id to ensure uniqueness (16 chars for better collision resistance)
        id_hash = hashlib.sha256(post_id.encode('utf-8')).hexdigest()[:16]
        filename = f"{safe_title}_{id_hash}.epub"
        
        # Write EPUB file
        epub.write_epub(filename, book)
        
        return filename
    
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
                
                # Save the post ID to history
                self._save_post_id(post_id)
                self.seen_posts.add(post_id)
                
                new_posts_count += 1
                
            except Exception as e:
                print(f"Error creating EPUB for post '{entry.get('title', 'Unknown')}' (ID: {post_id}): {e}")
                print(f"Skipping this post - it will be attempted again on the next run since it was not marked as processed.")
                continue
        
        print(f"\nProcessed {new_posts_count} new post(s)")
        return new_posts_count


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python rss_to_epub.py <RSS_FEED_URL>")
        print("Example: python rss_to_epub.py https://example.com/feed.rss")
        sys.exit(1)
    
    rss_url = sys.argv[1]
    
    converter = RSSToEpubConverter(rss_url)
    converter.process_feed()


if __name__ == '__main__':
    main()
