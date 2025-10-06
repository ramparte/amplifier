# Sample Inputs and Outputs

## Test Case 1: Simple Business Presentation

### Input (outline.md)
```markdown
# Q4 2024 Results

## Financial Performance
- Revenue: $12.5M (+25% YoY)
- EBITDA: $3.2M (26% margin)
- Cash flow positive for 6 consecutive quarters

## Customer Growth
- Total customers: 5,200 (+40% YoY)
- Enterprise accounts: 120 (+60% YoY)
- Net retention rate: 115%
- NPS score: 72

## Product Highlights
### New Features Launched
- AI-powered analytics dashboard
- Real-time collaboration tools
- Mobile app (iOS and Android)

### Usage Metrics
- DAU: 3,500 users
- Average session: 42 minutes
- Features adopted: 85% using 3+ features

## Q1 2025 Priorities
1. Launch enterprise tier
2. Expand to European market
3. Add predictive analytics
4. Improve onboarding flow
```

### Expected JSON Output (slide_002.json)
```json
{
  "id": "slide_002",
  "type": "data_chart",
  "title": "Financial Performance",
  "content": {
    "chart": {
      "type": "column",
      "data": [
        {"label": "Revenue", "value": 12.5, "unit": "$M", "change": "+25%"},
        {"label": "EBITDA", "value": 3.2, "unit": "$M", "change": "26% margin"}
      ],
      "colors": ["#2E7D32", "#1976D2"]
    },
    "bullets": [
      {"text": "Cash flow positive for 6 consecutive quarters", "emphasis": true}
    ],
    "notes": "Highlight the consistent cash flow positive status"
  },
  "style": {
    "theme": "corporate",
    "layout": "two_column",
    "background": "gradient_subtle"
  },
  "assets": [
    {
      "type": "icon",
      "name": "trending_up",
      "position": {"x": 850, "y": 100},
      "size": 48,
      "color": "#2E7D32"
    }
  ],
  "animations": {
    "entrance": "fade_in",
    "chart": "grow_from_bottom",
    "bullets": "appear_sequential"
  }
}
```

### CLI Interaction
```bash
$ presenter generate outline.md --theme corporate
Parsing outline... ✓
Analyzing content with AI... ✓
Generating 6 slides... ✓
Applying corporate theme... ✓
Exporting to PowerPoint... ✓

Output: Q4_2024_Results.pptx (6 slides)

Would you like to:
1. Preview slides
2. Edit a specific slide
3. Change theme
4. Export
5. Exit

> 1

Slide 1/6: [Title] Q4 2024 Results
Slide 2/6: [Chart] Financial Performance
Slide 3/6: [Data] Customer Growth
...
```

## Test Case 2: Technical Architecture Document

### Input
```markdown
# Microservices Migration Plan

## Current Architecture
- Monolithic Rails application
- PostgreSQL database (500GB)
- 15-year old codebase
- 200k LOC

## Target Architecture
### Service Decomposition
- User Service
- Product Service
- Order Service
- Payment Service
- Notification Service

### Technology Stack
- Services: Node.js/Go
- Communication: gRPC/REST
- Message Queue: Kafka
- Databases: PostgreSQL, MongoDB, Redis

## Migration Strategy
### Phase 1: Strangler Fig Pattern
- Start with edge services
- Notification service first
- No database migration yet

### Phase 2: Data Decomposition
- Split databases by domain
- Implement event sourcing
- Add CQRS where needed

### Phase 3: Core Services
- Migrate business logic
- Implement saga patterns
- Add circuit breakers
```

### Expected Enriched Analysis
```json
{
  "suggestions": {
    "slide_1": {
      "type": "title",
      "enhancement": "Add company logo and migration timeline"
    },
    "slide_2": {
      "type": "comparison",
      "layout": "side_by_side",
      "visual": "architecture_diagram",
      "suggestion": "Show before/after architecture visually"
    },
    "slide_3": {
      "type": "diagram",
      "diagram_type": "service_map",
      "suggestion": "Create service dependency graph"
    },
    "slide_4": {
      "type": "timeline",
      "visual": "gantt_chart",
      "phases": ["Phase 1: 3 months", "Phase 2: 6 months", "Phase 3: 6 months"]
    }
  },
  "concepts": [
    {"term": "Strangler Fig", "definition": "Gradual replacement pattern", "visual": "tree_diagram"},
    {"term": "Event Sourcing", "complexity": "high", "explanation_needed": true},
    {"term": "CQRS", "related_to": "Event Sourcing", "visual": "flow_diagram"}
  ],
  "recommendations": [
    "Add risk mitigation slide",
    "Include rollback strategy",
    "Add team structure/responsibilities",
    "Include success metrics"
  ]
}
```

## Test Case 3: Interactive Session

### User Conversation
```
User: I need to create a presentation about our new product launch