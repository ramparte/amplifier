# Test-Driven Development Plan

## Testing Strategy
- **Unit Tests**: Test each module in isolation with mocked dependencies
- **Integration Tests**: Test module interactions and data flow
- **End-to-End Tests**: Complete pipeline from outline to PowerPoint
- **Visual Regression Tests**: Ensure consistent visual output
- **Performance Tests**: Measure and optimize processing time

## Sample Test Data

### 1. Simple Outline Input
```markdown
# Q4 2024 Product Update

## Overview
- Record quarter for user growth
- Three major features launched
- Improved system performance by 40%

## Key Metrics
- Users: 1.2M (+25% QoQ)
- Revenue: $4.5M (+30% QoQ)
- NPS: 72 (+5 points)

## Product Launches
### Feature A: AI Assistant
- Natural language processing
- 24/7 availability
- 95% satisfaction rate

### Feature B: Analytics Dashboard
- Real-time metrics
- Custom reports
- Export capabilities

## Next Quarter
- Mobile app launch
- Enterprise features
- International expansion
```

### 2. Expected Parsed Outline (JSON)
```json
{
  "title": "Q4 2024 Product Update",
  "nodes": [
    {
      "level": 1,
      "text": "Overview",
      "type": "heading",
      "children": [
        {"level": 2, "text": "Record quarter for user growth", "type": "bullet"},
        {"level": 2, "text": "Three major features launched", "type": "bullet"},
        {"level": 2, "text": "Improved system performance by 40%", "type": "bullet"}
      ]
    },
    {
      "level": 1,
      "text": "Key Metrics",
      "type": "heading",
      "children": [
        {"level": 2, "text": "Users: 1.2M (+25% QoQ)", "type": "bullet"},
        {"level": 2, "text": "Revenue: $4.5M (+30% QoQ)", "type": "bullet"},
        {"level": 2, "text": "NPS: 72 (+5 points)", "type": "bullet"}
      ]
    }
  ]
}
```

### 3. Expected Enriched Outline (with LLM analysis)
```json
{
  "outline": "...",
  "suggestions": {
    "node_1": {
      "slide_type": "title",
      "visual_suggestion": "company_logo",
      "layout": "center_aligned"
    },
    "node_2": {
      "slide_type": "bullet_list",
      "visual_suggestion": "success_icon",
      "emphasis": ["Record quarter", "40%"]
    },
    "node_3": {
      "slide_type": "data_visualization",
      "chart_type": "bar_chart",
      "data_points": [
        {"label": "Users", "value": 1.2, "unit": "M", "change": "+25%"},
        {"label": "Revenue", "value": 4.5, "unit": "M", "change": "+30%"}
      ]
    }
  },
  "concepts": [
    {"text": "growth", "type": "positive", "icon": "trending_up"},
    {"text": "AI", "type": "technology", "icon": "robot"},
    {"text": "analytics", "type": "feature", "icon": "chart"}
  ]
}
```

### 4. Expected Slide JSON
```json
{
  "id": "slide_001",
  "version": "1.0",
  "type": "bullet",
  "title": "Overview",
  "content": {
    "main": [
      {"type": "bullet", "text": "Record quarter for user growth", "level": 1},
      {"type": "bullet", "text": "Three major features launched", "level": 1},
      {"type": "bullet", "text": "Improved system performance by 40%", "level": 1}
    ],
    "notes": "Emphasize the 40% performance improvement as a key technical achievement"
  },
  "metadata": {
    "source_node": "node_2",
    "order": 2,
    "section": "Overview"
  }
}
```

