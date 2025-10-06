# Module Specifications

## Module Contracts and Interfaces

### 1. Parser Module
```python
class OutlineParser:
    def parse(self, input_text: str) -> ParsedOutline:
        """Parse text input into structured outline."""

    def validate(self, outline: ParsedOutline) -> bool:
        """Validate outline structure."""

class ParsedOutline:
    title: str
    nodes: List[OutlineNode]
    metadata: Dict[str, Any]

class OutlineNode:
    level: int
    text: str
    children: List[OutlineNode]
    node_type: str  # heading, bullet, note, etc.
```

**Input**: Raw text (Markdown, plain text, OPML)
**Output**: Structured JSON outline
**Dependencies**: None
**Tests**: Parse various outline formats, handle edge cases

### 2. Analyzer Module
```python
class OutlineAnalyzer:
    def __init__(self, llm_client: LLMClient):
        pass

    async def analyze(self, outline: ParsedOutline) -> EnrichedOutline:
        """Analyze outline and add semantic information."""

    async def suggest_slide_types(self, node: OutlineNode) -> List[str]:
        """Suggest appropriate slide types for content."""

    async def extract_concepts(self, text: str) -> List[Concept]:
        """Extract key concepts for visualization."""

class EnrichedOutline:
    outline: ParsedOutline
    suggestions: Dict[str, SlideSuggestion]
    concepts: List[Concept]
```

**Input**: ParsedOutline
**Output**: EnrichedOutline with metadata
**Dependencies**: LLM module
**Tests**: Mock LLM responses, verify suggestions

### 3. Generator Module
```python
class SlideGenerator:
    def generate_slide(self, node: OutlineNode, metadata: Dict) -> Slide:
        """Generate slide from outline node."""

    def generate_presentation(self, outline: EnrichedOutline) -> List[Slide]:
        """Generate all slides from outline."""

    def extract_speaker_notes(self, node: OutlineNode) -> str:
        """Extract speaker notes from content."""

class Slide:
    id: str
    type: SlideType
    title: str
    content: SlideContent
    notes: str
    metadata: Dict
```

**Input**: EnrichedOutline
**Output**: List of Slide objects (JSON serializable)
**Dependencies**: None
**Tests**: Various outline structures, slide types

### 4. Style Module
```python
class StyleEngine:
    def __init__(self, theme_manager: ThemeManager):
        pass

    def apply_theme(self, slide: Slide, theme: Theme) -> StyledSlide:
        """Apply theme to slide."""

    def ensure_consistency(self, slides: List[Slide]) -> List[StyledSlide]:
        """Ensure visual consistency across slides."""

class Theme:
    id: str
    name: str
    colors: ColorPalette
    fonts: FontSettings
    layouts: Dict[SlideType, Layout]
```

**Input**: Slide + Theme
**Output**: StyledSlide with visual properties
**Dependencies**: Theme Manager
**Tests**: Theme application, consistency checks

### 5. Asset Module
```python
class AssetManager:
    def __init__(self, cache_dir: Path):
        pass

    async def fetch_icon(self, concept: str) -> Asset:
        """Fetch icon for concept."""

    async def generate_chart(self, data: ChartData) -> Asset:
        """Generate chart from data."""

    def optimize_image(self, image: Asset) -> Asset:
        """Optimize image for presentation."""

class Asset:
    id: str
    type: AssetType  # image, icon, chart
    path: Path
    metadata: Dict
```

**Input**: Asset requests
**Output**: Asset objects with file paths
**Dependencies**: External APIs, matplotlib
**Tests**: Asset generation, caching

### 6. Layout Module
```python
class LayoutEngine:
    def layout_slide(self, slide: StyledSlide) -> PositionedSlide:
        """Position elements on slide."""

    def auto_fit_text(self, text: str, bounds: Rectangle) -> TextLayout:
        """Fit text within bounds."""

    def arrange_elements(self, elements: List[Element]) -> List[PositionedElement]:
        """Arrange multiple elements."""

class PositionedSlide:
    slide: StyledSlide
    elements: List[PositionedElement]
```

**Input**: StyledSlide
**Output**: PositionedSlide with coordinates
**Dependencies**: None
**Tests**: Layout algorithms, edge cases

