from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ARRAY, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text)
    summary = Column(Text)
    url = Column(String(512), unique=True, nullable=False)
    source = Column(String(100))
    author = Column(String(100))
    published_at = Column(DateTime(timezone=True))
    crawled_at = Column(DateTime(timezone=True), server_default=func.now())
    category = Column(String(50))
    keywords = Column(ARRAY(String))
    is_ai_content = Column(Boolean, default=False)
    sentiment = Column(Float)

    __table_args__ = (
        Index('idx_news_published_at', 'published_at'),
        Index('idx_news_source', 'source'),
        Index('idx_news_category', 'category'),
        Index('idx_news_keywords', 'keywords', postgresql_using='gin'),
    )