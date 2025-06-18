from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Index
from sqlalchemy.orm import declarative_base  
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

Base = declarative_base() 

class Email(Base):
    # Composite index for efficient email searching
    __tablename__ = 'emails'
    
    id = Column(Integer, primary_key=True)
    message_id = Column(String, unique=True)
    from_address = Column(String)
    to_address = Column(String)
    subject = Column(String)
    received_date = Column(DateTime, index=True)
    message_body = Column(Text)
    labels = Column(String)
    
    __table_args__ = (
        Index('idx_email_search', 'from_address', 'subject', 'received_date'),
    )

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