### 7. Assembler Module
```python
class PresentationAssembler:
    def assemble(self, slides: List[PositionedSlide]) -> Presentation:
        """Assemble slides into presentation."""

    def apply_transitions(self, presentation: Presentation, transitions: TransitionSet):
        """Apply transitions between slides."""

    def merge_presentations(self, *presentations: Presentation) -> Presentation:
        """Merge multiple presentations."""

class Presentation:
    id: str
    title: str
    slides: List[PositionedSlide]
    theme: Theme
    settings: PresentationSettings
```

**Input**: List of slides
**Output**: Complete presentation object
**Dependencies**: None
**Tests**: Assembly, merging, reordering

### 8. Export Module
```python
class ExportEngine:
    def export_pptx(self, presentation: Presentation, output: Path) -> Path:
        """Export to PowerPoint format."""

    def export_pdf(self, presentation: Presentation, output: Path) -> Path:
        """Export to PDF format."""

    def export_html(self, presentation: Presentation, output: Path) -> Path:
        """Export to HTML/S5 format."""

class ExportOptions:
    format: ExportFormat
    quality: str  # draft, normal, high
    embed_assets: bool
    compression: bool
```

**Input**: Presentation object
**Output**: File in specified format
**Dependencies**: python-pptx, reportlab, jinja2
**Tests**: Export formats, asset embedding

### 9. Storage Module
```python
class StorageManager:
    def __init__(self, storage_path: Path):
        pass

    def save_slide(self, slide: Slide) -> str:
        """Save individual slide."""

    def save_presentation(self, presentation: Presentation) -> str:
        """Save complete presentation."""

    def load_presentation(self, presentation_id: str) -> Presentation:
        """Load presentation from storage."""

    def get_history(self, presentation_id: str) -> List[Version]:
        """Get version history."""

class Version:
    id: str
    timestamp: datetime
    changes: List[Change]
    author: str
```

**Input**: Slides/Presentations
**Output**: Stored data with IDs
**Dependencies**: SQLite, filesystem
**Tests**: CRUD operations, versioning

### 10. LLM Module
```python
class LLMClient:
    def __init__(self, api_key: str, model: str = "claude-3"):
        pass

    async def complete(self, prompt: str, system: str = None) -> str:
        """Get completion from LLM."""

    async def converse(self, messages: List[Message]) -> str:
        """Continue conversation."""

    def build_prompt(self, template: str, **kwargs) -> str:
        """Build prompt from template."""

class Message:
    role: str  # user, assistant, system
    content: str
```

**Input**: Prompts and conversation history
**Output**: LLM responses
**Dependencies**: anthropic-sdk-python
**Tests**: Mock responses, prompt building

### 11. CLI Module
```python
class PresenterCLI:
    def __init__(self, storage: StorageManager, llm: LLMClient):
        pass

    def run_interactive(self, outline_file: Path = None):
        """Run interactive session."""

    def generate(self, input_file: Path, output_file: Path, theme: str = "default"):
        """Generate presentation from file."""

    def edit_presentation(self, presentation_id: str):
        """Edit existing presentation."""

class CLICommands:
    new: Create new presentation
    edit: Edit existing presentation
    list: List presentations
    export: Export presentation
    preview: Preview slides
```

**Input**: User commands and files
**Output**: Generated presentations
**Dependencies**: All other modules
**Tests**: End-to-end scenarios

## Inter-Module Communication

### Data Flow
1. **Parser** → ParsedOutline → **Analyzer**
2. **Analyzer** → EnrichedOutline → **Generator**
3. **Generator** → Slides → **Style Engine**
4. **Style Engine** → StyledSlides → **Layout Engine**
5. **Layout Engine** → PositionedSlides → **Assembler**
6. **Assembler** → Presentation → **Export Engine**
7. **Export Engine** → Output Files

### Async Operations
- LLM calls (Analyzer, CLI)
- Asset fetching (Asset Manager)
- File I/O (Storage, Export)

### Error Handling
- Each module returns Result[T, Error] types
- Errors bubble up with context
- CLI provides user-friendly error messages
- All errors logged with full stack traces