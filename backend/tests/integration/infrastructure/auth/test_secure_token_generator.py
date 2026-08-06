from src.modules.auth.infrastructure.secure_token_generator import SecureTokenGenerator


def test_generate_returns_distinct_tokens() -> None:
    generator = SecureTokenGenerator()

    assert generator.generate() != generator.generate()


def test_hash_is_deterministic_for_the_same_token() -> None:
    generator = SecureTokenGenerator()
    token = generator.generate()

    assert generator.hash(token) == generator.hash(token)


def test_hash_differs_for_different_tokens() -> None:
    generator = SecureTokenGenerator()

    assert generator.hash("token-a") != generator.hash("token-b")
