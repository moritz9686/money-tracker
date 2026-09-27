from decimal import Decimal
from uuid import uuid4

from app.services.categorization import Categorization, MerchantCategorizationService


class Store:
    values = {}

    def get(self, user_id, merchant):
        return self.values.get((user_id, merchant))

    def save(self, user_id, merchant, result):
        self.values[(user_id, merchant)] = result


class AI:
    calls = 0

    def categorize_merchant(self, merchant):
        self.calls += 1
        assert merchant == "LOCAL CAFE"
        return Categorization("Food", Decimal("0.8"), "ai")


def test_rule_never_calls_ai() -> None:
    ai = AI()
    result = MerchantCategorizationService(Store(), ai).categorize(uuid4(), "Swiggy")
    assert result.category == "Food" and ai.calls == 0


def test_ai_is_cached_and_user_correction_wins() -> None:
    store, ai, user = Store(), AI(), uuid4()
    service = MerchantCategorizationService(store, ai)
    assert service.categorize(user, "Local Cafe").source == "ai"
    assert service.categorize(user, "Local Cafe").source == "ai" and ai.calls == 1
    assert service.correct(user, "Local Cafe", "Dining").category == "Dining"
