# JGL Assistant - AI-Powered Biography Script Generator

An AI-powered tool for generating professional biography scripts for YouTube videos using OpenAI's o3 model with high reasoning effort, featuring automatic phonetic conversion for text-to-speech (TTS) systems.

## Features

- Generates 5-minute biography scripts (780-830 words) with o3 high reasoning
- Automatic phonetic conversion for TTS using o4-mini model
- Professional sports-documentary storytelling style targeting 45-65 year olds
- Structured format with HOOK and BIO sections
- Actor-specific folder organization
- Script existence checking with overwrite options
- Real-time token usage and cost tracking from OpenAI API
- Handles personal flaws/controversies with candor
- Factual safety with «???» markers for uncertain information
- Case-insensitive actor name handling
- Comprehensive error handling and retry logic

## Requirements

- Python 3.8+
- OpenAI API key with o3 model access
- Organization verification for o3 model

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/JGL_Assistant.git
cd JGL_Assistant
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your OpenAI API key:
   - Copy `.env.example` to `.env`
   - Add your API key: `OPENAI_API_KEY=your-api-key-here`

## Usage

Run the application:
```bash
python main.py
```

The app will:
1. Ask for an actor's name
2. Check for existing scripts and offer options:
   - Use existing script (proceed to Step 2 - coming soon)
   - Generate new script (overwrites existing)
   - Cancel
3. Generate a biography script using o3 model with high reasoning
4. Generate a phonetic version for TTS using o4-mini
5. Save both versions in actor-specific folder: `output/actors/[actor_name]/`
6. Display actual token usage and costs from OpenAI API

Type 'quit' to exit the application.

## Script Format

Scripts include:
- **HOOK**: Attention-grabbing opening (3 fragments + surprise facet + imperative callback)
- **BIO**: Full biography narrative with:
  - 6-9 year stamps (max one date OR age per sentence)
  - Actor's age mentioned at least twice
  - A naturally arising tension question around 80-90 seconds
  - Single motif with exactly 3 callbacks (no labels)
  - At least one personal flaw/controversy handled candidly
  - Emotional legacy reflection ending
  - «???» markers for uncertain facts

## Project Structure

```
JGL_Assistant/
├── main.py                        # Main application entry point
├── production_script_generator.py # Script generation with o3 high reasoning
├── phonetic_generator.py          # Phonetic conversion using o4-mini
├── folder_manager.py             # Actor folder organization system
├── requirements.txt              # Python dependencies
├── .env                         # API key configuration (not in git)
├── .gitignore                   # Git ignore file
├── TASKS.md                     # Project task tracking
├── CONTEXT.md                   # Project context and architecture
├── CLAUDE.md                    # Claude assistant instructions
├── output/                      # Generated content
│   └── actors/                 # Actor-specific folders
│       └── [actor_name]/      # Normalized actor folder
│           ├── [actor]_script.txt           # Original script
│           ├── [actor]_PHONETIC_script.txt  # Phonetic version
│           ├── [actor]_script_data.json     # Generation metadata
│           └── [actor]_step2_data.json      # Future video planning
├── dev/                         # Development files
│   └── llm/                    # Logs and JSON backups
└── docs/                       # Documentation
    └── PROJECT_DETAILS.md      # Extended project vision
```

## Cost

Actual costs per script (with high reasoning effort):
- Original script (o3 model): $0.013-$0.016
  - Input tokens: ~2,700
  - Output tokens: ~1,000-3,000
  - Reasoning tokens: ~180% of output tokens
- Phonetic script (o4-mini): ~$0.001
- **Total: $0.014-$0.017 per complete script set**

Generation time: 47-177 seconds depending on complexity

## License

MIT License

## Contributing

Pull requests are welcome. For major changes, please open an issue first.