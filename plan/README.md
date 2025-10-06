# Presenter Pipeline - Project Plan

## Project Overview
A modular, test-driven pipeline for converting text outlines into professional PowerPoint presentations with rich graphics and consistent styling.

## Key Features
- **Text to PowerPoint**: Convert markdown/text outlines to professional presentations
- **AI Enhancement**: Use LLMs to improve content and suggest visualizations
- **Style Separation**: Apply different themes without regenerating content
- **Individual Slide Storage**: Rearrange and merge presentations easily
- **Interactive CLI**: Conversational interface for iterative refinement
- **Test-First Development**: Comprehensive test coverage from the start

## Architecture Highlights

### Modular Pipeline
```
Text → Parser → Analyzer → Generator → Style → Layout → Assembly → Export → PowerPoint
```

Each module:
- Has a single responsibility
- Defined contract/interface
- Can be tested in isolation
- Produces JSON intermediate format

### Content vs Style Separation
- **Content Pipeline**: Parser → Analyzer → Generator
- **Style Pipeline**: Style Engine → Layout Engine
- **Export Pipeline**: Assembler → Export Engine

This allows:
- Changing themes without regenerating content
- Multiple style variants of same presentation
- Progressive enhancement of slides

## Plan Documents

### Core Documents
1. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and module definitions
2. **[MODULE_SPECS.md](MODULE_SPECS.md)** - Detailed module contracts and interfaces
3. **[TASK_LIST.md](TASK_LIST.md)** - Complete implementation task breakdown (8 weeks)
4. **[TEST_PLAN.md](TEST_PLAN.md)** - TDD approach with sample test cases
5. **[IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)** - Development workflow and quick start
6. **[SAMPLE_INPUTS_OUTPUTS.md](SAMPLE_INPUTS_OUTPUTS.md)** - Concrete examples of data flow

## Next Session Tasks

### Immediate Actions (Session 2)
1. **Initialize Python Project**
   ```bash
   cd /mnt/c/Users/samschillace/presenter
   # Create pyproject.toml with dependencies
   # Set up pytest framework
   # Create basic directory structure
   ```

2. **Start Parser Module (TDD)**
   - Write test_parser.py first
   - Implement markdown parsing
   - Create sample test fixtures

3. **Define Data Models**
   - Slide model (Pydantic)
   - Presentation model
   - Theme model

### Quick Commands for Next Session
```bash
# Navigate to project
cd /mnt/c/Users/samschillace/presenter

# View task list
cat plan/TASK_LIST.md

# Check architecture
cat plan/ARCHITECTURE.md

# See test examples
cat plan/TEST_PLAN.md
```

## Development Philosophy

### Test-First Development
1. Write test describing desired behavior
2. Run test (see it fail)
3. Write minimal code to pass
4. Refactor for clarity
5. Repeat

### Modular Implementation
- Build one module at a time
- Test in isolation first
- Then test integration
- Keep modules loosely coupled

### Progressive Enhancement
- Start with basic text slides
- Add styling layer
- Add graphics/charts
- Add animations
- Each layer independent

## Success Metrics

### MVP (2 weeks)
- Parse markdown outline ✓
- Generate JSON slides ✓
- Export basic PowerPoint ✓
- 5 test presentations working ✓

### Enhanced (4 weeks)
- LLM content enhancement ✓
- Multiple themes ✓
- Interactive CLI ✓
- Asset generation ✓

### Production (8 weeks)
- Web interface ✓
- Collaboration features ✓
- 100+ slide support ✓
- <30 second generation ✓

## Key Design Decisions Made

1. **JSON as intermediate format** - LLM and human readable
2. **Filesystem + SQLite storage** - Simple, no external dependencies
3. **Content/style separation** - Enables re-theming
4. **Module independence** - Each module can be regenerated
5. **Test-first approach** - Ensures reliability from start

## Important Reminders

### For Future Sessions
- Always check TASK_LIST.md for next tasks
- Update task status after completion
- Run tests before committing code
- Document any design changes
- Keep intermediate JSON format stable

### Architecture Principles
- Each module does ONE thing well
- Modules communicate through JSON
- No module depends on another's internals
- All modules independently testable
- Prefer composition over inheritance

## Contact Points for Questions

When resuming work:
1. Review this README first
2. Check TASK_LIST.md for current status
3. Read IMPLEMENTATION_ROADMAP.md for workflow
4. Consult MODULE_SPECS.md for interfaces
5. Use TEST_PLAN.md for test examples

## Repository Structure
```
presenter/
├── plan/                 # All planning documents (THIS FOLDER)
│   ├── README.md        # This file
│   ├── ARCHITECTURE.md  # System design
│   ├── MODULE_SPECS.md  # Module contracts
│   ├── TASK_LIST.md    # Task tracking
│   ├── TEST_PLAN.md    # Test strategy
│   └── ...
├── pyproject.toml       # (To be created)
├── presenter/           # (To be created - source code)
├── tests/              # (To be created - test files)
└── data/               # (To be created - themes, assets)
```

---

**Project Status**: Planning Complete ✓
**Next Step**: Begin implementation with Parser module using TDD
**Estimated Timeline**: 8 weeks to production
**Approach**: Modular, test-first, incremental delivery