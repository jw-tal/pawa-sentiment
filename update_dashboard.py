#!/usr/bin/env python3
"""
Automated Dashboard Update Script
Runs via GitHub Actions to collect YouTube data and update dashboard
"""

import os
import json
import time
from datetime import datetime
from googleapiclient.discovery import build
from textblob import TextBlob

# Get API key from environment variable (set in GitHub Secrets)
API_KEY = os.environ.get('YOUTUBE_API_KEY')

def analyze_sentiment(text):
    """Analyze sentiment using TextBlob"""
    try:
        analysis = TextBlob(text)
        polarity = analysis.sentiment.polarity
        
        if polarity > 0.1:
            return 'Positive', polarity
        elif polarity < -0.1:
            return 'Negative', polarity
        else:
            return 'Neutral', polarity
    except:
        return 'Neutral', 0.0

def get_channel_id(youtube):
    """Get Pawa TV channel ID"""
    try:
        search_response = youtube.search().list(
            part='snippet',
            q='watchpawatv',
            type='channel',
            maxResults=1
        ).execute()
        
        if search_response['items']:
            return search_response['items'][0]['snippet']['channelId']
        return None
    except Exception as e:
        print(f"Error getting channel ID: {str(e)}")
        return None

def fetch_all_comments_from_video(youtube, video_id):
    """Fetch ALL comments from a video with pagination"""
    all_comments = []
    next_page_token = None
    
    while True:
        try:
            comments_response = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=100,
                pageToken=next_page_token,
                textFormat='plainText'
            ).execute()
            
            all_comments.extend(comments_response.get('items', []))
            next_page_token = comments_response.get('nextPageToken')
            
            if not next_page_token:
                break
                
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error fetching comments: {str(e)}")
            break
    
    return all_comments

def collect_youtube_data():
    """Main function to collect YouTube data"""
    print("🚀 Starting YouTube data collection...")
    
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        print("✓ API connection established")
    except Exception as e:
        print(f"✗ API Error: {str(e)}")
        return None
    
    # Get channel ID
    channel_id = get_channel_id(youtube)
    
    if not channel_id:
        print("✗ Could not find Pawa TV channel")
        # Fallback: search directly
        try:
            search_response = youtube.search().list(
                part='id,snippet',
                q='Pawa TV Papua New Guinea',
                type='video',
                maxResults=15,
                order='date'
            ).execute()
            videos = [(item['id']['videoId'], item['snippet']['title']) 
                      for item in search_response.get('items', [])]
        except Exception as e:
            print(f"✗ Search failed: {str(e)}")
            return None
    else:
        print(f"✓ Found channel: {channel_id}")
        
        try:
            search_response = youtube.search().list(
                part='id,snippet',
                channelId=channel_id,
                maxResults=15,
                order='date',
                type='video'
            ).execute()
            videos = [(item['id']['videoId'], item['snippet']['title']) 
                      for item in search_response.get('items', [])]
        except Exception as e:
            print(f"✗ Error fetching videos: {str(e)}")
            return None
    
    print(f"✓ Found {len(videos)} recent videos")
    
    if not videos:
        print("✗ No videos found")
        return None
    
    # Collect comments from all videos
    all_comments = []
    
    for idx, (video_id, video_title) in enumerate(videos, 1):
        print(f"[{idx}/{len(videos)}] {video_title[:50]}...")
        
        video_comments = fetch_all_comments_from_video(youtube, video_id)
        
        if video_comments:
            for item in video_comments:
                comment = item['snippet']['topLevelComment']['snippet']
                comment_text = comment['textDisplay']
                author = comment['authorDisplayName']
                
                sentiment, score = analyze_sentiment(comment_text)
                
                all_comments.append({
                    'text': comment_text,
                    'author': author,
                    'sentiment': sentiment,
                    'score': score,
                    'video_id': video_id,
                    'video_title': video_title
                })
            
            print(f"  ✓ Collected {len(video_comments)} comments")
        else:
            print(f"  ⚠ No comments")
    
    return all_comments

