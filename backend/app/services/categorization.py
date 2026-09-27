"""Privacy-minimised merchant categorization with deterministic rules first."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.services.deduplication import normalize_merchant

RULES = {
    "SWIGGY": "Food",
    "ZOMATO": "Food",
    "UBER": "Transport",
    "OLA": "Transport",
    "AMAZON": "Shopping",
    "NETFLIX": "Entertainment",
}


@dataclass(frozen=True)
class Categorization:
    category: str
    confidence: Decimal
    source: str


class AIProvider(Protocol):
    def categorize_merchant(self, merchant: str) -> Categorization | None: ...


class MerchantMappingStore(Protocol):
    def get(self, user_id: UUID, merchant: str) -> Categorization | None: ...
    def save(self, user_id: UUID, merchant: str, result: Categorization) -> None: ...


class MerchantCategorizationService:
    def __init__(
        self, store: MerchantMappingStore, provider: AIProvider | None = None
    ) -> None:
        self.store, self.provider = store, provider

    def categorize(self, user_id: UUID, merchant: str | None) -> Categorization:
        normalized = normalize_merchant(merchant)
        if not normalized:
            return Categorization("Uncategorized", Decimal("0"), "fallback")
        if normalized in RULES:
            return Categorization(RULES[normalized], Decimal("1"), "rule")
        cached = self.store.get(user_id, normalized)
        if cached:
            return cached
        if self.provider:
            result = self.provider.categorize_merchant(normalized)
            if result:
                self.store.save(user_id, normalized, result)
                return result
        return Categorization("Uncategorized", Decimal("0"), "fallback")

    def correct(self, user_id: UUID, merchant: str, category: str) -> Categorization:
        result = Categorization(category, Decimal("1"), "user")
        self.store.save(user_id, normalize_merchant(merchant), result)
        return result
