import logging
import praw
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RedditClient:
    """Client for interacting with Reddit to get music trends."""
    
    def __init__(self, client_id=None, client_secret=None, user_agent='ai-dj-app'):
        """Initialize the Reddit client.
        
        Args:
            client_id (str, optional): Reddit client ID
            client_secret (str, optional): Reddit client secret
            user_agent (str, optional): User agent for Reddit API
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        
        # Initialize the Reddit client if credentials are provided
        if client_id and client_secret:
            try:
                self.reddit = praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    user_agent=user_agent
                )
                logger.info("Reddit client initialized with authentication")
            except Exception as e:
                logger.error(f"Error initializing Reddit client with auth: {str(e)}")
                self.reddit = None
        else:
            # Initialize in read-only mode without authentication
            try:
                self.reddit = praw.Reddit(
                    user_agent=user_agent,
                    check_for_updates=False,
                    read_only=True
                )
                logger.info("Reddit client initialized in read-only mode")
            except Exception as e:
                logger.error(f"Error initializing Reddit client: {str(e)}")
                self.reddit = None
    
    def get_music_posts(self, subreddits=None, limit=10, time_filter='week'):
        """Get music-related posts from specified subreddits.
        
        Args:
            subreddits (list, optional): List of subreddits to search
            limit (int, optional): Maximum number of posts to return
            time_filter (str, optional): Time filter for posts
            
        Returns:
            list: List of music posts
        """
        try:
            if not self.reddit:
                raise Exception("Reddit client not initialized")
            
            if not subreddits:
                subreddits = ['listentothis', 'music', 'newmusic', 'indieheads']
            
            all_posts = []
            
            for subreddit_name in subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    # Get top posts
                    for post in subreddit.top(time_filter=time_filter, limit=limit * 2):
                        # Extract artist and title from post title
                        music_info = self._parse_music_post(post.title)
                        
                        if music_info:
                            all_posts.append({
                                'artist': music_info['artist'],
                                'title': music_info['title'],
                                'score': post.score,
                                'url': post.url,
                                'permalink': f"https://www.reddit.com{post.permalink}",
                                'subreddit': subreddit_name,
                                'created_utc': post.created_utc,
                                'source': 'reddit'
                            })
                
                except Exception as e:
                    logger.error(f"Error getting posts from r/{subreddit_name}: {str(e)}")
            
            # Sort by score and limit results
            all_posts.sort(key=lambda x: x['score'], reverse=True)
            
            return all_posts[:limit]
        
        except Exception as e:
            logger.error(f"Error getting music posts from Reddit: {str(e)}")
            return []
    
    def _parse_music_post(self, title):
        """Parse a Reddit post title to extract artist and song title.
        
        Args:
            title (str): Post title
            
        Returns:
            dict: Artist and title information, or None if not a music post
        """
        # Common patterns in music subreddits
        patterns = [
            # Artist - Title [Genre] (Year)
            r'([^-\[\]]+)\s*-\s*([^-\[\]]+)(?:\s*\[([^\]]+)\])?(?:\s*\((\d{4})\))?',
            # Artist -- Title
            r'([^-]+)\s*--\s*([^-]+)',
            # Artist "Title"
            r'([^"]+)\s*"([^"]+)"',
            # Artist – Title
            r'([^–]+)\s*–\s*([^–]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                artist = match.group(1).strip()
                title = match.group(2).strip()
                
                # Clean up artist and title
                artist = re.sub(r'\(.*?\)', '', artist).strip()
                title = re.sub(r'\(.*?\)', '', title).strip()
                
                return {
                    'artist': artist,
                    'title': title
                }
        
        return None
    
    def get_genre_trends(self, limit=5):
        """Get trending genres based on subreddit activity.
        
        Args:
            limit (int, optional): Maximum number of genres to return
            
        Returns:
            list: List of trending genres
        """
        try:
            if not self.reddit:
                raise Exception("Reddit client not initialized")
            
            # List of music genre subreddits to check
            genre_subreddits = [
                'hiphopheads', 'indieheads', 'metal', 'electronicmusic', 
                'jazz', 'classicalmusic', 'punk', 'popheads', 'rock', 
                'rnb', 'country', 'folkmusic', 'ambient', 'techno', 'house'
            ]
            
            genre_activity = []
            
            for subreddit_name in genre_subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    # Get subscriber count and active users
                    subscribers = subreddit.subscribers
                    active_users = subreddit.active_user_count if hasattr(subreddit, 'active_user_count') else 0
                    
                    # Calculate activity score (active users as percentage of subscribers)
                    activity_score = (active_users / subscribers * 100) if subscribers > 0 else 0
                    
                    # Get recent posts
                    recent_posts = list(subreddit.new(limit=10))
                    recent_post_count = len(recent_posts)
                    
                    # Calculate average score of recent posts
                    avg_score = sum(post.score for post in recent_posts) / recent_post_count if recent_post_count > 0 else 0
                    
                    # Format genre name
                    genre_name = subreddit_name
                    if genre_name == 'hiphopheads':
                        genre_name = 'Hip Hop'
                    elif genre_name == 'indieheads':
                        genre_name = 'Indie'
                    elif genre_name == 'popheads':
                        genre_name = 'Pop'
                    elif genre_name == 'electronicmusic':
                        genre_name = 'Electronic'
                    elif genre_name == 'classicalmusic':
                        genre_name = 'Classical'
                    elif genre_name == 'folkmusic':
                        genre_name = 'Folk'
                    else:
                        genre_name = genre_name.replace('music', '').title()
                    
                    genre_activity.append({
                        'genre': genre_name,
                        'subscribers': subscribers,
                        'active_users': active_users,
                        'activity_score': activity_score,
                        'avg_post_score': avg_score,
                        'source': 'reddit'
                    })
                
                except Exception as e:
                    logger.error(f"Error getting activity for r/{subreddit_name}: {str(e)}")
            
            # Sort by activity score and limit results
            genre_activity.sort(key=lambda x: x['activity_score'], reverse=True)
            
            return genre_activity[:limit]
        
        except Exception as e:
            logger.error(f"Error getting genre trends from Reddit: {str(e)}")
            return []
    
    def search_reddit_for_song(self, artist, title, limit=5):
        """Search Reddit for discussions about a specific song.
        
        Args:
            artist (str): Artist name
            title (str): Song title
            limit (int, optional): Maximum number of results to return
            
        Returns:
            list: List of Reddit posts about the song
        """
        try:
            if not self.reddit:
                raise Exception("Reddit client not initialized")
            
            query = f'"{artist}" "{title}"'
            
            results = []
            
            for submission in self.reddit.subreddit('all').search(query, limit=limit*2):
                results.append({
                    'title': submission.title,
                    'subreddit': submission.subreddit.display_name,
                    'score': submission.score,
                    'url': submission.url,
                    'permalink': f"https://www.reddit.com{submission.permalink}",
                    'created_utc': submission.created_utc,
                    'source': 'reddit'
                })
            
            # Sort by score and limit results
            results.sort(key=lambda x: x['score'], reverse=True)
            
            return results[:limit]
        
        except Exception as e:
            logger.error(f"Error searching Reddit for {artist} - {title}: {str(e)}")
            return []
