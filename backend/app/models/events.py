from sqlalchemy import Column, Integer, String, DateTime,ForeignKey, func
from sqlalchemy.orm import relationship
from app.models.base import Base # Import Base from the database module

class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), index=True)
    description = Column(String(500), nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    owner = relationship("User", back_populates="events")
    
    def __repr__(self):
        return f"<Event(id={self.id}, title={self.title}, start_time={self.start_time}, end_time={self.end_time})>"

    