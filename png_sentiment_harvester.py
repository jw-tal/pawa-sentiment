#!/usr/bin/env python3
"""
PNG Sentiment Harvester - Python Implementation
Advanced sentiment analysis for Papua New Guinean content
Handles Tok Pisin, PNG English, and cultural nuances
"""

import re
from typing import Dict, List, Tuple

class PNGSentimentLexicon:
    """PNG-specific sentiment lexicon with weighted terms"""
    
    # ENGLISH - POSITIVE (weighted by intensity)
    POSITIVE_STRONG = {
        'weight': 1.8,
        'terms': ['excellent', 'outstanding', 'brilliant', 'perfect', 'amazing', 'fantastic', 
                 'incredible', 'wonderful', 'superb', 'exceptional', 'phenomenal', 'magnificent']
    }
    
    POSITIVE_MODERATE = {
        'weight': 1.2,
        'terms': ['good', 'great', 'nice', 'love', 'appreciate', 'enjoyed', 'liked', 'helpful',
                 'informative', 'interesting', 'well done', 'congrats', 'congratulations']
    }
    
    POSITIVE_LIGHT = {
        'weight': 0.7,
        'terms': ['okay', 'ok', 'alright', 'fine', 'decent', 'fair', 'satisfactory']
    }
    
    # ENGLISH - NEGATIVE (weighted by intensity)
    NEGATIVE_STRONG = {
        'weight': -1.8,
        'terms': ['terrible', 'horrible', 'awful', 'disgusting', 'pathetic', 'atrocious',
                 'appalling', 'dreadful', 'hate', 'worst', 'rubbish', 'trash', 'garbage']
    }
    
    NEGATIVE_MODERATE = {
        'weight': -1.2,
        'terms': ['bad', 'poor', 'disappointing', 'weak', 'lacking', 'inadequate',
                 'boring', 'dull', 'useless', 'waste', 'wrong', 'misleading', 'biased']
    }
    
    NEGATIVE_LIGHT = {
        'weight': -0.7,
        'terms': ['meh', 'mediocre', 'average', 'could be better', 'not great']
    }
    
    # TOK PISIN - POSITIVE
    TOKPISIN_POSITIVE_STRONG = {
        'weight': 1.7,
        'terms': ['trupla', 'gut tumas', 'nambawan', 'wanpela nambawan', 'bikpela gutpela',
                 'planti gutpela', 'tru ya', 'stret tumas']
    }
    
    TOKPISIN_POSITIVE_MODERATE = {
        'weight': 1.2,
        'terms': ['em nau', 'naispla', 'naispla wok', 'gutpela', 'gutpela tumas', 'orait tumas',
                 'pawa tumas', 'strong tumas', 'stretpela']
    }
    
    TOKPISIN_POSITIVE_LIGHT = {
        'weight': 0.8,
        'terms': ['orait', 'em tasol', 'stret', 'ino nogut', 'gutpela liklik']
    }
    
    # TOK PISIN - NEGATIVE
    TOKPISIN_NEGATIVE_STRONG = {
        'weight': -1.8,
        'terms': ['giaman', 'lus lulu', 'nogut tumas', 'pinis', 'taim bilong yu pinis',
                 'wanpla samting nating', 'rubbis tumas', 'kranki tumas']
    }
    
    TOKPISIN_NEGATIVE_MODERATE = {
        'weight': -1.2,
        'terms': ['nogut', 'nogat', 'ino stret', 'ino gutpela', 'les', 'wanpela rubbis',
                 'pait nating', 'rong', 'bagarap']
    }
    
    TOKPISIN_NEGATIVE_LIGHT = {
        'weight': -0.7,
        'terms': ['ino stap gut', 'liklik problem', 'ino strong']
    }
    
    # PNG ENGLISH VARIATIONS
    PNG_ENGLISH_POSITIVE = {
        'weight': 1.5,
        'terms': ['proper good', 'well well', 'number one', 'first class', 'top shelf',
                 'straight up good', 'really really good', 'too good']
    }
    
    PNG_ENGLISH_NEGATIVE = {
        'weight': -1.4,
        'terms': ['proper bad', 'straight up bad', 'no good at all', 'nothing special']
    }
    
    # CONTEXT MODIFIERS
    NEGATION_WORDS = ['not', 'no', 'never', 'nobody', 'nothing', 'neither', 'nowhere', 'none', 'ino']
    AMPLIFIERS = ['very', 'really', 'extremely', 'totally', 'absolutely', 'completely', 'tumas', 'strong']
    DIMINISHERS = ['somewhat', 'slightly', 'barely', 'hardly', 'liklik', 'smol']
    
    # BRAND & LOCATION TERMS
    BRAND_TERMS = ['pawa', 'pawa tv', 'watchpawatv', 'host', 'presenter', 'interview', 'show', 'program']
    PNG_LOCATIONS = ['png', 'papua', 'moresby', 'lae', 'madang', 'goroka', 'mt hagen', 'rabaul',
                    'wewak', 'kimbe', 'kokopo', 'arawa']


