from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from typing import List, Dict
from ..core.config import settings


class TopicDetector:
    def __init__(self):
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.n_clusters = 5
        self.vectorizer = TfidfVectorizer(max_features=10, stop_words='english')
    
    def detect_topics(self, texts: List[str]) -> List[Dict]:
        if len(texts) < self.n_clusters:
            return [{'topic': 'General', 'keywords': []}]
        
        try:
            embeddings = self.embedding_model.encode(texts)
            kmeans = KMeans(n_clusters=self.n_clusters, random_state=42)
            clusters = kmeans.fit_predict(embeddings)
            
            topics = []
            for i in range(self.n_clusters):
                cluster_texts = [texts[j] for j in range(len(texts)) if clusters[j] == i]
                
                if cluster_texts:
                    try:
                        tfidf_matrix = self.vectorizer.fit_transform(cluster_texts)
                        feature_names = self.vectorizer.get_feature_names_out()
                        keywords = feature_names[:5].tolist()
                    except:
                        keywords = []
                    
                    topic_label = f"Topic {i+1}"
                    if keywords:
                        topic_label = keywords[0].capitalize()
                    
                    topics.append({
                        'topic': topic_label,
                        'keywords': keywords,
                        'count': len(cluster_texts)
                    })
            
            return topics
        except Exception as e:
            print(f"Topic detection error: {e}")
            return [{'topic': 'General', 'keywords': [], 'count': len(texts)}]
    
    def get_topic_for_text(self, text: str, existing_topics: List[str]) -> str:
        if not existing_topics:
            return "General"
        
        try:
            text_lower = text.lower()
            for topic in existing_topics:
                if topic.lower() in text_lower:
                    return topic
            return existing_topics[0] 
        except:
            return "General"


# Singleton instance
_topic_detector = None

def get_topic_detector() -> TopicDetector:
    global _topic_detector
    if _topic_detector is None:
        _topic_detector = TopicDetector()
    return _topic_detector