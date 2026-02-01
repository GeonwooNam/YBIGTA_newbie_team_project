import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.user.user_repository import UserRepository
from app.user.user_schema import User

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

CREATE_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    username TEXT NOT NULL
);
"""

@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    connection.execute(text(CREATE_TABLE_QUERY))
    connection.commit()

    yield session 

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def user_repo(db_session):
    return UserRepository(db_session)


def test_save_new_user(user_repo):
    new_user = User(email="test@example.com", password="secure123", username="testuser")

    saved_user = user_repo.save_user(new_user)
    
    assert saved_user is not None
    assert saved_user.email == "test@example.com"
    assert saved_user.password == "secure123"
    assert saved_user.username == "testuser"


def test_get_user_by_email(user_repo):
    user_repo.save_user(User(email="getuser@example.com", password="getpassword", username="getusername"))

    user = user_repo.get_user_by_email("getuser@example.com")
    
    assert user is not None
    assert user.email == "getuser@example.com"
    assert user.password == "getpassword"
    assert user.username == "getusername"


def test_update_existing_user(user_repo):
    user_repo.save_user(User(email="update@example.com", password="oldpass", username="olduser"))

    updated_user = User(email="update@example.com", password="newpass", username="newuser")
    user_repo.save_user(updated_user)

    user = user_repo.get_user_by_email("update@example.com")
    
    assert user is not None
    assert user.password == "newpass"
    assert user.username == "newuser"


def test_delete_user(user_repo):
    user_repo.save_user(User(email="delete@example.com", password="delpass", username="deluser"))

    user = user_repo.get_user_by_email("delete@example.com")
    assert user is not None 

    user_repo.delete_user(user)
    user_after_delete = user_repo.get_user_by_email("delete@example.com")

    assert user_after_delete is None 