class PNGSentimentHarvester:
    """
    Advanced sentiment analyzer for PNG content
    Implements weighted scoring with cultural and linguistic awareness
    """
    
    def __init__(self):
        self.lexicon = PNGSentimentLexicon()
        self._compile_lexicon_categories()
    
    def _compile_lexicon_categories(self):
        """Pre-compile all lexicon categories for faster lookup"""
        self.categories = {}
        for attr_name in dir(self.lexicon):
            if attr_name.isupper() and not attr_name.startswith('_'):
                attr = getattr(self.lexicon, attr_name)
                if isinstance(attr, dict) and 'weight' in attr and 'terms' in attr:
                    self.categories[attr_name] = attr
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Main sentiment analysis function
        
        Args:
            text: Comment text to analyze
            
        Returns:
            Dictionary with sentiment, score, confidence, and details
        """
        if not text or len(text.strip()) < 3:
            return {
                'sentiment': 'Neutral',
                'score': 0.0,
                'confidence': 'low',
                'details': {}
            }
        
        text_lower = text.lower()
        tokens = self._tokenize(text_lower)
        
        # Detect context modifiers
        context_modifiers = self._detect_context_modifiers(text, text_lower, tokens)
        
        # Score sentiment terms
        sentiment_scores = self._score_sentiment_terms(text_lower, tokens, context_modifiers)
        positive_score = sentiment_scores['positive']
        negative_score = sentiment_scores['negative']
        
        # Detect sentiment clusters
        cluster_bonus = self._detect_sentiment_clusters(text_lower, context_modifiers)
        positive_score += cluster_bonus['positive']
        negative_score += cluster_bonus['negative']
        
        # Apply context modifiers
        modified_scores = self._apply_context_modifiers(
            positive_score,
            negative_score,
            context_modifiers
        )
        
        # Calculate final sentiment
        net_score = modified_scores['positive'] + modified_scores['negative']
        total_magnitude = abs(modified_scores['positive']) + abs(modified_scores['negative'])
        
        # Determine sentiment category
        if net_score > 0.5:
            sentiment = 'Positive'
        elif net_score < -0.5:
            sentiment = 'Negative'
        else:
            sentiment = 'Neutral'
        
        # Determine confidence
        confidence = 'low'
        if total_magnitude >= 3.0 and not context_modifiers['has_question']:
            confidence = 'high'
        elif total_magnitude >= 1.5:
            confidence = 'medium'
        
        # Reduce confidence for ambiguous contexts
        if context_modifiers['is_all_caps'] or context_modifiers['has_question']:
            confidence = 'medium' if confidence == 'high' else 'low'
        
        return {
            'sentiment': sentiment,
            'score': round(net_score, 2),
            'confidence': confidence,
            'details': {
                'positive_score': round(modified_scores['positive'], 2),
                'negative_score': round(modified_scores['negative'], 2),
                'total_magnitude': round(total_magnitude, 2),
                'context_modifiers': context_modifiers,
                'matched_terms': sentiment_scores['matched_terms']
            }
        }
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        cleaned = re.sub(r'[^\w\s\']', ' ', text)
        return [t for t in cleaned.lower().split() if len(t) > 0]
    
    def _detect_context_modifiers(self, text: str, text_lower: str, tokens: List[str]) -> Dict:
        """Detect various context modifiers in the text"""
        return {
            'has_negation': any(word in tokens for word in self.lexicon.NEGATION_WORDS),
            'has_amplifier': any(word in tokens for word in self.lexicon.AMPLIFIERS),
            'has_diminisher': any(word in tokens for word in self.lexicon.DIMINISHERS),
            'has_brand': any(term in text_lower for term in self.lexicon.BRAND_TERMS),
            'has_location': any(loc in text_lower for loc in self.lexicon.PNG_LOCATIONS),
            'exclamation_count': text.count('!'),
            'is_all_caps': text.isupper() and len(text) > 10,
            'has_question': '?' in text
        }
    
    def _score_sentiment_terms(self, text: str, tokens: List[str], context_modifiers: Dict) -> Dict:
        """Score all sentiment terms found in text"""
        positive_score = 0.0
        negative_score = 0.0
        matched_terms = {'positive': [], 'negative': []}
        
        for category_name, category_data in self.categories.items():
            weight = category_data['weight']
            terms = category_data['terms']
            
            for term in terms:
                # Use word boundary for single words, substring for phrases
                if ' ' in term:
                    pattern = re.compile(re.escape(term), re.IGNORECASE)
                else:
                    pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
                
                matches = pattern.findall(text)
                if matches:
                    match_count = len(matches)
                    score = weight * match_count
                    
                    if weight > 0:
                        positive_score += score
                        matched_terms['positive'].append({
                            'term': term,
                            'weight': weight,
                            'count': match_count
                        })
                    else:
                        negative_score += score
                        matched_terms['negative'].append({
                            'term': term,
                            'weight': weight,
                            'count': match_count
                        })
        
        return {
            'positive': positive_score,
            'negative': negative_score,
            'matched_terms': matched_terms
        }
    
    def _detect_sentiment_clusters(self, text: str, context_modifiers: Dict) -> Dict:
        """Detect phrase clusters that indicate stronger sentiment"""
        positive_bonus = 0.0
        negative_bonus = 0.0
        
        # Brand + Positive sentiment = bonus
        if context_modifiers['has_brand']:
            brand_positive_patterns = [
                r'pawa\s+(tv\s+)?(is|was|em)\s+(good|great|excellent|gutpela|naispla)',
                r'(love|like|enjoy)\s+pawa',
                r'pawa\s+\w+\s+(tru|stret|nau)'
            ]
            
            for pattern in brand_positive_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    positive_bonus += 0.5
            
            brand_negative_patterns = [
                r'pawa\s+(tv\s+)?(is|was|em)\s+(bad|terrible|nogut|giaman)',
                r'(hate|dislike)\s+pawa'
            ]
            
            for pattern in brand_negative_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    negative_bonus -= 0.5
        
        # PNG Location + Positive = local pride bonus
        if context_modifiers['has_location']:
            location_pride_patterns = [
                r'png\s+(proud|strong|number\s+one)',
                r'(proud|gutpela)\s+\w+\s+png'
            ]
            
            for pattern in location_pride_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    positive_bonus += 0.3
        
        # Constructive feedback detection
        constructive_patterns = [
            r'(could|should|need\s+to|maybe)\s+\w+\s+(improve|better|more)',
            r'good\s+but',
            r'like\s+\w+\s+but'
        ]
        
        is_constructive = any(re.search(p, text, re.IGNORECASE) for p in constructive_patterns)
        if is_constructive:
            positive_bonus += 0.4
        
        return {'positive': positive_bonus, 'negative': negative_bonus}
    
    def _apply_context_modifiers(self, positive_score: float, negative_score: float, 
                                 modifiers: Dict) -> Dict:
        """Apply context modifiers to sentiment scores"""
        modified_positive = positive_score
        modified_negative = negative_score
        
        # Negation - flip and amplify
        if modifiers['has_negation']:
            modified_positive = negative_score * -1.2
            modified_negative = positive_score * -1.2
        
        # Amplifiers boost magnitude
        if modifiers['has_amplifier']:
            modified_positive *= 1.3
            modified_negative *= 1.3
        
        # Diminishers reduce magnitude
        if modifiers['has_diminisher']:
            modified_positive *= 0.7
            modified_negative *= 0.7
        
        # Multiple exclamation marks = stronger emotion
        if modifiers['exclamation_count'] >= 2:
            boost = min(1.0 + (modifiers['exclamation_count'] * 0.1), 1.5)
            modified_positive *= boost
            modified_negative *= boost
        
        # All caps = emphasis
        if modifiers['is_all_caps']:
            modified_positive *= 1.2
            modified_negative *= 1.2
        
        # Question mark = uncertainty
        if modifiers['has_question']:
            modified_positive *= 0.8
            modified_negative *= 0.8
        
        return {
            'positive': modified_positive,
            'negative': modified_negative
        }
    
    def analyze_batch(self, comments: List[Dict]) -> List[Dict]:
        """Analyze multiple comments at once"""
        results = []
        for comment in comments:
            analysis = self.analyze_sentiment(comment.get('text', ''))
            results.append({
                **comment,
                'sentiment': analysis['sentiment'],
                'sentiment_score': analysis['score'],
                'confidence': analysis['confidence'],
                'analysis_details': analysis['details']
            })
        return results
    
    def generate_summary(self, analyzed_comments: List[Dict]) -> Dict:
        """Generate summary statistics from analyzed comments"""
        if not analyzed_comments:
            return {
                'total': 0,
                'counts': {'positive': 0, 'negative': 0, 'neutral': 0},
                'percentages': {'positive': 0, 'negative': 0, 'neutral': 0}
            }
        
        total = len(analyzed_comments)
        counts = {
            'positive': sum(1 for c in analyzed_comments if c.get('sentiment') == 'Positive'),
            'negative': sum(1 for c in analyzed_comments if c.get('sentiment') == 'Negative'),
            'neutral': sum(1 for c in analyzed_comments if c.get('sentiment') == 'Neutral')
        }
        
        avg_score = sum(c.get('sentiment_score', 0) for c in analyzed_comments) / total
        
        top_positive = sorted(
            [c for c in analyzed_comments if c.get('sentiment') == 'Positive'],
            key=lambda x: x.get('sentiment_score', 0),
            reverse=True
        )[:10]
        
        top_negative = sorted(
            [c for c in analyzed_comments if c.get('sentiment') == 'Negative'],
            key=lambda x: x.get('sentiment_score', 0)
        )[:10]
        
        return {
            'total': total,
            'counts': counts,
            'percentages': {
                'positive': round((counts['positive'] / total) * 100, 1),
                'negative': round((counts['negative'] / total) * 100, 1),
                'neutral': round((counts['neutral'] / total) * 100, 1)
            },
            'average_score': round(avg_score, 2),
            'top_positive': top_positive,
            'top_negative': top_negative
        }


# Example usage and testing
if __name__ == '__main__':
    harvester = PNGSentimentHarvester()
    
    # Test cases
    test_comments = [
        {'id': 1, 'text': 'Em nau! Trupla gutpela wok ya, Pawa TV!', 'author': 'User1'},
        {'id': 2, 'text': 'This is giaman, nogut tumas', 'author': 'User2'},
        {'id': 3, 'text': 'Not bad, but could be better', 'author': 'User3'},
        {'id': 4, 'text': 'PAWA TV NUMBER ONE!!! 🔥🔥🔥', 'author': 'User4'},
        {'id': 5, 'text': 'Proper good interview bro, straight up', 'author': 'User5'},
        {'id': 6, 'text': 'Is this for real? Seems like rubbish to me', 'author': 'User6'},
        {'id': 7, 'text': 'PNG proud! Love what Pawa TV is doing', 'author': 'User7'}
    ]
    
    print('\n' + '='*70)
    print('PNG SENTIMENT HARVESTER - TEST RESULTS')
    print('='*70 + '\n')
    
    for comment in test_comments:
        result = harvester.analyze_sentiment(comment['text'])
        print(f"Comment: \"{comment['text']}\"")
        print(f"Result: {result['sentiment'].upper()} (score: {result['score']}, confidence: {result['confidence']})")
        print(f"Matched terms: {len(result['details']['matched_terms']['positive'])} positive, "
              f"{len(result['details']['matched_terms']['negative'])} negative")
        print('-'*70 + '\n')
