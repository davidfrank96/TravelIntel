"""
Data Cleaning and Normalization Module
"""
import re
import os
from pathlib import Path
from typing import List, Dict, Optional, Set
import pandas as pd
from datetime import datetime
import unicodedata
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from nltk.stem import WordNetLemmatizer
import nltk

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)


class DataCleaner:
    """Cleans and normalizes scraped travel advisory data"""
    
    # Risk level mappings for normalization
    RISK_LEVEL_MAPPING = {
        'level 1': 'Low Risk',
        'level 2': 'Exercise Increased Caution',
        'level 3': 'Reconsider Travel',
        'level 4': 'Do Not Travel',
        'exercise normal': 'Low Risk',
        'exercise increased': 'Exercise Increased Caution',
        'reconsider': 'Reconsider Travel',
        'do not travel': 'Do Not Travel',
        'advise against all travel': 'Do Not Travel',
        'all travel': 'Do Not Travel',
        'advise against all but essential travel': 'Reconsider Travel',
        'all but essential travel': 'Reconsider Travel',
        'avoid': 'Do Not Travel',
        'high': 'High Risk',
        'medium': 'Medium Risk',
        'low': 'Low Risk',
        'moderate': 'Medium Risk'
    }
    
    # Country name normalization (common variations)
    COUNTRY_NORMALIZATION = {
        'usa': 'United States',
        'us': 'United States',
        'u.s.': 'United States',
        'u.s.a.': 'United States',
        'uk': 'United Kingdom',
        'u.k.': 'United Kingdom',
        'britain': 'United Kingdom',
        'great britain': 'United Kingdom',
        'uae': 'United Arab Emirates',
        'russia': 'Russian Federation',
        'south korea': 'Republic of Korea',
        'north korea': "Democratic People's Republic of Korea",
        'dprk': "Democratic People's Republic of Korea"
    }
    
    def __init__(self):
        """Initialize data cleaner"""
        self._sentiment = SentimentIntensityAnalyzer()
        self._lemmatizer = WordNetLemmatizer()
        # Load external corpus/keyword lists if available
        self._corpus_keywords = set(self._load_corpus())
        
        # Define robust defaults for categorization
        self.DEFAULT_SECURITY = {'crime', 'terrorism', 'kidnap', 'armed', 'attack', 'robbery', 'violence', 'gang', 'cartel', 'carjacking', 'homicide', 'murder', 'shooting', 'extremist', 'hostage', 'bombing', 'assault', 'mugging', 'theft'}
        self.DEFAULT_SAFETY = {'health', 'disease', 'epidemic', 'pandemic', 'virus', 'earthquake', 'flood', 'tsunami', 'hurricane', 'cyclone', 'typhoon', 'landslide', 'medical', 'hospital', 'cholera', 'dengue', 'malaria', 'yellow fever', 'zika', 'accident'}
        self.DEFAULT_SERENITY = {'protest', 'demonstration', 'rally', 'march', 'unrest', 'riot', 'strike', 'political', 'tension', 'curfew', 'emergency', 'disruption', 'civil', 'instability'}

        # Load category-specific keywords
        self._security_keywords = self._load_category_keywords('data/wordlists/security.txt', self.DEFAULT_SECURITY)
        self._safety_keywords = self._load_category_keywords('data/wordlists/safety.txt', self.DEFAULT_SAFETY)
        self._serenity_keywords = self._load_category_keywords('data/wordlists/serenity.txt', self.DEFAULT_SERENITY)

    def _load_corpus(self, path: str = 'data/wordlists/corpus.txt') -> List[str]:
        """Load keyword corpus from a simple newline-delimited file.

        Falls back to the built-in travel keywords if the file is missing
        or cannot be read.
        """
        default = [
            'terrorism', 'crime', 'violence', 'civil unrest', 'natural disaster',
            'epidemic', 'pandemic', 'health', 'safety', 'security', 'travel ban',
            'quarantine', 'visa', 'border', 'entry', 'exit', 'restriction',
            'warning', 'alert', 'advisory', 'risk', 'danger', 'unsafe'
        ]

        try:
            p = Path(path)
            if p.is_file():
                with p.open('r', encoding='utf-8') as f:
                    lines = [ln.strip() for ln in f if ln.strip()]
                # normalize and deduplicate while preserving order
                cleaned = []
                for ln in lines:
                    low = ln.lower()
                    if low not in cleaned:
                        cleaned.append(low)
                # merge with defaults, defaults appended after file entries
                for d in default:
                    if d not in cleaned:
                        cleaned.append(d)
                return cleaned
        except Exception:
            pass

        return default
    
    def _load_category_keywords(self, path: str, defaults: Optional[Set[str]] = None) -> Set[str]:
        """Load category-specific keywords from file or use defaults."""
        keywords = set()
        if defaults:
            keywords.update(d.lower() for d in defaults)
        try:
            p = Path(path)
            if p.is_file():
                with p.open('r', encoding='utf-8') as f:
                    keywords.update(ln.strip().lower() for ln in f if ln.strip())
        except Exception:
            pass
        return keywords
    
    def normalize_country_name(self, country: str) -> str:
        """Normalize country names to standard format"""
        if not country:
            return 'Unknown'
        
        # Remove extra whitespace
        country = ' '.join(country.split())
        
        # Convert to lowercase for lookup
        country_lower = country.lower().strip()
        
        # Check normalization mapping
        if country_lower in self.COUNTRY_NORMALIZATION:
            return self.COUNTRY_NORMALIZATION[country_lower]
        
        # Remove common prefixes/suffixes
        country = re.sub(r'^the\s+', '', country, flags=re.IGNORECASE)
        
        # Title case normalization
        country = country.title()
        
        return country
    
    def normalize_risk_level(self, risk_level: str) -> Optional[str]:
        """Normalize risk levels to standard format"""
        if not risk_level:
            return None
        
        risk_lower = risk_level.lower().strip()
        
        # Check mapping
        for key, value in self.RISK_LEVEL_MAPPING.items():
            if key in risk_lower:
                return value
        
        # Default return original if no match
        return risk_level.title()
    
    def extract_risk_score(self, risk_level: str) -> int:
        """Extract numeric risk score from risk level (1-4 scale)"""
        risk_normalized = self.normalize_risk_level(risk_level)
        
        if not risk_normalized:
            return 0
        
        risk_lower = risk_normalized.lower()
        
        if (
            'do not travel' in risk_lower
            or 'level 4' in risk_lower
            or 'advise against all travel' in risk_lower
        ):
            return 4
        elif (
            'reconsider' in risk_lower
            or 'level 3' in risk_lower
            or 'all but essential travel' in risk_lower
        ):
            return 3
        elif 'exercise increased' in risk_lower or 'level 2' in risk_lower:
            return 2
        elif 'low' in risk_lower or 'level 1' in risk_lower or 'normal' in risk_lower:
            return 1
        else:
            return 0
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract important keywords from text using corpus and lemmatization"""
        if not text:
            return []
        text_lower = text.lower()
        found_keywords = []

        # Use external corpus if available, else built-in defaults are loaded
        # Sort by length descending to match longer phrases first
        for keyword in sorted(self._corpus_keywords, key=lambda s: -len(s)):
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        # Extract additional keywords (simple approach - can be enhanced with NLP)
        words = re.findall(r'\b[a-z]{4,}\b', text_lower)
        word_freq = {}
        for word in words:
            if word not in ['that', 'this', 'with', 'from', 'have', 'been', 'will', 'were']:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top words
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        additional_keywords = [word for word, freq in sorted_words[:max_keywords] 
                              if freq > 1]
        
        return list(set(found_keywords + additional_keywords))[:max_keywords]
    
    def calculate_corpus_grade(self, text: str) -> str:
        """
        Calculate an A-E grade based on the presence of risk-related corpus words.
        A = Lowest Risk (No/Few risk words)
        E = Highest Risk (Many risk words)
        """
        if not text:
            return 'A'
            
        text_lower = text.lower()
        
        # Aggregate all risk keywords
        all_keywords = self._corpus_keywords | self._security_keywords | self._safety_keywords | self._serenity_keywords
        
        # Count unique keywords present in the text
        hit_count = 0
        for kw in all_keywords:
            if kw in text_lower:
                hit_count += 1
                
        # Grading Scale based on keyword density
        if hit_count == 0:
            return 'A'
        elif hit_count <= 2:
            return 'B'
        elif hit_count <= 5:
            return 'C'
        elif hit_count <= 9:
            return 'D'
        else:
            return 'E'

    def categorize_advisory(self, text: str) -> Dict[str, bool]:
        """
        Categorize advisory by security, safety, and serenity concerns.
        
        Returns:
            Dict with 'security', 'safety', 'serenity' boolean flags
        """
        text_lower = text.lower()
        return {
            'has_security_concerns': any(kw in text_lower for kw in self._security_keywords),
            'has_safety_concerns': any(kw in text_lower for kw in self._safety_keywords),
            'has_serenity_concerns': any(kw in text_lower for kw in self._serenity_keywords),
        }
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ''
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:\-()]', '', text)
        
        # Normalize unicode
        text = unicodedata.normalize('NFKD', text)
        
        return text.strip()
    
    def parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None
        
        try:
            # Try ISO format first
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            pass
        
        # Try common date formats
        date_formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%B %d, %Y',
            '%d %B %Y',
            '%Y-%m-%d %H:%M:%S'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        
        return None
    
    def clean_advisory(self, advisory: Dict) -> Dict:
        """Clean a single advisory record"""
        cleaned = advisory.copy()
        
        # Normalize country
        cleaned['country_normalized'] = self.normalize_country_name(
            advisory.get('country', '')
        )
        
        # Normalize risk level
        risk_level = advisory.get('risk_level', '')
        cleaned['risk_level_normalized'] = self.normalize_risk_level(risk_level)
        cleaned['risk_score'] = self.extract_risk_score(risk_level)
        
        # Clean description
        description = advisory.get('description', '')
        cleaned['description_cleaned'] = self.clean_text(description)
        
        # Extract keywords
        full_text = f"{description} {risk_level}"
        cleaned['keywords'] = self.extract_keywords(full_text)
        
        # Categorize by concern type
        categories = self.categorize_advisory(full_text)
        cleaned.update(categories)
        
        # Sentiment (compound score -1..1 over advisory text)
        sentiment_source = cleaned['description_cleaned'] or description or ""
        if sentiment_source:
            scores = self._sentiment.polarity_scores(sentiment_source)
            cleaned['sentiment_score'] = scores.get('compound', 0.0)
        else:
            cleaned['sentiment_score'] = 0.0
        
        # Corpus-based Risk Grade (A-E)
        cleaned['corpus_risk_grade'] = self.calculate_corpus_grade(full_text)
        
        # Parse date
        date_str = advisory.get('date')
        cleaned['date_parsed'] = self.parse_date(date_str)
        
        return cleaned
    
    def clean_batch(self, advisories: List[Dict]) -> List[Dict]:
        """Clean a batch of advisories"""
        cleaned_advisories = []
        
        for advisory in advisories:
            try:
                cleaned = self.clean_advisory(advisory)
                cleaned_advisories.append(cleaned)
            except Exception as e:
                print(f"Error cleaning advisory: {e}")
                continue
        
        return cleaned_advisories
    
    def deduplicate(self, advisories: List[Dict]) -> List[Dict]:
        """Remove duplicate advisories with a stable fallback when date is missing."""
        seen = set()
        unique_advisories = []
        
        for advisory in advisories:
            source = advisory.get('source', '')
            country = advisory.get('country_normalized', advisory.get('country', ''))
            date_val = advisory.get('date_parsed') or advisory.get('date')

            if date_val:
                key = (source, country, str(date_val))
            else:
                # Most sources miss publication date; use content/url fallback to avoid duplicates.
                key = (
                    source,
                    country,
                    advisory.get('url', ''),
                    advisory.get('risk_level_normalized', advisory.get('risk_level', '')),
                    (advisory.get('description_cleaned') or advisory.get('description') or '')[:160]
                )
            
            if key not in seen:
                seen.add(key)
                unique_advisories.append(advisory)
        
        return unique_advisories
    
    def create_dataframe(self, advisories: List[Dict]) -> pd.DataFrame:
        """Convert cleaned advisories to pandas DataFrame"""
        df = pd.DataFrame(advisories)
        
        # Ensure date column is datetime
        if 'date_parsed' in df.columns:
            df['date'] = pd.to_datetime(df['date_parsed'], errors='coerce')
        
        return df
