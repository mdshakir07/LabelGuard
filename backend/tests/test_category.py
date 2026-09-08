"""Unit tests for the category-suggestion service (PRD §18, §40 P0)."""
from app.services.category import suggest_categories


class TestSuggestCategories:
    def test_empty_when_no_signal(self):
        assert suggest_categories() == []

    def test_product_hint_drives_food(self):
        out = suggest_categories(product_name_hint="Parle-G Biscuits")
        assert out[0]["category"] == "food"
        assert out[0]["confidence"] >= 0.5

    def test_extracted_product_takes_precedence(self):
        a = suggest_categories(product_name_hint="Generic pack",
                               extracted_product="Dove Conditioner 200 ml")
        assert a[0]["category"] == "cosmetics"

    def test_special_status_maps(self):
        out = suggest_categories(special_status="GM food")
        assert out[0]["category"] == "food"
        assert out[0]["basis"].startswith("special status")

    def test_beverage_keywords(self):
        out = suggest_categories(extracted_product="Thums Up Soft Drink 750 ml")
        assert out[0]["category"] == "beverages"

    def test_garment_keywords(self):
        out = suggest_categories(product_name_hint="Cotton Kurta for men")
        assert out[0]["category"] == "garments"

    def test_current_category_preserved_when_unscored(self):
        out = suggest_categories(category="household", product_name_hint="Biscuits")
        cats = [r["category"] for r in out]
        assert "food" in cats
        assert "household" in cats  # kept at low rank

    def test_sorted_desc(self):
        out = suggest_categories(product_name_hint="Biscuit spray deodorant")
        confs = [r["confidence"] for r in out]
        assert confs == sorted(confs, reverse=True)

    def test_max_five(self):
        out = suggest_categories(product_name_hint="biscuit pasta rice soap shampoo kurta")
        assert len(out) <= 5