### 5. Expected Styled Slide JSON
```json
{
  "id": "slide_001",
  "type": "bullet",
  "title": {
    "text": "Overview",
    "style": {
      "font": "Arial",
      "size": 44,
      "color": "#1a1a1a",
      "weight": "bold",
      "position": {"x": 50, "y": 100}
    }
  },
  "content": {
    "bullets": [
      {
        "text": "Record quarter for user growth",
        "style": {
          "font": "Arial",
          "size": 24,
          "color": "#333333",
          "position": {"x": 70, "y": 200}
        },
        "icon": {"type": "checkmark", "color": "#4CAF50"}
      }
    ]
  },
  "background": {
    "color": "#ffffff",
    "gradient": {"start": "#ffffff", "end": "#f5f5f5", "angle": 90}
  },
  "theme_id": "corporate_blue"
}
```

## Test Cases by Module

### Parser Module Tests
```python
def test_parse_simple_outline():
    input_text = "# Title\n- Point 1\n- Point 2"
    result = parser.parse(input_text)
    assert result.title == "Title"
    assert len(result.nodes) == 2

def test_parse_nested_outline():
    input_text = "# Title\n## Section\n- Point\n  - Subpoint"
    result = parser.parse(input_text)
    assert result.nodes[0].children[0].level == 2

def test_parse_with_code_blocks():
    input_text = "# Code Example\n```python\nprint('hello')\n```"
    result = parser.parse(input_text)
    assert result.nodes[0].type == "code"

def test_handle_empty_input():
    with pytest.raises(ValueError):
        parser.parse("")

def test_parse_front_matter():
    input_text = "---\nauthor: John\n---\n# Title"
    result = parser.parse(input_text)
    assert result.metadata["author"] == "John"
```

### Analyzer Module Tests
```python
async def test_analyze_outline():
    outline = ParsedOutline(title="Test", nodes=[...])
    mock_llm = Mock(return_value="mock_response")
    analyzer = OutlineAnalyzer(mock_llm)
    result = await analyzer.analyze(outline)
    assert result.suggestions is not None

async def test_suggest_chart_for_data():
    node = OutlineNode(text="Sales: $1M, $2M, $3M")
    suggestions = await analyzer.suggest_slide_types(node)
    assert "chart" in suggestions

async def test_extract_concepts():
    text = "AI-powered analytics dashboard"
    concepts = await analyzer.extract_concepts(text)
    assert any(c.text == "AI" for c in concepts)
```

### Generator Module Tests
```python
def test_generate_title_slide():
    node = OutlineNode(level=0, text="Presentation Title")
    slide = generator.generate_slide(node, {})
    assert slide.type == SlideType.TITLE
    assert slide.title == "Presentation Title"

def test_generate_bullet_slide():
    node = OutlineNode(text="Section", children=[...])
    slide = generator.generate_slide(node, {})
    assert slide.type == SlideType.BULLET
    assert len(slide.content.main) == len(node.children)

def test_extract_speaker_notes():
    node = OutlineNode(text="Topic <!-- Note: Emphasize this -->")
    notes = generator.extract_speaker_notes(node)
    assert "Emphasize this" in notes
```

### Style Engine Tests
```python
def test_apply_theme():
    slide = Slide(title="Test", type=SlideType.BULLET)
    theme = Theme(id="default", colors={"primary": "#000000"})
    styled = style_engine.apply_theme(slide, theme)
    assert styled.title.style.color == "#000000"

def test_consistency_across_slides():
    slides = [Slide(...), Slide(...)]
    styled = style_engine.ensure_consistency(slides)
    assert styled[0].theme_id == styled[1].theme_id

def test_style_inheritance():
    theme = Theme(defaults={"font": "Arial"})
    slide = Slide(title="Test")
    styled = style_engine.apply_theme(slide, theme)
    assert styled.title.style.font == "Arial"
```

### Export Module Tests
```python
def test_export_to_pptx(tmp_path):
    presentation = Presentation(slides=[...])
    output = tmp_path / "test.pptx"
    result = exporter.export_pptx(presentation, output)
    assert output.exists()
    # Verify PowerPoint structure
    prs = pptx.Presentation(output)
    assert len(prs.slides) == len(presentation.slides)

def test_export_with_images():
    slide = Slide(assets=[Asset(type="image", path="test.png")])
    presentation = Presentation(slides=[slide])
    output = exporter.export_pptx(presentation, output_path)
    # Verify image is embedded
    prs = pptx.Presentation(output)
    assert len(prs.slides[0].shapes.placeholders) > 0
```

