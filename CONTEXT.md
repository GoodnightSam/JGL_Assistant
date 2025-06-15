# JGL Assistant - Project Context

## Project Overview
JGL Assistant is an AI-powered biography script generator designed for YouTube content creation. It generates 5-minute biography scripts (780-830 words) about actors and celebrities in a sports-documentary style, optimized for text-to-speech narration.

## Current Architecture

### Core Components
1. **Script Generation** (`production_script_generator.py`)
   - Uses OpenAI o3 model with high reasoning effort
   - Implements comprehensive prompt engineering
   - Includes retry logic and error handling
   - Tracks actual token usage and costs

2. **Phonetic Conversion** (`phonetic_generator.py`)
   - Uses o4-mini model for cost-effective conversion
   - Converts difficult proper nouns for TTS compatibility
   - Preserves script structure and formatting

3. **Folder Management** (`folder_manager.py`)
   - Organizes projects by actor in dedicated folders
   - Handles case-insensitive name matching
   - Manages script versioning and overwrites

4. **Main Application** (`main.py`)
   - Interactive CLI interface
   - Script existence checking
   - Cost tracking and reporting
   - Folder-based file organization

## Key Design Decisions

### Model Selection
- **o3 with high reasoning**: Chosen for superior creative output despite higher cost
- **o4-mini**: Selected for phonetic conversion to balance quality and cost
- **Reasoning effort**: Set to "high" for maximum script quality

### Prompt Engineering
The o3 prompt includes 11 detailed guidelines:
1. Word count control (780-830 words)
2. Tense consistency rules
3. Target demographic voice (45-65 year olds)
4. Date/age placement restrictions
5. Suspense moment timing
6. Callback engine (motif repetition)
7. Realism clause (flaws/controversies)
8. Emotional closure
9. Factual safety with «???» markers
10. Language rhythm variation
11. Output sanitation (no meta-text)

### File Organization
```
output/
└── actors/
    └── [actor_name]/
        ├── [actor_name]_script.txt
        ├── [actor_name]_PHONETIC_script.txt
        ├── [actor_name]_script_data.json
        └── [actor_name]_step2_data.json (future)
```

## Performance Characteristics
- **Generation time**: 47-177 seconds per script
- **Token usage**: 
  - Input: ~2,700 tokens (includes full prompt)
  - Output: 1,000-3,000 tokens
  - Reasoning: ~180% of output tokens
- **Cost per script**: $0.01-0.02 (varies with reasoning)

## Future Integration Points
The project is designed to support a full video production pipeline:
1. Script chunk analysis (3-10 second segments)
2. AI image/video generation prompts
3. Music description generation
4. Asset search and collection
5. Video editing automation
6. YouTube upload integration

## Development Environment
- Python 3.8+
- Virtual environment with dependencies in `requirements.txt`
- Environment variables in `.env` (OPENAI_API_KEY required)
- Logging to `dev/llm/script_generation.log`
- JSON backups in actor folders and `dev/llm/`