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

4. Set up your API keys:
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key: `OPENAI_API_KEY=your-api-key-here`
   - For Step 3 (Image Search), add Google API credentials:
     - `GOOGLE_API_KEY=your-google-api-key`
     - `GOOGLE_SEARCH_ENGINE_ID=your-search-engine-id`
     - See "Google API Setup" section below for details

## Usage

Run the application:
```bash
python main.py
```

The app will:
1. Ask for an actor's name
2. Check for existing scripts and offer options:
   - Use existing script (proceed to Step 2)
   - Generate new script (overwrites existing)
   - Cancel
3. Generate a biography script using o3 model with high reasoning
4. Generate a phonetic version for TTS using o4-mini
5. **Step 2**: Generate storyboard (45+ shots) and music plan (3 AI prompts)
6. **Step 3**: Search and download Google Images for each shot
7. Save everything in actor-specific folder: `output/actors/[actor_name]/`
8. Display actual token usage and costs from OpenAI API

Type 'quit' to exit the application.

## Google API Setup

For Step 3 (Image Search), you need Google Custom Search API credentials:

### 1. Get Google API Key:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable "Custom Search API"
4. Go to "Credentials" → "Create Credentials" → "API Key"
5. Copy the API key

### 2. Get Search Engine ID:
1. Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Click "Add" to create a new search engine
3. Configure:
   - Enable "Image search"
   - Enable "Search the entire web"
4. Copy the "Search engine ID"

### 3. Add to .env:
```
GOOGLE_API_KEY=your_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
```

**Note**: Google provides 100 free searches per day. Additional searches cost $5 per 1000 queries.

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
│           ├── [actor]_storyboard.json      # 45+ shot breakdown
│           ├── [actor]_music_plan.json      # 3 AI music prompts
│           ├── [actor]_image_metadata.json  # Downloaded image info
│           ├── [actor]_cost_tracking.json   # API cost tracking
│           └── images/                      # Downloaded images
│               ├── 1B.jpg, 1C.png, ...     # Shot 1 images
│               └── 2B.jpg, 2C.png, ...     # Shot 2 images
├── dev/                         # Development files
│   └── llm/                    # Logs and JSON backups
└── docs/                       # Documentation
    └── PROJECT_DETAILS.md      # Extended project vision
```

## Cost

Actual costs per complete video project (with high reasoning effort):
- **Step 1**: Script Generation
  - Original script (o3): $0.013-$0.036
  - Phonetic script (o4-mini): ~$0.001
- **Step 2**: Video Planning
  - Storyboard (o3): $0.10-$0.21
  - Music plan (o3): $0.01-$0.02
- **Step 3**: Image Search
  - Google API: FREE (first 100 searches/day)
- **Total: $0.12-$0.27 per complete project**

Generation time: 5-10 minutes total

## License

MIT License

## Contributing

Pull requests are welcome. For major changes, please open an issue first.