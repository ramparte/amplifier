"""Pytest configuration and shared fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def sample_markdown_simple():
    """Simple markdown outline."""
    return """# Q4 2024 Product Update

## Overview
- Record quarter for user growth
- Three major features launched
- Improved system performance by 40%

## Key Metrics
- Users: 1.2M (+25% QoQ)
- Revenue: $4.5M (+30% QoQ)
- NPS: 72 (+5 points)
"""


@pytest.fixture
def sample_markdown_nested():
    """Markdown with nested structure."""
    return """# Product Roadmap

## Q1 Goals
### Feature Development
- User authentication
  - OAuth integration
  - Two-factor auth
- Analytics dashboard
  - Real-time metrics
  - Custom reports

### Infrastructure
- Database optimization
- API performance improvements
"""


@pytest.fixture
def sample_markdown_with_code():
    """Markdown with code blocks."""
    return """# Technical Documentation

## API Example

Here's how to use our API:

```python
import requests
response = requests.get('https://api.example.com/data')
print(response.json())
```

## Configuration

```yaml
server:
  host: localhost
  port: 8080
```
"""


@pytest.fixture
def sample_markdown_with_frontmatter():
    """Markdown with YAML front matter."""
    return """---
title: Quarterly Review
author: Jane Smith
date: 2024-01-15
tags: [review, quarterly, business]
---

# Q4 2024 Results

## Summary
- Strong performance
- Exceeded targets
"""


@pytest.fixture
def fixtures_dir():
    """Path to fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_outlines_dir(fixtures_dir):
    """Path to sample outlines directory."""
    path = fixtures_dir / "sample_outlines"
    path.mkdir(parents=True, exist_ok=True)
    return path
