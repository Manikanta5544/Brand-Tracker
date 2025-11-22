from transformers import pipeline
import torch
from typing import Dict
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        self.device = 0 if torch.cuda.is_available() else -1
        try:
            self.classifier = pipeline(
                "sentiment-analysis",
                model=settings.SENTIMENT_MODEL,
                device=self.device,
                truncation=True,
                max_length=512
            )
            logger.info("Sentiment analyzer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize sentiment analyzer: {e}")
            self.classifier = None
    
    def analyze(self, text: str) -> Dict[str, any]:
        if not text or not self.classifier:
            return self._default_sentiment()
        
        try:
            text = str(text).strip()[:512]
            if not text:
                return self._default_sentiment()
                
            result = self.classifier(text)[0]
            
            label = result['label']
            score = result['score']
            
            if label == 'POSITIVE':
                normalized_score = score
                sentiment = 'positive'
            elif label == 'NEGATIVE':
                normalized_score = -score
                sentiment = 'negative'
            else:
                normalized_score = 0.0
                sentiment = 'neutral'
            
            return {
                'sentiment': sentiment,
                'score': normalized_score,
                'confidence': score,
                'success': True
            }
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return self._default_sentiment()
    
    def _default_sentiment(self) -> Dict[str, any]:
        return {
            'sentiment': 'neutral',
            'score': 0.0,
            'confidence': 0.0,
            'success': False
        }


# Singleton instance with thread safety
_sentiment_analyzer = None
_analyzer_lock = None

def get_sentiment_analyzer() -> SentimentAnalyzer:
    global _sentiment_analyzer, _analyzer_lock
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer