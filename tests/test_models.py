import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Email
from datetime import datetime

@pytest.fixture(scope='function')
def db_session():
    # Use SQLite in-memory database for testing
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_email_model(db_session):
    # Test email creation and retrieval
    email = Email(
        message_id='test123',
        from_address='sender@test.com',
        to_address='receiver@test.com',
        subject='Test Email',
        received_date=datetime.now(),
        message_body='Test content',
        labels='Important'
    )
    
    db_session.add(email)
    db_session.commit()
    
    # Test retrieval
    retrieved = db_session.query(Email).filter_by(message_id='test123').first()
    assert retrieved.from_address == 'sender@test.com'
    assert retrieved.subject == 'Test Email'

def test_email_unique_constraint(db_session):
    # Test that duplicate message_ids are not allowed
    email1 = Email(message_id='test123', from_address='test1@test.com')
    email2 = Email(message_id='test123', from_address='test2@test.com')
    
    db_session.add(email1)
    db_session.commit()
    
    with pytest.raises(Exception):
        db_session.add(email2)
        db_session.commit()