#!/usr/bin/env python3
"""
PNG Sentiment Harvester - Multi-Channel Test
Analyzes multiple PNG YouTube channels to demonstrate the harvester's capabilities
"""

import os
import json
import time
from datetime import datetime
from googleapiclient.discovery import build
from png_sentiment_harvester import PNGSentimentHarvester

# Get API key
API_KEY = os.environ.get('YOUTUBE_API_KEY', 'AIzaSyADo2tQwp44BI1eRkGfwyn-C-5VxpyLOyE')

# Initialize harvester
harvester = PNGSentimentHarvester()

# Test channels
TEST_CHANNELS = [
    {'name': 'EMTV Online', 'url': 'https://www.youtube.com/@emtvonline', 'skip': False},
    {'name': 'TVWAN Online', 'url': 'https://www.youtube.com/@TVWANOnline', 'skip': False},
    {'name': 'NBC PNG', 'url': 'https://www.youtube.com/@nbcpng9354', 'skip': False},
    {'name': 'Post Courier', 'url': 'https://www.youtube.com/@PostcourierOnline', 'skip': True},  # SKIP: Too many videos (20k+), run separately
    {'name': 'Tonton Malele', 'url': 'https://www.youtube.com/@tonton_malele', 'skip': False},
    {'name': 'Kali D Official', 'url': 'https://www.youtube.com/@KaliDofficial', 'skip': False},
    {'name': 'O-Shen', 'url': 'https://www.youtube.com/@OSHENOfficial', 'skip': False},
    {'name': 'Sprigga Mek', 'url': 'https://www.youtube.com/@spriggamekmusic', 'skip': False},
    {'name': 'L Saiikay', 'url': 'https://www.youtube.com/@lsaiikay', 'skip': False},
    {'name': 'Kabbage Gang', 'url': 'https://www.youtube.com/c/KabbageGangPNG', 'skip': False},
    {'name': 'Steamships', 'url': 'https://www.youtube.com/@steamshipstradingcompanylt8100', 'skip': False}
]

def get_channel_id_from_url(youtube, url):
    """Extract channel ID from URL using multiple methods"""
    
    # Method 1: Direct channel ID in URL (e.g., /channel/UCxxxxx)
    if '/channel/' in url:
        try:
            channel_id = url.split('/channel/')[1].strip('/').split('?')[0]
            print(f"  ✓ Extracted channel ID from URL: {channel_id}")
            return channel_id
        except:
            pass
    
    # Method 2: Handle/username (@username or /c/username)
    handle = None
    if '/@' in url:
        handle = url.split('/@')[1].strip('/').split('?')[0]
    elif '/c/' in url:
        handle = url.split('/c/')[1].strip('/').split('?')[0]
    elif '/user/' in url:
        handle = url.split('/user/')[1].strip('/').split('?')[0]
    
    if handle:
        # Try forUsername API
        try:
            channel_response = youtube.channels().list(
                part='id',
                forUsername=handle
            ).execute()
            
            if channel_response.get('items'):
                channel_id = channel_response['items'][0]['id']
                print(f"  ✓ Found channel ID via forUsername: {channel_id}")
                return channel_id
        except Exception as e:
            pass
        
        # Fallback: Search for the channel
        try:
            search_response = youtube.search().list(
                part='snippet',
                q=handle,
                type='channel',
                maxResults=5
            ).execute()
            
            # Try to find exact match
            for item in search_response.get('items', []):
                channel_title = item['snippet']['channelTitle'].lower()
                if handle.lower() in channel_title or channel_title in handle.lower():
                    channel_id = item['snippet']['channelId']
                    print(f"  ✓ Found channel ID via search: {channel_id}")
                    return channel_id
            
            # If no exact match, use first result
            if search_response.get('items'):
                channel_id = search_response['items'][0]['snippet']['channelId']
                print(f"  ⚠ Using best match channel ID: {channel_id}")
                return channel_id
                
        except Exception as e:
            print(f"  Error searching for channel: {str(e)}")
    
    print(f"  ✗ Could not extract channel ID from URL")
    return None

