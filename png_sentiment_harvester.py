"""
PNG Sentiment Harvester - FIXED VERSION with Contextual Negation
Analyzes sentiment in PNG comments with Tok Pisin support and proper negation handling
"""

import re
from typing import Dict, List, Tuple
from collections import defaultdict


class PNGSentimentLexicon:
    """Lexicon of PNG-specific sentiment terms"""
    
    # Negation words
    NEGATION_WORDS = {'not', 'no', 'never', 'none', 'nobody', 'nothing', 'neither', 'nowhere', 'hardly', 'barely',
                      'ino', 'nogat', 'nomore'}
    
    # Amplifiers
    AMPLIFIERS = {'very', 'really', 'extremely', 'absolutely', 'incredibly', 'totally', 'completely',
                  'tumas', 'tru', 'stret', 'much', 'so', 'too'}
    
    # Diminishers
    DIMINISHERS = {'slightly', 'somewhat', 'kind of', 'sort of', 'a bit', 'a little',
                   'liklik', 'smol', 'small'}
    
    # Brand terms
    BRAND_TERMS = ['pawa tv', 'pawa', 'pawatv']
    
    # PNG locations
    PNG_LOCATIONS = ['png', 'papua new guinea', 'port moresby', 'lae', 'madang', 'goroka', 
                     'mount hagen', 'rabaul', 'wewak', 'highlands', 'momase', 'niugini']
    
    # English positive terms
    ENGLISH_POSITIVE_STRONG = ['excellent', 'outstanding', 'brilliant', 'fantastic', 'wonderful', 
                               'amazing', 'superb', 'perfect', 'incredible', 'phenomenal',
                               'awesome', 'extraordinary', 'exceptional', 'magnificent']
    
    ENGLISH_POSITIVE_MODERATE = ['good', 'great', 'nice', 'love', 'like', 'enjoy', 'appreciate',
                                 'happy', 'glad', 'pleased', 'thanks', 'thank', 'helpful',
                                 'useful', 'informative', 'interesting', 'beautiful', 'well done']
    
    ENGLISH_POSITIVE_LIGHT = ['okay', 'ok', 'alright', 'fine', 'decent', 'fair', 'acceptable']
    
    # English negative terms
    ENGLISH_NEGATIVE_STRONG = ['terrible', 'horrible', 'awful', 'disgusting', 'pathetic', 'atrocious',
                               'abysmal', 'dreadful', 'appalling', 'outrageous', 'unacceptable',
                               'worthless', 'useless', 'garbage', 'trash', 'crap']
    
    ENGLISH_NEGATIVE_MODERATE = ['bad', 'poor', 'disappointing', 'weak', 'inadequate', 'inferior',
                                 'subpar', 'lacking', 'dislike', 'hate', 'annoying', 'frustrating',
                                 'concerning', 'worried', 'sad', 'upset', 'angry']
    
    ENGLISH_NEGATIVE_LIGHT = ['meh', 'mediocre', 'average', 'so-so', 'nothing special', 'boring']
    
    # Tok Pisin positive terms
    TOK_PISIN_POSITIVE_STRONG = ['trupla', 'gut tumas', 'nambawan', 'tru ya', 'stret tumas',
                                 'planti gut', 'tupela gut']
    
    TOK_PISIN_POSITIVE_MODERATE = ['em nau', 'naispla', 'gutpela', 'orait tumas', 'ino bagarap',
                                   'em stret', 'em gut', 'mi laikim', 'pawa', 'strong']
    
    TOK_PISIN_POSITIVE_LIGHT = ['orait', 'em tasol', 'stret', 'olgeta gut']
    
    # Tok Pisin negative terms
    TOK_PISIN_NEGATIVE_STRONG = ['giaman', 'lus lulu', 'nogut tumas', 'pinis', 'bagarap tumas',
                                 'rabis tumas', 'ino gut tru']
    
    TOK_PISIN_NEGATIVE_MODERATE = ['nogut', 'ino stret', 'ino gutpela', 'bagarap', 'rabis',
                                   'mi no laikim', 'ino orait', 'wari']
    
    TOK_PISIN_NEGATIVE_LIGHT = ['ino stap gut', 'liklik problem', 'ino nambawan']
    
    # PNG English (unique expressions)
    PNG_ENGLISH_POSITIVE = ['proper good', 'well well', 'number one', 'straight up good',
                            'too much good', 'very very good']
    
    PNG_ENGLISH_NEGATIVE = ['proper bad', 'straight up bad', 'no good at all', 'very very bad',
                            'too much bad']


