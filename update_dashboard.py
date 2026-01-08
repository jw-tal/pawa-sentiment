#!/usr/bin/env python3
"""
Automated Dashboard Update Script with PNG Sentiment Harvester
Runs via GitHub Actions to collect YouTube data and update dashboard
Uses advanced PNG-aware sentiment analysis
"""

import os
import json
import time
from datetime import datetime
from googleapiclient.discovery import build

# Import PNG Sentiment Harvester
from png_sentiment_harvester import PNGSentimentHarvester

# Get API key from environment variable (set in GitHub Secrets)
API_KEY = os.environ.get('YOUTUBE_API_KEY')

# Initialize harvester
harvester = PNGSentimentHarvester()


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
    """Main function to collect YouTube data with PNG-aware sentiment analysis"""
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
                all_comments.append({
                    'text': comment['textDisplay'],
                    'author': comment['authorDisplayName'],
                    'video_id': video_id,
                    'video_title': video_title
                })
            
            print(f"  ✓ Collected {len(video_comments)} comments")
        else:
            print(f"  ⚠ No comments")
    
    return all_comments


def analyze_comments_with_harvester(comments):
    """Analyze comments using PNG Sentiment Harvester"""
    print(f"\n🔍 Analyzing {len(comments)} comments with PNG Sentiment Harvester...")
    
    analyzed_comments = harvester.analyze_batch(comments)
    
    # Print some insights
    high_confidence = [c for c in analyzed_comments if c.get('confidence') == 'high']
    print(f"✓ Analysis complete: {len(high_confidence)} high-confidence results")
    
    return analyzed_comments


def calculate_statistics(analyzed_comments):
    """Calculate sentiment statistics using harvester's summary"""
    summary = harvester.generate_summary(analyzed_comments)
    
    return {
        'total': summary['total'],
        'positive': summary['counts']['positive'],
        'negative': summary['counts']['negative'],
        'neutral': summary['counts']['neutral'],
        'positive_pct': summary['percentages']['positive'],
        'negative_pct': summary['percentages']['negative'],
        'neutral_pct': summary['percentages']['neutral'],
        'average_score': summary.get('average_score', 0)
    }


def generate_recommendations(stats, analyzed_comments):
    """Generate AI recommendations based on PNG-aware analysis"""
    recommendations = []
    
    pos_pct = stats['positive_pct']
    neg_pct = stats['negative_pct']
    neu_pct = stats['neutral_pct']
    
    # High confidence insights
    high_conf_positive = [c for c in analyzed_comments 
                         if c.get('sentiment') == 'Positive' and c.get('confidence') == 'high']
    high_conf_negative = [c for c in analyzed_comments 
                         if c.get('sentiment') == 'Negative' and c.get('confidence') == 'high']
    
    # Check for PNG-specific engagement
    tok_pisin_comments = [c for c in analyzed_comments 
                         if any(term in c.get('text', '').lower() 
                               for term in ['em nau', 'trupla', 'gutpela', 'naispla', 'giaman', 'nogut'])]
    
    # Analyze sentiment distribution
    if pos_pct > 60:
        recommendations.append(
            f"✓ Strong positive sentiment ({pos_pct:.1f}%) - PNG audience highly engaged. "
            f"Found {len(high_conf_positive)} high-confidence positive comments. "
            f"Continue current content strategy and increase posting frequency."
        )
    elif pos_pct > 40:
        recommendations.append(
            f"✓ Healthy positive engagement ({pos_pct:.1f}%). "
            f"Build on this momentum by responding to comments and creating similar content."
        )
    
    if neg_pct > 30:
        recommendations.append(
            f"⚠ Elevated negative sentiment ({neg_pct:.1f}%) detected. "
            f"Review {len(high_conf_negative)} high-confidence negative comments for specific concerns. "
            f"Consider addressing audience feedback in next video."
        )
    elif neg_pct > 15:
        recommendations.append(
            f"→ Moderate negative feedback ({neg_pct:.1f}%). "
            f"Monitor comments for constructive criticism and address concerns transparently."
        )
    
    if neu_pct > 60:
        recommendations.append(
            f"→ High neutral sentiment ({neu_pct:.1f}%) - opportunity for deeper engagement. "
            f"Add more calls-to-action and emotionally resonant content to convert neutral viewers."
        )
    
    # PNG-specific insights
    if tok_pisin_comments:
        tok_pisin_pct = (len(tok_pisin_comments) / stats['total']) * 100
        recommendations.append(
            f"🇵🇬 PNG Cultural Engagement: {tok_pisin_pct:.1f}% of comments use Tok Pisin or PNG English. "
            f"Strong local audience connection detected. Consider more PNG-focused content."
        )
    
    # Brand engagement
    brand_mentions = [c for c in analyzed_comments 
                     if 'pawa' in c.get('text', '').lower()]
    if brand_mentions:
        brand_pct = (len(brand_mentions) / stats['total']) * 100
        brand_positive = [c for c in brand_mentions if c.get('sentiment') == 'Positive']
        recommendations.append(
            f"📺 Brand Awareness: {brand_pct:.1f}% directly mention Pawa TV. "
            f"{len(brand_positive)} positive brand associations detected. Strong brand recognition."
        )
    
    # Community size recommendation
    if stats['total'] > 50:
        recommendations.append(
            f"📈 Active community with {stats['total']} comments. "
            f"Maintain engagement through regular responses and community features."
        )
    elif stats['total'] > 20:
        recommendations.append(
            f"🌱 Growing community ({stats['total']} comments). "
            f"Encourage discussion through strategic questions and community interaction."
        )
    else:
        recommendations.append(
            f"🎬 Early-stage engagement ({stats['total']} comments). "
            f"Focus on consistent posting and cross-platform promotion to build audience."
        )
    
    return recommendations