def get_uploads_playlist_id(youtube, channel_id):
    """Get the uploads playlist ID for a channel"""
    try:
        channel_response = youtube.channels().list(
            part='contentDetails',
            id=channel_id
        ).execute()
        
        if channel_response['items']:
            return channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    except Exception as e:
        print(f"  Error getting uploads playlist: {str(e)}")
    
    return None

def fetch_all_videos_from_channel(youtube, channel_id):
    """Fetch ALL videos from a channel using the uploads playlist (comprehensive method)"""
    all_videos = []
    
    # Get the uploads playlist ID
    uploads_playlist_id = get_uploads_playlist_id(youtube, channel_id)
    
    if not uploads_playlist_id:
        print("  ✗ Could not get uploads playlist")
        return []
    
    print("  ⏳ Fetching ALL videos from uploads playlist...")
    next_page_token = None
    page_count = 0
    
    while True:
        try:
            playlist_response = youtube.playlistItems().list(
                part='snippet',
                playlistId=uploads_playlist_id,
                maxResults=50,  # Max per page
                pageToken=next_page_token
            ).execute()
            
            page_count += 1
            
            for item in playlist_response.get('items', []):
                video_id = item['snippet']['resourceId']['videoId']
                video_title = item['snippet']['title']
                all_videos.append((video_id, video_title))
            
            # Progress indicator every 5 pages
            if page_count % 5 == 0:
                print(f"     Fetched {len(all_videos)} videos so far... (page {page_count})")
            
            next_page_token = playlist_response.get('nextPageToken')
            
            if not next_page_token:
                break
            
            time.sleep(0.3)  # Rate limiting
            
        except Exception as e:
            print(f"  ⚠ Error fetching videos page {page_count}: {str(e)}")
            break
    
    return all_videos

def fetch_all_comments_from_video(youtube, video_id, video_title):
    """Fetch ALL comments from a single video with pagination"""
    all_comments = []
    next_page_token = None
    
    while True:
        try:
            comments_response = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=100,  # Max per request
                pageToken=next_page_token,
                textFormat='plainText'
            ).execute()
            
            for item in comments_response.get('items', []):
                comment = item['snippet']['topLevelComment']['snippet']
                all_comments.append({
                    'text': comment['textDisplay'],
                    'author': comment['authorDisplayName'],
                    'video_title': video_title,
                    'video_id': video_id
                })
            
            next_page_token = comments_response.get('nextPageToken')
            
            if not next_page_token:
                break
            
            time.sleep(0.3)  # Rate limiting
            
        except Exception as e:
            # Video might have comments disabled
            break
    
    return all_comments

def fetch_comments_from_channel(youtube, channel_id):
    """Fetch ALL comments from ALL videos in a channel"""
    all_comments = []
    
    try:
        # Get ALL videos
        videos = fetch_all_videos_from_channel(youtube, channel_id)
        print(f"  ✓ Found {len(videos)} videos")
        
        if not videos:
            return []
        
        # Fetch ALL comments from each video
        print(f"  ⏳ Fetching all comments from {len(videos)} videos...")
        
        for idx, (video_id, video_title) in enumerate(videos, 1):
            video_comments = fetch_all_comments_from_video(youtube, video_id, video_title)
            
            if video_comments:
                all_comments.extend(video_comments)
                print(f"     [{idx}/{len(videos)}] {video_title[:50]}... → {len(video_comments)} comments")
            
            # Progress indicator every 10 videos
            if idx % 10 == 0:
                print(f"     Progress: {idx}/{len(videos)} videos | {len(all_comments)} total comments so far")
        
    except Exception as e:
        print(f"  Error fetching from channel: {str(e)}")
    
    return all_comments