## End-to-End Test Scenarios

### Scenario 1: Basic Presentation
```python
async def test_complete_pipeline():
    # Input
    outline = "# Product Demo\n## Features\n- Feature A\n- Feature B"

    # Parse
    parsed = parser.parse(outline)
    assert parsed.title == "Product Demo"

    # Analyze
    enriched = await analyzer.analyze(parsed)
    assert len(enriched.suggestions) > 0

    # Generate
    slides = generator.generate_presentation(enriched)
    assert len(slides) >= 2

    # Style
    styled = style_engine.apply_theme(slides, default_theme)
    assert all(s.theme_id == "default" for s in styled)

    # Export
    presentation = assembler.assemble(styled)
    output = exporter.export_pptx(presentation, "test.pptx")
    assert Path("test.pptx").exists()
```

### Scenario 2: Style Change
```python
def test_restyle_presentation():
    # Load existing presentation
    presentation = storage.load_presentation("test_id")
    original_theme = presentation.theme.id

    # Apply new theme
    new_theme = theme_manager.get_theme("modern")
    restyled = style_engine.apply_theme(presentation.slides, new_theme)

    # Verify style changed but content unchanged
    assert restyled[0].theme_id == "modern"
    assert restyled[0].title == presentation.slides[0].title
    assert restyled[0].content == presentation.slides[0].content
```

### Scenario 3: Interactive Editing
```python
async def test_interactive_cli_session():
    # Simulate CLI interaction
    responses = [
        "Create a presentation about AI",
        "Add more detail to slide 2",
        "Change theme to modern",
        "Export to PowerPoint"
    ]

    cli = PresenterCLI(mock_storage, mock_llm)
    with mock_input(responses):
        result = await cli.run_interactive()

    assert result.presentation_id is not None
    assert Path(result.output_file).exists()
```

## Performance Benchmarks

### Target Metrics
- Parse 100-line outline: <100ms
- LLM analysis per slide: <2s
- Generate 10 slides: <5s
- Apply styling: <500ms
- Export to PPTX: <3s
- Total pipeline for 10-slide deck: <15s

### Test Implementation
```python
def test_performance_parse_large_outline():
    outline = generate_large_outline(lines=1000)
    start = time.time()
    parsed = parser.parse(outline)
    duration = time.time() - start
    assert duration < 1.0  # Should parse in under 1 second
    assert len(parsed.nodes) > 100

def test_performance_parallel_generation():
    slides = [create_slide() for _ in range(50)]
    start = time.time()
    styled = style_engine.apply_theme_parallel(slides, theme)
    duration = time.time() - start
    assert duration < 2.0  # Should style 50 slides in under 2 seconds
```

## Visual Regression Tests

### Approach
1. Generate reference presentations with known inputs
2. Store visual snapshots (PNG exports of slides)
3. Compare new outputs against references
4. Flag visual differences above threshold

### Implementation
```python
def test_visual_consistency():
    # Generate presentation
    presentation = generate_test_presentation()

    # Export to images
    images = export_to_images(presentation)

    # Compare with reference
    for i, img in enumerate(images):
        reference = load_reference_image(f"slide_{i}.png")
        diff = image_diff(img, reference)
        assert diff < 0.01  # Less than 1% difference
```

## Continuous Testing

### Pre-commit Hooks
- Run unit tests for changed modules
- Validate JSON schemas
- Check code formatting

### CI Pipeline
1. Run all unit tests
2. Run integration tests
3. Generate sample presentations
4. Check performance benchmarks
5. Run visual regression tests
6. Generate coverage report

### Coverage Goals
- Unit tests: >80% coverage
- Integration tests: All module boundaries
- E2E tests: Main user journeys