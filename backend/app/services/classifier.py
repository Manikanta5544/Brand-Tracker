from transformers import pipeline
import torch
from typing import Dict
from ..core.config import settings


class ZeroShotClassifier:
    def __init__(self):
        self.device = 0 if torch.cuda.is_available() else -1
        self.classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=self.device
        )
        
        self.categories = [
            "Product Issue",
            "Pricing",
            "Complaint",
            "Praise",
            "Feature Request",
            "Comparison",
            "Review",
            "Question",
            "General"
        ]
    
    def classify(self, text: str) -> Dict[str, any]:
        try:
            text = text[:512]
            result = self.classifier(text, self.categories)
            
            return {
                'category': result['labels'][0],
                'score': result['scores'][0],
                'all_scores': dict(zip(result['labels'], result['scores']))
            }
        except Exception as e:
            print(f"Classification error: {e}")
            return {
                'category': 'General',
                'score': 0.5,
                'all_scores': {}
            }


# Singleton instance
_classifier = None

def get_classifier() -> ZeroShotClassifier:
    global _classifier
    if _classifier is None:
        _classifier = ZeroShotClassifier()
    return _classifier