def analyze_channel(youtube, channel_info, channel_number, total_channels):
    """Analyze a single channel"""
    print(f"\n{'='*70}")
    print(f"📺 [{channel_number}/{total_channels}] {channel_info['name']}")
    print(f"   {channel_info['url']}")
    print('='*70)
    
    start_time = time.time()
    
    # Get channel ID
    channel_id = get_channel_id_from_url(youtube, channel_info['url'])
    
    if not channel_id:
        print("  ✗ Could not find channel")
        return None
    
    # Fetch comments
    print("  ⏳ Starting comprehensive data collection...")
    comments = fetch_comments_from_channel(youtube, channel_id)
    
    elapsed_time = time.time() - start_time
    
    if not comments:
        print(f"  ✗ No comments found (took {elapsed_time:.0f} seconds)")
        return None
    
    print(f"  ✓ Collected {len(comments)} comments in {elapsed_time/60:.1f} minutes")
    
    # Analyze with PNG Harvester
    print("  🔍 Analyzing with PNG Sentiment Harvester...")
    analyzed_comments = harvester.analyze_batch(comments)
    
    # Generate summary
    summary = harvester.generate_summary(analyzed_comments)
    
    # Print results
    print(f"\n  📊 RESULTS:")
    print(f"     Total Comments: {summary['total']}")
    print(f"     Positive: {summary['counts']['positive']} ({summary['percentages']['positive']}%)")
    print(f"     Negative: {summary['counts']['negative']} ({summary['percentages']['negative']}%)")
    print(f"     Neutral: {summary['counts']['neutral']} ({summary['percentages']['neutral']}%)")
    print(f"     Average Score: {summary.get('average_score', 0):.2f}")
    
    # Show Tok Pisin detection
    tok_pisin_terms = ['em nau', 'trupla', 'gutpela', 'naispla', 'giaman', 'nogut', 
                       'orait', 'stret', 'lus lulu', 'nambawan', 'pawa']
    tok_pisin_comments = [c for c in analyzed_comments 
                         if any(term in c.get('text', '').lower() for term in tok_pisin_terms)]
    
    tok_pisin_pct = 0
    if tok_pisin_comments:
        tok_pisin_pct = (len(tok_pisin_comments) / len(analyzed_comments)) * 100
        print(f"     🇵🇬 Tok Pisin Comments: {len(tok_pisin_comments)} ({tok_pisin_pct:.1f}%)")
    
    # Show top positive and negative
    if summary['top_positive']:
        print(f"\n  😊 TOP POSITIVE COMMENT:")
        top = summary['top_positive'][0]
        print(f"     \"{top.get('text', '')[:100]}...\"")
        print(f"     Score: {top.get('sentiment_score', 0):.2f} | Confidence: {top.get('confidence', 'unknown')}")
    
    if summary['top_negative']:
        print(f"\n  😠 TOP NEGATIVE COMMENT:")
        top = summary['top_negative'][0]
        print(f"     \"{top.get('text', '')[:100]}...\"")
        print(f"     Score: {top.get('sentiment_score', 0):.2f} | Confidence: {top.get('confidence', 'unknown')}")
    
    return {
        'channel': channel_info['name'],
        'url': channel_info['url'],
        'summary': summary,
        'tok_pisin_percentage': tok_pisin_pct,
        'processing_time_minutes': elapsed_time / 60
    }

