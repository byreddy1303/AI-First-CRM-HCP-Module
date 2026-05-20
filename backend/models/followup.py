from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from backend.database import Base


class FollowUp(Base):
    __tablename__ = "followups"

    id = Column(Integer, primary_key=True, index=True)
    interaction_id = Column(Integer, ForeignKey("interactions.id"), nullable=False, index=True)
    scheduled_date = Column(Date, nullable=False)
    note = Column(Text, nullable=False)
    status = Column(String(40), nullable=False, default="scheduled")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    interaction = relationship("Interaction", back_populates="followups")

