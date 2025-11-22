from detoxify import Detoxify
from typing import Dict


class ToxicityDetector:
    def __init__(self):
        self.model = Detoxify('original')
    
    def detect(self, text: str) -> Dict[str, float]:
        try:
            results = self.model.predict(text)
            return {
                'toxicity': float(results['toxicity']),
                'severe_toxicity': float(results['severe_toxicity']),
                'obscene': float(results['obscene']),
                'threat': float(results['threat']),
                'insult': float(results['insult']),
                'identity_attack': float(results['identity_attack'])
            }
        except Exception as e:
            print(f"Toxicity detection error: {e}")
            return {
                'toxicity': 0.0,
                'severe_toxicity': 0.0,
                'obscene': 0.0,
                'threat': 0.0,
                'insult': 0.0,
                'identity_attack': 0.0
            }


# Singleton instance
_toxicity_detector = None

def get_toxicity_detector() -> ToxicityDetector:
    global _toxicity_detector
    if _toxicity_detector is None:
        _toxicity_detector = ToxicityDetector()
    return _toxicity_detector