def main():
    """Main execution"""
    print("\n" + "="*70)
    print("PNG SENTIMENT HARVESTER - COMPREHENSIVE MULTI-CHANNEL TEST")
    print("Collecting ALL comments from ALL videos across ALL time")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Channels to test: {len(TEST_CHANNELS)}")
    print(f"\n⚠️  WARNING: This will take 15-30 minutes per channel!")
    print(f"⚠️  Total estimated time: 3-5 hours for all {len(TEST_CHANNELS)} channels")
    print(f"⚠️  Press Ctrl+C to stop at any time\n")
    
    # Initialize YouTube API
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
    except Exception as e:
        print(f"✗ API Error: {str(e)}")
        return
    
    # Analyze each channel
    results = []
    total_start_time = time.time()
    skipped_channels = []
    
    for idx, channel_info in enumerate(TEST_CHANNELS, 1):
        # Check if channel should be skipped
        if channel_info.get('skip', False):
            print(f"\n{'='*70}")
            print(f"⏭️  [{idx}/{len(TEST_CHANNELS)}] {channel_info['name']}")
            print(f"   SKIPPED (run separately - too large)")
            print('='*70)
            skipped_channels.append(channel_info['name'])
            continue
        
        try:
            result = analyze_channel(youtube, channel_info, idx, len(TEST_CHANNELS))
            if result:
                results.append(result)
                
                # Estimate remaining time
                avg_time = (time.time() - total_start_time) / len(results)
                remaining = len(TEST_CHANNELS) - idx - len(skipped_channels)
                est_remaining_minutes = (avg_time * remaining) / 60
                
                print(f"\n  ⏱️  Estimated time remaining: {est_remaining_minutes:.0f} minutes")
            
            time.sleep(2)  # Rate limiting between channels
            
        except KeyboardInterrupt:
            print("\n\n⚠️  INTERRUPTED BY USER")
            print(f"Processed {len(results)} of {len(TEST_CHANNELS)} channels")
            break
        except Exception as e:
            print(f"  ✗ Error analyzing channel: {str(e)}")
            continue
    
    # Print summary comparison
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)
    
    if results:
        # Sort by engagement
        results_sorted = sorted(results, key=lambda x: x['summary']['total'], reverse=True)
        
        print(f"\n{'Channel':<25} {'Comments':<10} {'Pos%':<8} {'Neg%':<8} {'Tok Pisin%':<12} {'Time(min)':<10}")
        print("-"*80)
        
        for r in results_sorted:
            print(f"{r['channel']:<25} "
                  f"{r['summary']['total']:<10} "
                  f"{r['summary']['percentages']['positive']:<8.1f} "
                  f"{r['summary']['percentages']['negative']:<8.1f} "
                  f"{r['tok_pisin_percentage']:<12.1f} "
                  f"{r.get('processing_time_minutes', 0):<10.1f}")
        
        # Best for Tok Pisin
        tok_pisin_sorted = sorted(results, key=lambda x: x['tok_pisin_percentage'], reverse=True)
        if tok_pisin_sorted[0]['tok_pisin_percentage'] > 0:
            print(f"\n🇵🇬 Most Tok Pisin Usage: {tok_pisin_sorted[0]['channel']} "
                  f"({tok_pisin_sorted[0]['tok_pisin_percentage']:.1f}%)")
        
        # Most positive
        positive_sorted = sorted(results, key=lambda x: x['summary']['percentages']['positive'], reverse=True)
        print(f"😊 Most Positive: {positive_sorted[0]['channel']} "
              f"({positive_sorted[0]['summary']['percentages']['positive']:.1f}%)")
        
        # Most negative
        negative_sorted = sorted(results, key=lambda x: x['summary']['percentages']['negative'], reverse=True)
        if negative_sorted[0]['summary']['percentages']['negative'] > 0:
            print(f"😠 Most Negative: {negative_sorted[0]['channel']} "
                  f"({negative_sorted[0]['summary']['percentages']['negative']:.1f}%)")
        
        # Save results
        with open('channel_comparison_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        total_comments = sum(r['summary']['total'] for r in results)
        total_time = sum(r.get('processing_time_minutes', 0) for r in results)
        
        print(f"\n📈 TOTALS:")
        print(f"   Channels analyzed: {len(results)}")
        if skipped_channels:
            print(f"   Channels skipped: {len(skipped_channels)} ({', '.join(skipped_channels)})")
        print(f"   Total comments collected: {total_comments:,}")
        print(f"   Total processing time: {total_time:.1f} minutes ({total_time/60:.1f} hours)")
        print(f"   Average per channel: {total_time/len(results):.1f} minutes")
        
        print(f"\n✓ Full results saved to: channel_comparison_results.json")
    
    print("\n" + "="*70)
    print("✅ MULTI-CHANNEL TEST COMPLETE")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
