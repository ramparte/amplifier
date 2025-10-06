"""Outline parser for converting text to structured data."""

import re
from contextlib import suppress
from typing import Any

import yaml
from presenter.models import NodeType
from presenter.models import OutlineNode
from presenter.models import ParsedOutline


class OutlineParser:
    """Parser for converting text outlines to structured format."""

    def __init__(self):
        """Initialize the parser."""
        self.heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$")
        self.bullet_pattern = re.compile(r"^(\s*)[*\-+]\s+(.+)$")
        self.code_block_pattern = re.compile(r"^```(\w*)\s*$")
        self.frontmatter_pattern = re.compile(r"^---\s*$")
        self.alt_h1_pattern = re.compile(r"^=+\s*$")
        self.alt_h2_pattern = re.compile(r"^-+\s*$")

    def parse(self, input_text: str) -> ParsedOutline:
        """Parse text input into structured outline.

        Args:
            input_text: Raw text input (Markdown, plain text, etc.)

        Returns:
            ParsedOutline object with hierarchical structure

        Raises:
            ValueError: If input is empty
        """
        if not input_text or not input_text.strip():
            raise ValueError("Empty input")

        lines = input_text.strip().split("\n")
        metadata: dict[str, Any] = {}
        start_idx = 0

        # Check for frontmatter
        if lines[0].strip() == "---":
            frontmatter_end = self._find_frontmatter_end(lines[1:])
            if frontmatter_end > 0:
                frontmatter_text = "\n".join(lines[1 : frontmatter_end + 1])
                with suppress(yaml.YAMLError):
                    parsed = yaml.safe_load(frontmatter_text) or {}
                    # Convert dates back to strings to maintain consistency
                    metadata = {}
                    for key, value in parsed.items():
                        if hasattr(value, "isoformat"):
                            metadata[key] = value.isoformat()
                        else:
                            metadata[key] = value
                start_idx = frontmatter_end + 2

        # Parse the main content
        title, nodes = self._parse_content(lines[start_idx:])

        return ParsedOutline(title=title, nodes=nodes, metadata=metadata)

    def validate(self, outline: ParsedOutline) -> bool:
        """Validate an outline structure.

        Args:
            outline: ParsedOutline to validate

        Returns:
            True if valid, False otherwise
        """
        if not outline.nodes:
            return False

        # Check that all nodes have required fields
        def validate_node(node: OutlineNode) -> bool:
            if not node.text:
                return False
            return all(validate_node(child) for child in node.children)

        return all(validate_node(node) for node in outline.nodes)

    def _find_frontmatter_end(self, lines: list[str]) -> int:
        """Find the end of frontmatter section."""
        for i, line in enumerate(lines):
            if line.strip() == "---":
                return i
        return -1

    def _parse_content(self, lines: list[str]) -> tuple[str | None, list[OutlineNode]]:
        """Parse the main content lines."""
        title = None
        nodes: list[OutlineNode] = []
        current_stack: list[OutlineNode] = []
        in_code_block = False
        code_language = None
        code_lines: list[str] = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Handle code blocks
            if self.code_block_pattern.match(line):
                if not in_code_block:
                    match = self.code_block_pattern.match(line)
                    code_language = match.group(1) if match else None
                    in_code_block = True
                    code_lines = []
                else:
                    # End of code block
                    code_node = OutlineNode(
                        level=len(current_stack),
                        text="\n".join(code_lines),
                        node_type=NodeType.CODE,
                        metadata={"language": code_language} if code_language else {},
                    )
                    self._add_node_to_structure(code_node, current_stack, nodes)
                    in_code_block = False
                    code_lines = []
                i += 1
                continue

            if in_code_block:
                code_lines.append(line)
                i += 1
                continue

            # Check for alternative header syntax (underline style)
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if self.alt_h1_pattern.match(next_line):
                    if title is None:
                        title = line.strip()
                    else:
                        node = OutlineNode(level=0, text=line.strip(), node_type=NodeType.HEADING)
                        nodes.append(node)
                        current_stack = [node]
                    i += 2
                    continue
                if self.alt_h2_pattern.match(next_line):
                    node = OutlineNode(level=1, text=line.strip(), node_type=NodeType.HEADING)
                    self._add_node_to_structure(node, current_stack, nodes)
                    i += 2
                    continue

            # Check for markdown headers
            heading_match = self.heading_pattern.match(line)
            if heading_match:
                level = len(heading_match.group(1)) - 1  # 0-indexed
                text = heading_match.group(2).strip()

                if level == 0 and title is None:
                    title = text
                else:
                    node = OutlineNode(level=level if title else level - 1, text=text, node_type=NodeType.HEADING)
                    self._add_heading_to_structure(node, current_stack, nodes)

                i += 1
                continue

            # Check for bullets
            bullet_match = self.bullet_pattern.match(line)
            if bullet_match:
                indent = len(bullet_match.group(1))
                text = bullet_match.group(2).strip()
                level = indent // 2  # Assume 2 spaces per level

                # Check for sub-bullets on the same line
                sub_bullets = []
                if i + 1 < len(lines):
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j]
                        next_bullet = self.bullet_pattern.match(next_line)
                        if next_bullet:
                            next_indent = len(next_bullet.group(1))
                            if next_indent > indent:
                                sub_text = next_bullet.group(2).strip()
                                sub_bullets.append(
                                    OutlineNode(level=level + 1, text=sub_text, node_type=NodeType.BULLET)
                                )
                                j += 1
                            else:
                                break
                        else:
                            break

                node = OutlineNode(level=level, text=text, node_type=NodeType.BULLET, children=sub_bullets)

                # Adjust position based on sub-bullets processed
                if sub_bullets:
                    i = j - 1

                self._add_node_to_structure(node, current_stack, nodes)
                i += 1
                continue

            # Plain text line - collect consecutive lines
            if line.strip():
                text_lines = [line.strip()]
                j = i + 1

                # Collect consecutive plain text lines
                while j < len(lines):
                    next_line = lines[j]
                    # Stop if we hit a structured element
                    if (
                        self.heading_pattern.match(next_line)
                        or self.bullet_pattern.match(next_line)
                        or self.code_block_pattern.match(next_line)
                        or not next_line.strip()
                    ):
                        break
                    # Check for alt headers
                    if j + 1 < len(lines):
                        after_next = lines[j + 1]
                        if self.alt_h1_pattern.match(after_next) or self.alt_h2_pattern.match(after_next):
                            break
                    text_lines.append(next_line.strip())
                    j += 1

                # Create single node with all collected lines
                node = OutlineNode(level=len(current_stack), text="\n".join(text_lines), node_type=NodeType.TEXT)
                self._add_node_to_structure(node, current_stack, nodes)
                i = j
                continue

            i += 1

        return title, nodes

    def _add_heading_to_structure(
        self, node: OutlineNode, current_stack: list[OutlineNode], root_nodes: list[OutlineNode]
    ):
        """Add a heading node to the structure, maintaining hierarchy."""
        # If this is a top-level heading (level 0)
        if node.level == 0:
            root_nodes.append(node)
            current_stack.clear()
            current_stack.append(node)
            return

        # Pop stack until we find the right parent level
        # Headers at same level should be siblings, not parent-child
        while current_stack and current_stack[-1].level >= node.level:
            current_stack.pop()

        # If we have a parent in the stack, add as its child
        if current_stack:
            current_stack[-1].children.append(node)
        else:
            # No parent found, add to root
            root_nodes.append(node)

        # Add this node to the stack for future children
        current_stack.append(node)

    def _add_node_to_structure(
        self, node: OutlineNode, current_stack: list[OutlineNode], root_nodes: list[OutlineNode]
    ):
        """Add a non-heading node to the structure."""
        if current_stack:
            # Add to the most recent container
            current_stack[-1].children.append(node)
        else:
            root_nodes.append(node)
