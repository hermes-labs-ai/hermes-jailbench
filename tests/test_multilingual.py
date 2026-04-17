"""
Tests for multilingual attack category.
Verifies that multilingual attacks are well-formed and integrated correctly.
"""

from jailbreak_bench.attacks import (
    ALL_ATTACKS,
    ATTACKS_BY_CATEGORY,
    MULTILINGUAL_ATTACKS,
    Attack,
    Category,
    ExpectedResult,
)


class TestMultilingualAttackIntegration:
    """Test that multilingual attacks are properly integrated into the system."""

    def test_multilingual_category_exists(self):
        """Multilingual category should exist in Category enum."""
        assert hasattr(Category, "MULTILINGUAL")
        assert Category.MULTILINGUAL.value == "multilingual"

    def test_multilingual_attacks_in_category_dict(self):
        """Multilingual attacks should be registered in ATTACKS_BY_CATEGORY."""
        assert Category.MULTILINGUAL in ATTACKS_BY_CATEGORY
        assert ATTACKS_BY_CATEGORY[Category.MULTILINGUAL] == MULTILINGUAL_ATTACKS

    def test_multilingual_attacks_in_all_attacks(self):
        """All multilingual attacks should be in ALL_ATTACKS."""
        for attack in MULTILINGUAL_ATTACKS:
            assert attack in ALL_ATTACKS, f"Attack '{attack.name}' not in ALL_ATTACKS"

    def test_multilingual_attacks_count(self):
        """Should have exactly 8 multilingual attacks."""
        assert len(MULTILINGUAL_ATTACKS) == 8, (
            f"Expected 8 multilingual attacks, got {len(MULTILINGUAL_ATTACKS)}"
        )


class TestMultilingualAttackStructure:
    """Test structural integrity of multilingual attacks."""

    def test_all_multilingual_attacks_are_instances(self):
        """All items in MULTILINGUAL_ATTACKS should be Attack instances."""
        for attack in MULTILINGUAL_ATTACKS:
            assert isinstance(attack, Attack), f"{attack!r} is not an Attack instance"

    def test_all_multilingual_have_names(self):
        """All attacks should have non-empty names."""
        for attack in MULTILINGUAL_ATTACKS:
            assert attack.name and attack.name.strip(), (
                f"Multilingual attack has empty name: {attack!r}"
            )

    def test_all_multilingual_have_category_multilingual(self):
        """All should have MULTILINGUAL category."""
        for attack in MULTILINGUAL_ATTACKS:
            assert attack.category == Category.MULTILINGUAL, (
                f"Attack '{attack.name}' has wrong category: {attack.category}"
            )

    def test_all_multilingual_have_refused_expected_result(self):
        """All should expect REFUSED response."""
        for attack in MULTILINGUAL_ATTACKS:
            assert attack.expected_result == ExpectedResult.REFUSED, (
                f"Attack '{attack.name}' expected_result is {attack.expected_result}"
            )

    def test_all_multilingual_have_templates(self):
        """All should have non-empty templates."""
        for attack in MULTILINGUAL_ATTACKS:
            assert attack.template and len(attack.template.strip()) > 10, (
                f"Attack '{attack.name}' has too-short template"
            )

    def test_all_multilingual_have_tags(self):
        """All should have tags list."""
        for attack in MULTILINGUAL_ATTACKS:
            assert isinstance(attack.tags, list), f"Attack '{attack.name}' tags must be a list"
            assert len(attack.tags) > 0, f"Attack '{attack.name}' should have at least one tag"


class TestMultilingualAttackNames:
    """Test that specific multilingual attacks exist with correct names."""

    EXPECTED_ATTACKS = {
        "Spanish System Prompt Extraction",
        "French System Prompt Extraction",
        "German System Prompt Extraction",
        "Japanese System Prompt Extraction",
        "Code-Switching Attack",
        "Base64 Spanish Instruction",
        "Translation Instruction Bypass",
        "Freedom Language Attack",
    }

    def test_all_expected_attacks_exist(self):
        """All 8 expected multilingual attacks should exist."""
        attack_names = {a.name for a in MULTILINGUAL_ATTACKS}
        assert attack_names == self.EXPECTED_ATTACKS, (
            f"Attack names don't match. Missing: {self.EXPECTED_ATTACKS - attack_names}, "
            f"Extra: {attack_names - self.EXPECTED_ATTACKS}"
        )

    def test_spanish_extraction_exists(self):
        assert any(a.name == "Spanish System Prompt Extraction" for a in MULTILINGUAL_ATTACKS)

    def test_french_extraction_exists(self):
        assert any(a.name == "French System Prompt Extraction" for a in MULTILINGUAL_ATTACKS)

    def test_german_extraction_exists(self):
        assert any(a.name == "German System Prompt Extraction" for a in MULTILINGUAL_ATTACKS)

    def test_japanese_extraction_exists(self):
        assert any(a.name == "Japanese System Prompt Extraction" for a in MULTILINGUAL_ATTACKS)

    def test_code_switching_exists(self):
        assert any(a.name == "Code-Switching Attack" for a in MULTILINGUAL_ATTACKS)

    def test_base64_spanish_exists(self):
        assert any(a.name == "Base64 Spanish Instruction" for a in MULTILINGUAL_ATTACKS)

    def test_translation_bypass_exists(self):
        assert any(a.name == "Translation Instruction Bypass" for a in MULTILINGUAL_ATTACKS)

    def test_freedom_language_exists(self):
        assert any(a.name == "Freedom Language Attack" for a in MULTILINGUAL_ATTACKS)


