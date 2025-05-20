from crypto_calculator.auth import User


def test_password_hashing_and_verification():
    user = User.create("alice", "secret")
    assert user.verify_password("secret")
    assert not user.verify_password("wrong")
