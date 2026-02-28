"""Database models."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    authors = Column(Text)  # JSON string list
    abstract = Column(Text)
    arxiv_id = Column(String(50), unique=True, nullable=True)
    pdf_path = Column(String(500), unique=True)
    summary = Column(Text, nullable=True)
    github_repo = Column(String(500), nullable=True)
    year = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    favorites = relationship("Favorite", back_populates="paper")


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    paper = relationship("Paper", back_populates="favorites")