class PNGSentimentHarvester:
    """
    PNG-aware sentiment analyzer with contextual negation handling
    """
    
    def __init__(self):
        self.lexicon = PNGSentimentLexicon()
        self.categories = self._build_categories()
    
    def _build_categories(self) -> Dict:
        """Build weighted categories from lexicon"""
        return {
            'english_positive_strong': {
                'weight': 1.8,
                'terms': self.lexicon.ENGLISH_POSITIVE_STRONG
            },
            'english_positive_moderate': {
                'weight': 1.2,
                'terms': self.lexicon.ENGLISH_POSITIVE_MODERATE
            },
            'english_positive_light': {
                'weight': 0.7,
                'terms': self.lexicon.ENGLISH_POSITIVE_LIGHT
            },
            'english_negative_strong': {
                'weight': -1.8,
                'terms': self.lexicon.ENGLISH_NEGATIVE_STRONG
            },
            'english_negative_moderate': {
                'weight': -1.2,
                'terms': self.lexicon.ENGLISH_NEGATIVE_MODERATE
            },
            'english_negative_light': {
                'weight': -0.7,
                'terms': self.lexicon.ENGLISH_NEGATIVE_LIGHT
            },
            'tok_pisin_positive_strong': {
                'weight': 1.7,
                'terms': self.lexicon.TOK_PISIN_POSITIVE_STRONG
            },
            'tok_pisin_positive_moderate': {
                'weight': 1.2,
                'terms': self.lexicon.TOK_PISIN_POSITIVE_MODERATE
            },
            'tok_pisin_positive_light': {
                'weight': 0.8,
                'terms': self.lexicon.TOK_PISIN_POSITIVE_LIGHT
            },
            'tok_pisin_negative_strong': {
                'weight': -1.8,
                'terms': self.lexicon.TOK_PISIN_NEGATIVE_STRONG
            },
            'tok_pisin_negative_moderate': {
                'weight': -1.2,
                'terms': self.lexicon.TOK_PISIN_NEGATIVE_MODERATE
            },
            'tok_pisin_negative_light': {
                'weight': -0.7,
                'terms': self.lexicon.TOK_PISIN_NEGATIVE_LIGHT
            },
            'png_english_positive': {
                'weight': 1.5,
                'terms': self.lexicon.PNG_ENGLISH_POSITIVE
            },
            'png_english_negative': {
                'weight': -1.4,
                'terms': self.lexicon.PNG_ENGLISH_NEGATIVE
            }
        }
    
    def analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of text with PNG context"""
        if not text or not text.strip():
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
        
        # Score sentiment terms WITH POSITIONAL INFORMATION
        sentiment_scores = self._score_sentiment_terms_with_positions(text_lower, tokens, context_modifiers)
        
        # Apply contextual negation (FIXED VERSION)
        final_scores = self._apply_contextual_negation(
            tokens, 
            sentiment_scores['positive_terms'],
            sentiment_scores['negative_terms'],
            context_modifiers
        )
        
        positive_score = final_scores['positive']
        negative_score = final_scores['negative']
        
        # Detect sentiment clusters
        cluster_bonuses = self._detect_sentiment_clusters(text_lower, context_modifiers)
        positive_score += cluster_bonuses['positive']
        negative_score += cluster_bonuses['negative']
        
        # Calculate final score
        total_score = positive_score + negative_score
        total_magnitude = abs(positive_score) + abs(negative_score)
        
        # Determine sentiment category
        if abs(total_score) < 0.5:
            sentiment = 'Neutral'
            confidence = 'low' if total_magnitude < 1.0 else 'medium'
        elif total_score > 0:
            sentiment = 'Positive'
            confidence = 'high' if total_score > 2.0 else 'medium'
        else:
            sentiment = 'Negative'
            confidence = 'high' if total_score < -2.0 else 'medium'
        
        return {
            'sentiment': sentiment,
            'score': round(total_score, 2),
            'confidence': confidence,
            'details': {
                'positive_score': round(positive_score, 2),
                'negative_score': round(negative_score, 2),
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
    
    def _score_sentiment_terms_with_positions(self, text: str, tokens: List[str], 
                                             context_modifiers: Dict) -> Dict:
        """Score all sentiment terms and track their positions - FIXED VERSION"""
        positive_terms = []
        negative_terms = []
        matched_terms = {'positive': [], 'negative': []}
        
        for category_name, category_data in self.categories.items():
            weight = category_data['weight']
            terms = category_data['terms']
            
            for term in terms:
                # Find all matches and their positions
                if ' ' in term:
                    # Multi-word phrase
                    pattern = re.compile(re.escape(term), re.IGNORECASE)
                else:
                    # Single word with boundaries
                    pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
                
                for match in pattern.finditer(text):
                    # Calculate approximate token position
                    start_pos = match.start()
                    text_before = text[:start_pos]
                    token_position = len(text_before.split())
                    
                    term_data = {
                        'term': term,
                        'weight': weight,
                        'position': token_position,
                        'match_text': match.group()
                    }
                    
                    if weight > 0:
                        positive_terms.append(term_data)
                    else:
                        negative_terms.append(term_data)
        
        # Aggregate for matched_terms summary
        term_counts = defaultdict(lambda: {'weight': 0, 'count': 0})
        for term_data in positive_terms + negative_terms:
            key = term_data['term']
            term_counts[key]['weight'] = term_data['weight']
            term_counts[key]['count'] += 1
        
        for term, data in term_counts.items():
            if data['weight'] > 0:
                matched_terms['positive'].append({
                    'term': term,
                    'weight': data['weight'],
                    'count': data['count']
                })
            else:
                matched_terms['negative'].append({
                    'term': term,
                    'weight': data['weight'],
                    'count': data['count']
                })
        
        return {
            'positive_terms': positive_terms,
            'negative_terms': negative_terms,
            'matched_terms': matched_terms
        }
    
    def _apply_contextual_negation(self, tokens: List[str], positive_terms: List[Dict],
                                   negative_terms: List[Dict], modifiers: Dict) -> Dict:
        """
        Apply contextual negation - FIXED VERSION
        Only negates terms within 2 words AFTER a negation word
        """
        # Find negation positions
        negation_positions = []
        for i, token in enumerate(tokens):
            if token in self.lexicon.NEGATION_WORDS:
                negation_positions.append(i)
        
        positive_score = 0.0
        negative_score = 0.0
        
        # Process positive terms
        for term_data in positive_terms:
            weight = term_data['weight']
            position = term_data['position']
            
            # Check if within 2 words AFTER any negation (negation comes before the term)
            is_negated = any(0 < (position - neg_pos) <= 2 for neg_pos in negation_positions)
            
            if is_negated:
                # Flip to negative and amplify
                negative_score += weight * -1.2
            else:
                # Keep positive
                positive_score += weight
        
        # Process negative terms
        for term_data in negative_terms:
            weight = term_data['weight']  # Already negative
            position = term_data['position']
            
            # Check if within 2 words AFTER any negation
            is_negated = any(0 < (position - neg_pos) <= 2 for neg_pos in negation_positions)
            
            if is_negated:
                # Flip to positive and amplify
                positive_score += abs(weight) * 1.2
            else:
                # Keep negative
                negative_score += weight
        
        # Apply other modifiers (amplifiers, diminishers, etc.)
        modified_positive, modified_negative = self._apply_other_modifiers(
            positive_score, negative_score, modifiers
        )
        
        return {
            'positive': modified_positive,
            'negative': modified_negative
        }
    
    def _apply_other_modifiers(self, positive_score: float, negative_score: float,
                               modifiers: Dict) -> Tuple[float, float]:
        """Apply non-negation modifiers"""
        modified_positive = positive_score
        modified_negative = negative_score
        
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
        
        # All caps = emphasis (but reduce confidence due to potential spam)
        if modifiers['is_all_caps']:
            modified_positive *= 1.2
            modified_negative *= 1.2
        
        # Question mark = uncertainty
        if modifiers['has_question']:
            modified_positive *= 0.8
            modified_negative *= 0.8
        
        return modified_positive, modified_negative
    
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
    
    def analyze_batch(self, comments: List[str]) -> List[Dict]:
        """Analyze a batch of comments"""
        return [self.analyze_sentiment(comment) for comment in comments]
    
    def generate_summary(self, analyzed_comments: List[Dict]) -> Dict:
        """Generate summary statistics from analyzed comments"""
        if not analyzed_comments:
            return {
                'total': 0,
                'counts': {'positive': 0, 'negative': 0, 'neutral': 0},
                'percentages': {'positive': 0, 'negative': 0, 'neutral': 0},
                'average_score': 0.0,
                'top_positive': [],
                'top_negative': []
            }
        
        counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        scores = []
        
        for result in analyzed_comments:
            sentiment = result.get('sentiment', 'Neutral')
            counts[sentiment.lower()] += 1
            scores.append(result.get('score', 0))
        
        total = len(analyzed_comments)
        percentages = {
            'positive': round((counts['positive'] / total) * 100, 1),
            'negative': round((counts['negative'] / total) * 100, 1),
            'neutral': round((counts['neutral'] / total) * 100, 1)
        }
        
        # Sort by score to find top comments
        comments_with_scores = [(c.get('text', ''), c.get('score', 0), c.get('sentiment_score', c.get('score', 0)), 
                                c.get('confidence', 'unknown')) for c in analyzed_comments]
        
        top_positive = sorted([c for c in analyzed_comments if c.get('sentiment') == 'Positive'], 
                            key=lambda x: x.get('score', 0), reverse=True)[:5]
        top_negative = sorted([c for c in analyzed_comments if c.get('sentiment') == 'Negative'], 
                            key=lambda x: x.get('score', 0))[:5]
        
        return {
            'total': total,
            'counts': counts,
            'percentages': percentages,
            'average_score': round(sum(scores) / len(scores), 2) if scores else 0.0,
            'top_positive': top_positive,
            'top_negative': top_negative
        }


if __name__ == '__main__':
    # Test the contextual negation fix
    harvester = PNGSentimentHarvester()
    
    test_cases = [
        "Wonderful Pigin lyrics. Thanks, Oshen, for portraying the Tokpisin lyrics in your inspirational songs🎵...it's not the first really! But PNGuinean's a...",
        "This is wonderful! Not bad at all.",
        "Not good, actually terrible",
        "I love this, it's not boring",
        "The video is great but the audio is not clear",
        "Gutpela tumas! Em ino nogut."
    ]
    
    print("="*80)
    print("CONTEXTUAL NEGATION TEST - FIXED VERSION")
    print("="*80)
    
    for text in test_cases:
        result = harvester.analyze_sentiment(text)
        print(f"\nText: {text}")
        print(f"Score: {result['score']:.2f} | Sentiment: {result['sentiment']} | Confidence: {result['confidence']}")
