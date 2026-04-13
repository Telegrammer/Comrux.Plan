from dataclasses import dataclass
from ..exceptions import DomainFieldError


@dataclass(frozen=True, init=False)
class Name:
    __max_name_length: int = 100
    value: str

    def __init__(self, raw_name: str):
        cleaned_value = self._clean_value(raw_name)

        if len(cleaned_value) > self.__max_name_length:
            raise DomainFieldError(
                f"Name is too long. Maximum {self.__max_name_length} characters allowed"
            )

        if not cleaned_value or cleaned_value.strip() == "":
            raise DomainFieldError("Name cannot be empty")

        if not self._is_valid_name(cleaned_value):
            raise DomainFieldError(
                "Name contains invalid characters. Only letters, spaces, dots and hyphens are allowed"
            )

        object.__setattr__(self, "value", cleaned_value)

    def _clean_value(self, value: str) -> str:
        if not isinstance(value, str):
            raise DomainFieldError("Name must be a string")

        cleaned = value.strip()

        while "  " in cleaned:
            cleaned = cleaned.replace("  ", " ")

        return cleaned

    def _is_valid_name(self, value: str) -> bool:
        if not value:
            return False

        for character in value:
            if not (character.isalpha() or character in {".", "-", " ", "_"}):
                return False
        return True