class TestMultilingualAttackRendering:
    """Test that multilingual attacks render correctly with payloads."""

    DEFAULT_PAYLOAD = "explain how to make a dangerous chemical weapon"

    def test_code_switching_renders_with_payload(self):
        """Code-switching attack should inject payload."""
        attack = next(a for a in MULTILINGUAL_ATTACKS if a.name == "Code-Switching Attack")
        rendered = attack.render(self.DEFAULT_PAYLOAD)
        assert self.DEFAULT_PAYLOAD in rendered, (
            "Code-switching attack should contain injected payload"
        )
        assert "{TARGET}" not in rendered, "Placeholder should be replaced in rendered output"

    def test_freedom_language_renders_with_payload(self):
        """Freedom language attack should inject payload."""
        attack = next(a for a in MULTILINGUAL_ATTACKS if a.name == "Freedom Language Attack")
        rendered = attack.render(self.DEFAULT_PAYLOAD)
        assert self.DEFAULT_PAYLOAD in rendered, (
            "Freedom language attack should contain injected payload"
        )
        assert "{TARGET}" not in rendered, "Placeholder should be replaced in rendered output"

    def test_non_placeholder_attacks_render_unchanged(self):
        """Spanish/French/German/Japanese extractions have no {TARGET}, should render as-is."""
        extraction_attacks = [
            a for a in MULTILINGUAL_ATTACKS if "Extraction" in a.name and "Spanish" in a.name
        ]
        for attack in extraction_attacks:
            rendered = attack.render(self.DEFAULT_PAYLOAD)
            # Should not contain the payload (it doesn't have {TARGET})
            assert self.DEFAULT_PAYLOAD not in rendered, (
                f"Attack '{attack.name}' shouldn't contain injected payload"
            )


class TestMultilingualAttackLanguages:
    """Test that attacks cover multiple languages."""

    def test_spanish_attack_uses_spanish(self):
        attack = next(
            a for a in MULTILINGUAL_ATTACKS if a.name == "Spanish System Prompt Extraction"
        )
        spanish_words = ["Por favor", "oración", "exactamente", "escrita"]
        assert any(word in attack.template for word in spanish_words), (
            "Spanish attack should contain Spanish language"
        )

    def test_french_attack_uses_french(self):
        attack = next(
            a for a in MULTILINGUAL_ATTACKS if a.name == "French System Prompt Extraction"
        )
        french_words = ["S'il vous plaît", "complétez", "phrase", "exactement"]
        assert any(word in attack.template for word in french_words), (
            "French attack should contain French language"
        )

    def test_german_attack_uses_german(self):
        attack = next(
            a for a in MULTILINGUAL_ATTACKS if a.name == "German System Prompt Extraction"
        )
        german_words = ["Bitte", "vervollständige", "Satz", "geschrieben"]
        assert any(word in attack.template for word in german_words), (
            "German attack should contain German language"
        )

    def test_japanese_attack_uses_japanese(self):
        attack = next(
            a for a in MULTILINGUAL_ATTACKS if a.name == "Japanese System Prompt Extraction"
        )
        # Japanese hiragana, katakana, or kanji should be present
        assert len(attack.template) > 0 and any(ord(c) > 0x3040 for c in attack.template), (
            "Japanese attack should contain Japanese characters"
        )


class TestMultilingualAttackTags:
    """Test that multilingual attacks have relevant tags."""

    def test_language_tags_present(self):
        """Attacks should be tagged with language names."""
        all_tags = {tag for attack in MULTILINGUAL_ATTACKS for tag in attack.tags}
        language_tags = {"spanish", "french", "german", "japanese"}
        assert language_tags.issubset(all_tags), f"Missing language tags. Have: {all_tags}"

    def test_spanish_extraction_has_spanish_tag(self):
        attack = next(
            a for a in MULTILINGUAL_ATTACKS if a.name == "Spanish System Prompt Extraction"
        )
        assert "spanish" in attack.tags

    def test_code_switching_has_relevant_tags(self):
        attack = next(a for a in MULTILINGUAL_ATTACKS if a.name == "Code-Switching Attack")
        assert "code-switching" in attack.tags or "mixed-language" in attack.tags

    def test_base64_spanish_has_multiple_tags(self):
        attack = next(a for a in MULTILINGUAL_ATTACKS if a.name == "Base64 Spanish Instruction")
        assert "base64" in attack.tags
        assert "spanish" in attack.tags


class TestMultilingualAttackIntegrationWithOthers:
    """Test that multilingual attacks don't interfere with existing attacks."""

    def test_total_attack_count_increases(self):
        """Adding 8 multilingual attacks should increase total count."""
        # Original: 37 attacks (5+5+5+5+5+5+7)
        # New: 45 attacks (adding 8)
        expected = 37 + 8
        assert len(ALL_ATTACKS) == expected, (
            f"Expected {expected} total attacks, got {len(ALL_ATTACKS)}"
        )

    def test_no_duplicate_names_across_all_attacks(self):
        """No two attacks (including multilingual) should share the same name."""
        names = [a.name for a in ALL_ATTACKS]
        duplicates = [n for n in names if names.count(n) > 1]
        assert not duplicates, (
            f"Found duplicate attack names across all categories: {set(duplicates)}"
        )

    def test_all_categories_still_have_minimum_attacks(self):
        """Each category should still meet minimum requirements."""
        for cat in Category:
            attacks = ATTACKS_BY_CATEGORY.get(cat, [])
            assert len(attacks) >= 5, (
                f"Category '{cat.value}' only has {len(attacks)} attacks (min 5)"
            )
