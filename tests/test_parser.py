"""Tests for the outline parser module."""

import pytest

from presenter.models import NodeType, OutlineNode, ParsedOutline


class TestParser:
    """Test the outline parser."""

    def test_parse_simple_markdown(self, sample_markdown_simple):
        """Test parsing a simple markdown outline."""
        from presenter.parser import OutlineParser

        parser = OutlineParser()
        result = parser.parse(sample_markdown_simple)

        assert isinstance(result, ParsedOutline)
        assert result.title == "Q4 2024 Product Update"
        assert len(result.nodes) == 2
        assert result.nodes[0].text == "Overview"
        assert result.nodes[0].node_type == NodeType.HEADING
        assert len(result.nodes[0].children) == 3

    def test_parse_nested_structure(self, sample_markdown_nested):
        """Test parsing nested markdown structure."""
        from presenter.parser import OutlineParser

        parser = OutlineParser()
        result = parser.parse(sample_markdown_nested)

        assert result.title == "Product Roadmap"
        assert len(result.nodes) == 1  # Q1 Goals
        assert result.nodes[0].text == "Q1 Goals"

        # Check nested structure
        q1_goals = result.nodes[0]
        assert len(q1_goals.children) == 2  # Feature Development, Infrastructure

        feature_dev = q1_goals.children[0]
        assert feature_dev.text == "Feature Development"
        assert len(feature_dev.children) == 2  # User auth, Analytics

        # Check deeper nesting
        user_auth = feature_dev.children[0]
        assert user_auth.text == "User authentication"
        assert len(user_auth.children) == 2  # OAuth, Two-factor

    def test_parse_code_blocks(self, sample_markdown_with_code):
        """Test parsing markdown with code blocks."""
        from presenter.parser import OutlineParser

        parser = OutlineParser()
        result = parser.parse(sample_markdown_with_code)

        assert result.title == "Technical Documentation"

        # Find the API Example section
        api_section = result.nodes[0]
        assert api_section.text == "API Example"

        # Check that code block is captured
        code_found = False
        for child in api_section.children:
            if child.node_type == NodeType.CODE:
                code_found = True
                assert "import requests" in child.text
                assert child.metadata.get("language") == "python"
                break
        assert code_found, "Code block should be parsed"

    def test_parse_frontmatter(self, sample_markdown_with_frontmatter):
        """Test parsing markdown with YAML front matter."""
        from presenter.parser import OutlineParser

        parser = OutlineParser()
        result = parser.parse(sample_markdown_with_frontmatter)

        # Check metadata from frontmatter
        assert result.metadata.get("title") == "Quarterly Review"
        assert result.metadata.get("author") == "Jane Smith"
        assert result.metadata.get("date") == "2024-01-15"
        assert "review" in result.metadata.get("tags", [])

        # Check that the main title is still parsed
        assert result.title == "Q4 2024 Results"

    def test_parse_empty_input(self):
        """Test parsing empty input."""
        from presenter.parser import OutlineParser

        parser = OutlineParser()

        with pytest.raises(ValueError, match="Empty input"):
            parser.parse("")

    def test_parse_plain_text(self):
        """Test parsing plain text without structure."""
        from presenter.parser import OutlineParser

        parser = OutlineParser()
        result = parser.parse("This is just plain text\nwith multiple lines")

        assert isinstance(result, ParsedOutline)
        assert result.title is None
        assert len(result.nodes) == 1
        assert result.nodes[0].node_type == NodeType.TEXT

    def test_extract_hierarchy(self):
        """Test hierarchy extraction from headers."""
        from presenter.parser import OutlineParser

        markdown = """# Main Title
## Section 1
### Subsection 1.1
Content here
### Subsection 1.2
## Section 2
Content for section 2"""

        parser = OutlineParser()
        result = parser.parse(markdown)

        assert result.title == "Main Title"
        assert len(result.nodes) == 2  # Section 1 and Section 2
        assert result.nodes[0].level == 1
        assert result.nodes[0].children[0].level == 2

    def test_parse_bullets_only(self):
        """Test parsing content with only bullet points."""
        from presenter.parser import OutlineParser

        markdown = """- Item 1
- Item 2
  - Nested item 2.1
  - Nested item 2.2
- Item 3"""

        parser = OutlineParser()
        result = parser.parse(markdown)

        assert len(result.nodes) == 3  # Three top-level items
        assert result.nodes[1].children[0].text == "Nested item 2.1"

    def test_validate_outline(self):
        """Test outline validation."""
        from presenter.parser import OutlineParser

        parser = OutlineParser()

        # Valid outline
        valid = ParsedOutline(
            title="Test",
            nodes=[OutlineNode(level=1, text="Section", node_type=NodeType.HEADING)]
        )
        assert parser.validate(valid) is True

        # Invalid outline (empty nodes)
        invalid = ParsedOutline(title="Test", nodes=[])
        assert parser.validate(invalid) is False

    @pytest.mark.parametrize("input_text,expected_title", [
        ("# Title\nContent", "Title"),
        ("## No H1 Title\nContent", None),
        ("Title without hash\n===\nContent", "Title without hash"),
    ])
    def test_title_extraction(self, input_text, expected_title):
        """Test various title extraction scenarios."""
        from presenter.parser import OutlineParser

        parser = OutlineParser()
        result = parser.parse(input_text)
        assert result.title == expected_title