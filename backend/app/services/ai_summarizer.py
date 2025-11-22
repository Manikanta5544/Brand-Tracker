from openai import AsyncOpenAI
from typing import List, Dict
from ..core.config import settings


class AISummarizer:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
    
    async def generate_daily_summary(self, mentions: List[Dict]) -> str:
        if not self.client or not mentions:
            return "No summary available. Please configure OpenAI API key."
        
        try:
            # Prepare context
            mention_texts = [m['text'][:200] for m in mentions[:50]]  # Limit to 50 mentions
            context = "\n".join([f"- {text}" for text in mention_texts])
            
            prompt = f"""Analyze these brand mentions and provide a concise summary:

{context}

Provide:
1. Overall sentiment trend
2. Key themes and topics
3. Notable positive highlights
4. Areas of concern
5. Actionable insights

Keep it under 200 words."""

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a brand reputation analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"AI summarization error: {e}")
            return f"Summary generation failed: {str(e)}"
    
    async def explain_spike(self, recent_mentions: List[Dict], spike_data: Dict) -> str:
        if not self.client or not recent_mentions:
            return "Spike detected but explanation unavailable."
        
        try:
            mention_texts = [m['text'][:200] for m in recent_mentions[:30]]
            context = "\n".join([f"- {text}" for text in mention_texts])
            
            prompt = f"""There's been a spike in brand mentions. Current count: {spike_data.get('current_count')}, Normal average: {spike_data.get('mean', 0):.1f}.

Recent mentions:
{context}

Explain in 2-3 sentences what's causing this spike."""

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a brand reputation analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Spike explanation error: {e}")
            return "Unable to explain spike at this time."
    
    async def summarize_topic(self, topic: str, mentions: List[Dict]) -> str:
        """
        Generate a summary for a specific topic
        """
        if not self.client or not mentions:
            return f"No summary available for topic: {topic}"
        
        try:
            mention_texts = [m['text'][:200] for m in mentions[:30]]
            context = "\n".join([f"- {text}" for text in mention_texts])
            
            prompt = f"""Summarize the key points about "{topic}" from these mentions:

{context}

Provide a brief summary (3-4 sentences) highlighting the main sentiment and key points."""

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a brand reputation analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Topic summarization error: {e}")
            return f"Unable to summarize topic: {topic}"


# Singleton instance
_ai_summarizer = None

def get_ai_summarizer() -> AISummarizer:
    global _ai_summarizer
    if _ai_summarizer is None:
        _ai_summarizer = AISummarizer()
    return _ai_summarizer