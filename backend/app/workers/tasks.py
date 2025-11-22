from celery import group, Task
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SyncSessionLocal
from app.models.mention import Mention
from app.models.alert import Alert
from app.models.topic import Topic
from app.services.sentiment_analyzer import get_sentiment_analyzer
from app.services.classifier import get_classifier
from app.services.toxicity_detector import get_toxicity_detector
from app.services.topic_detector import get_topic_detector
from app.workers.scrapers.reddit_scraper import scrape_reddit
from app.workers.scrapers.twitter_scraper import scrape_twitter
from app.workers.scrapers.news_scraper import scrape_news
import logging
from typing import Any

celery_app = __import__('app.workers.celery_app', fromlist=['celery_app']).celery_app
logger = logging.getLogger(__name__)


class CallbackTask(Task):
    def on_failure(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        """Handle task failures."""
        logger.error(f"Task {task_id} failed with error: {exc}", exc_info=True)

    def on_success(self, result: Any, task_id: str, args: tuple, kwargs: dict) -> None:
        """Handle task success."""
        logger.info(f"Task {task_id} completed successfully")


@celery_app.task(name='app.workers.tasks.collect_all_mentions', bind=True, base=CallbackTask)
def collect_all_mentions(self: Task) -> dict[str, Any]:
    try:
        logger.info("Starting mention collection from all sources")
        tasks = group(
            collect_reddit_mentions.s(),
            collect_twitter_mentions.s(),
            collect_news_mentions.s(),
        )
        result = tasks.apply_async()
        logger.info(f"Dispatched mention collection tasks: {result.id}")
        return {"status": "Collection tasks dispatched", "task_id": result.id}
    except Exception as e:
        logger.error(f"Error in collect_all_mentions: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@celery_app.task(name='app.workers.tasks.collect_reddit_mentions', bind=True, base=CallbackTask)
def collect_reddit_mentions(self: Task) -> dict[str, Any]:
    try:
        logger.info("Starting Reddit mention collection")
        mentions = scrape_reddit(brand_keywords=["your_brand", "YourBrand"])

        if mentions:
            db = SyncSessionLocal()
            try:
                count = 0
                for mention_data in mentions:
                    try:
                        processed = process_mention_with_ai(mention_data)
                        mention = Mention(**processed)
                        db.add(mention)
                        count += 1
                    except Exception as e:
                        logger.error(f"Error processing Reddit mention: {e}", exc_info=True)
                        continue

                db.commit()
                logger.info(f"Successfully saved {count} Reddit mentions")
                return {"status": "success", "count": count, "source": "reddit"}
            except Exception as e:
                db.rollback()
                logger.error(f"Error saving Reddit mentions: {e}", exc_info=True)
                return {"status": "error", "message": str(e), "source": "reddit"}
            finally:
                db.close()

        logger.info("No new Reddit mentions found")
        return {"status": "success", "count": 0, "source": "reddit"}
    except Exception as e:
        logger.error(f"Reddit mention collection error: {e}", exc_info=True)
        return {"status": "error", "message": str(e), "source": "reddit"}


@celery_app.task(name='app.workers.tasks.collect_twitter_mentions', bind=True, base=CallbackTask)
def collect_twitter_mentions(self: Task) -> dict[str, Any]:
    try:
        logger.info("Starting Twitter mention collection")
        mentions = scrape_twitter(brand_keywords=["your_brand", "YourBrand"])

        if mentions:
            db = SyncSessionLocal()
            try:
                count = 0
                for mention_data in mentions:
                    try:
                        processed = process_mention_with_ai(mention_data)
                        mention = Mention(**processed)
                        db.add(mention)
                        count += 1
                    except Exception as e:
                        logger.error(f"Error processing Twitter mention: {e}", exc_info=True)
                        continue

                db.commit()
                logger.info(f"Successfully saved {count} Twitter mentions")
                return {"status": "success", "count": count, "source": "twitter"}
            except Exception as e:
                db.rollback()
                logger.error(f"Error saving Twitter mentions: {e}", exc_info=True)
                return {"status": "error", "message": str(e), "source": "twitter"}
            finally:
                db.close()

        logger.info("No new Twitter mentions found")
        return {"status": "success", "count": 0, "source": "twitter"}
    except Exception as e:
        logger.error(f"Twitter mention collection error: {e}", exc_info=True)
        return {"status": "error", "message": str(e), "source": "twitter"}


@celery_app.task(name='app.workers.tasks.collect_news_mentions', bind=True, base=CallbackTask)
def collect_news_mentions(self: Task) -> dict[str, Any]:
   
    try:
        logger.info("Starting news mention collection")
        mentions = scrape_news(brand_keywords=["your_brand", "YourBrand"])

        if mentions:
            db = SyncSessionLocal()
            try:
                count = 0
                for mention_data in mentions:
                    try:
                        processed = process_mention_with_ai(mention_data)
                        mention = Mention(**processed)
                        db.add(mention)
                        count += 1
                    except Exception as e:
                        logger.error(f"Error processing news mention: {e}", exc_info=True)
                        continue

                db.commit()
                logger.info(f"Successfully saved {count} news mentions")
                return {"status": "success", "count": count, "source": "news"}
            except Exception as e:
                db.rollback()
                logger.error(f"Error saving news mentions: {e}", exc_info=True)
                return {"status": "error", "message": str(e), "source": "news"}
            finally:
                db.close()

        logger.info("No new news mentions found")
        return {"status": "success", "count": 0, "source": "news"}
    except Exception as e:
        logger.error(f"News mention collection error: {e}", exc_info=True)
        return {"status": "error", "message": str(e), "source": "news"}


def process_mention_with_ai(mention_data: dict[str, Any]) -> dict[str, Any]:
    try:
        text = mention_data.get('text', '')

        sentiment_analyzer = get_sentiment_analyzer()
        sentiment_result = sentiment_analyzer.analyze(text)

        classifier = get_classifier()
        category_result = classifier.classify(text)

        toxicity_detector = get_toxicity_detector()
        toxicity_result = toxicity_detector.detect(text)

        topic_detector = get_topic_detector()
        topic = topic_detector.get_topic_for_text(text, ["Product", "Service", "Support", "Pricing"])

        is_toxic = toxicity_result.get('toxicity', 0.0) > 0.5
        needs_attention = is_toxic or sentiment_result['sentiment'] == 'negative'

        return {
            **mention_data,
            'content': text,
            'sentiment': sentiment_result['sentiment'],
            'sentiment_score': sentiment_result['score'],
            'category': category_result['category'],
            'toxicity': toxicity_result['toxicity'],
            'is_toxic': is_toxic,
            'topic': topic,
            'needs_attention': needs_attention,
            'is_processed': True,
            'created_at': datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error processing mention with AI: {e}", exc_info=True)
        return {
            **mention_data,
            'content': mention_data.get('text', ''),
            'sentiment': 'neutral',
            'sentiment_score': 0.0,
            'category': 'General',
            'toxicity': 0.0,
            'is_toxic': False,
            'topic': 'General',
            'needs_attention': False,
            'is_processed': False,
            'created_at': datetime.utcnow()
        }


@celery_app.task(name='app.workers.tasks.check_for_spikes', bind=True, base=CallbackTask)
def check_for_spikes(self: Task) -> dict[str, Any]:
    try:
        logger.info("Starting spike detection")
        db = SyncSessionLocal()
        try:
            from app.services.spike_detector import get_spike_detector
            from sqlalchemy import select
            from datetime import timedelta

            spike_detector = get_spike_detector()

            now = datetime.utcnow()
            current_hour = now.replace(minute=0, second=0, microsecond=0)
            previous_hour = current_hour - timedelta(hours=1)

            current_count = db.query(Mention).filter(
                Mention.timestamp >= current_hour
            ).count()

            previous_count = db.query(Mention).filter(
                Mention.timestamp.between(previous_hour, current_hour)
            ).count() or 1

            if current_count > previous_count * 3:
                alert = Alert(
                    alert_type='spike',
                    severity='high',
                    title='Mention Spike Detected',
                    message=f'Detected spike: {current_count} mentions in last hour (normal: ~{previous_count})',
                    source='spike_detector',
                    is_active=True
                )
                db.add(alert)
                db.commit()
                logger.info("Created spike alert")
                return {"status": "success", "spike_detected": True}

            logger.info("No significant spikes detected")
            return {"status": "success", "spike_detected": False}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Spike detection error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@celery_app.task(name='app.workers.tasks.update_topics', bind=True, base=CallbackTask)
def update_topics(self: Task) -> dict[str, Any]:
    try:
        logger.info("Starting topic update")
        db = SyncSessionLocal()
        try:
            mentions = db.query(Mention).order_by(Mention.timestamp.desc()).limit(1000).all()

            if len(mentions) > 10:
                texts = [m.content or "" for m in mentions]

                topic_detector = get_topic_detector()
                detected_topics = topic_detector.detect_topics(texts)

                for topic_data in detected_topics:
                    try:
                        topic = db.query(Topic).filter(Topic.label == topic_data['topic']).first()

                        if not topic:
                            topic = Topic(
                                label=topic_data['topic'],
                                keywords=topic_data.get('keywords', []),
                                mention_count=topic_data.get('count', 0),
                                is_active=True
                            )
                            db.add(topic)
                        else:
                            topic.keywords = topic_data.get('keywords', [])
                            topic.mention_count = topic_data.get('count', 0)
                    except Exception as e:
                        logger.error(f"Error updating topic {topic_data.get('topic')}: {e}", exc_info=True)
                        continue

                db.commit()
                logger.info(f"Updated {len(detected_topics)} topics")
                return {"status": "success", "topics_updated": len(detected_topics)}

            logger.info("Not enough mentions to update topics")
            return {"status": "success", "topics_updated": 0}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Topic update error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