def calculate_statistics(comments):
    """Calculate sentiment statistics"""
    if not comments:
        return {
            'total': 0,
            'positive': 0,
            'negative': 0,
            'neutral': 0,
            'positive_pct': 0,
            'negative_pct': 0,
            'neutral_pct': 0
        }
    
    total = len(comments)
    positive = sum(1 for c in comments if c['sentiment'] == 'Positive')
    negative = sum(1 for c in comments if c['sentiment'] == 'Negative')
    neutral = sum(1 for c in comments if c['sentiment'] == 'Neutral')
    
    return {
        'total': total,
        'positive': positive,
        'negative': negative,
        'neutral': neutral,
        'positive_pct': (positive / total * 100) if total > 0 else 0,
        'negative_pct': (negative / total * 100) if total > 0 else 0,
        'neutral_pct': (neutral / total * 100) if total > 0 else 0
    }

def generate_recommendations(stats):
    """Generate AI recommendations"""
    recommendations = []
    
    if stats['positive_pct'] > 60:
        recommendations.append("✓ Strong positive sentiment - audience is highly engaged")
        recommendations.append("→ Consider increasing content frequency to maintain momentum")
    elif stats['negative_pct'] > 30:
        recommendations.append("⚠ Elevated negative sentiment detected")
        recommendations.append("→ Review recent content and address audience concerns")
    
    if stats['neutral_pct'] > 60:
        recommendations.append("→ High neutral sentiment - opportunity for deeper engagement")
        recommendations.append("→ Consider more interactive content to boost positive response")
    
    if not recommendations:
        recommendations.append("→ Sentiment distribution is balanced")
        recommendations.append("→ Continue current content strategy")
    
    return recommendations

def save_dashboard_data(comments, stats):
    """Save data for dashboard"""
    print("\n💾 Saving data...")
    
    # Get top comments
    positive_comments = [c for c in comments if c['sentiment'] == 'Positive']
    negative_comments = [c for c in comments if c['sentiment'] == 'Negative']
    
    positive_comments.sort(key=lambda x: x['score'], reverse=True)
    negative_comments.sort(key=lambda x: x['score'])
    
    dashboard_data = {
        'timestamp': datetime.now().isoformat(),
        'lastUpdated': datetime.now().strftime('%d/%m/%Y, %H:%M:%S'),
        'stats': stats,
        'recommendations': generate_recommendations(stats),
        'topPositive': [
            {'text': c['text'], 'author': c['author'], 'score': c['score']}
            for c in positive_comments[:10]
        ],
        'topNegative': [
            {'text': c['text'], 'author': c['author'], 'score': c['score']}
            for c in negative_comments[:10]
        ],
        'allComments': comments[:100]
    }
    
    with open('youtube_dashboard_data.json', 'w', encoding='utf-8') as f:
        json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
    
    print("✓ Data saved to youtube_dashboard_data.json")
    return True

def main():
    """Main execution"""
    print("=" * 60)
    print("PAWA TV DASHBOARD AUTO-UPDATE")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    if not API_KEY:
        print("✗ ERROR: YOUTUBE_API_KEY not found in environment")
        return False
    
    # Collect data
    comments = collect_youtube_data()
    
    if not comments:
        print("\n✗ Failed to collect data")
        return False
    
    # Calculate stats
    stats = calculate_statistics(comments)
    print(f"\n📊 Results:")
    print(f"   Total: {stats['total']} comments")
    print(f"   Positive: {stats['positive']} ({stats['positive_pct']:.1f}%)")
    print(f"   Negative: {stats['negative']} ({stats['negative_pct']:.1f}%)")
    print(f"   Neutral: {stats['neutral']} ({stats['neutral_pct']:.1f}%)")
    
    # Save data
    success = save_dashboard_data(comments, stats)
    
    if success:
        print("\n✅ Dashboard update complete!")
        return True
    else:
        print("\n✗ Failed to save data")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