def save_dashboard_data(comments, stats):
    """Save data for dashboard"""
    print("\n💾 Saving data...")
    
    # Get top comments using harvester's summary
    summary = harvester.generate_summary(comments)
    
    dashboard_data = {
        'timestamp': datetime.now().isoformat(),
        'lastUpdated': datetime.now().strftime('%d/%m/%Y, %H:%M:%S'),
        'stats': stats,
        'recommendations': generate_recommendations(stats, comments),
        'topPositive': [
            {
                'text': c.get('text', ''),
                'author': c.get('author', ''),
                'score': c.get('sentiment_score', 0),
                'confidence': c.get('confidence', 'unknown')
            }
            for c in summary['top_positive']
        ],
        'topNegative': [
            {
                'text': c.get('text', ''),
                'author': c.get('author', ''),
                'score': c.get('sentiment_score', 0),
                'confidence': c.get('confidence', 'unknown')
            }
            for c in summary['top_negative']
        ],
        'allComments': comments[:100]  # Store first 100 for reference
    }
    
    with open('youtube_dashboard_data.json', 'w', encoding='utf-8') as f:
        json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
    
    print("✓ Data saved to youtube_dashboard_data.json")
    return True


def main():
    """Main execution with PNG Sentiment Harvester"""
    print("=" * 60)
    print("PAWA TV DASHBOARD AUTO-UPDATE (PNG-Enhanced)")
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
    
    # Analyze with PNG Sentiment Harvester
    analyzed_comments = analyze_comments_with_harvester(comments)
    
    # Calculate stats
    stats = calculate_statistics(analyzed_comments)
    print(f"\n📊 Results:")
    print(f"   Total: {stats['total']} comments")
    print(f"   Positive: {stats['positive']} ({stats['positive_pct']:.1f}%)")
    print(f"   Negative: {stats['negative']} ({stats['negative_pct']:.1f}%)")
    print(f"   Neutral: {stats['neutral']} ({stats['neutral_pct']:.1f}%)")
    print(f"   Average Score: {stats['average_score']:.2f}")
    
    # Save data
    success = save_dashboard_data(analyzed_comments, stats)
    
    if success:
        print("\n✅ Dashboard update complete with PNG-enhanced analysis!")
        return True
    else:
        print("\n✗ Failed to save data")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
