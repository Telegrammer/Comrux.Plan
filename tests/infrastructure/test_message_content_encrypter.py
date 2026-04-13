from infrastructure.adapters.message_content_encrypter import (
    FernetMessageContentEncrypter,
)
from domain.value_objects import MessageEncryptionKey


def test_fernet_message_content_encrypter_encrypts_plain_text() -> None:
    encrypter = FernetMessageContentEncrypter(
        MessageEncryptionKey("U6WgwxM_H0F1fvJzDYa0_Ac40mSZ8FGcqqb86QjYgHg=")
    )

    encrypted_content = encrypter("Chat created")

    assert encrypted_content != b"Chat created"
    assert encrypted_content.startswith(b"gAAAA")
