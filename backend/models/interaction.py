from sqlalchemy import JSON, Column, Date, DateTime, ForeignKey, Integer, String, Text, Time, func
from sqlalchemy.orm import relationship

from backend.database import Base


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, ForeignKey("hcps.id"), nullable=False, index=True)
    interaction_type = Column(String(80), nullable=False, default="meeting")
    date = Column(Date, nullable=True)
    time = Column(Time, nullable=True)
    attendees = Column(JSON, nullable=False, default=list)
    topics = Column(JSON, nullable=False, default=list)
    materials_shared = Column(JSON, nullable=False, default=list)
    samples_distributed = Column(JSON, nullable=False, default=list)
    sentiment = Column(String(40), nullable=True)
    outcome = Column(Text, nullable=True)
    follow_up_actions = Column(JSON, nullable=False, default=list)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    hcp = relationship("HCP", back_populates="interactions")
    followups = relationship("FollowUp", back_populates="interaction", cascade="all, delete-orphan")

