from sqlalchemy import Column, Integer, String, DateTime, func, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from app.models.base import Base # Import Base from the database module

user_shares = Table(
    'user_shares', Base.metadata,
    Column('sharer_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('shared_with_id', Integer, ForeignKey('users.id'), primary_key=True), extend_existing=True 
)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)  # Increased length and made non-nullable
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    events = relationship("Event", back_populates="owner", cascade="all, delete-orphan")
    
    # For calendar sharing
    shared_with = relationship(
        "User",
        secondary=user_shares,
        primaryjoin=id == user_shares.c.sharer_id,
        secondaryjoin=id == user_shares.c.shared_with_id,
        back_populates="shared_by"
    )
    
    shared_by = relationship(
        "User",
        secondary=user_shares,
        primaryjoin=id == user_shares.c.shared_with_id,
        secondaryjoin=id == user_shares.c.sharer_id,
        back_populates="shared_with"
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
