from crypto_calculator.db import init_db, add_user, get_user_by_username


def test_add_and_get_user(tmp_path, monkeypatch):
    db_file = tmp_path / "users.db"
    monkeypatch.setattr("crypto_calculator.db.DB_PATH", db_file)
    init_db()
    user = add_user("bob", "password")
    fetched = get_user_by_username("bob")
    assert fetched is not None
    assert fetched.username == "bob"
    assert fetched.verify_password("password")
