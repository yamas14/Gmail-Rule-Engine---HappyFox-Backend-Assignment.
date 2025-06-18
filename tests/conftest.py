import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

@pytest.fixture
def db_session():
    # Create an in-memory SQLite database for testing
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    
    # Create a new session factory bound to the engine
    Session = sessionmaker(bind=engine)
    
    # Create a new session for the test
    session = Session()
    
    yield session
    
    # Clean up after the test
    session.close()
    Base.metadata.drop_all(engine)