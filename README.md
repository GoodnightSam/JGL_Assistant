# JGL Assistant - AI-Powered Biography Script Generator

An AI-powered tool for generating professional biography scripts for YouTube videos using OpenAI's o3 model, with automatic phonetic conversion for text-to-speech (TTS) systems.

## Features

- Generates 5-minute biography scripts (780-830 words)
- Automatic phonetic conversion for ElevenLabs TTS compatibility
- Professional sports-documentary storytelling style
- Structured format with HOOK and BIO sections
- Converts difficult proper nouns to phonetic spelling
- Automatic validation and error handling
- Cost estimation per script
- Simple command-line interface

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
2. Generate a biography script using o3 model
3. Generate a phonetic version for TTS using gpt-4o-mini
4. Save both versions as text files in `output/scripts/`
5. Show cost estimation

Type 'quit' to exit the application.

## Script Format

Scripts include:
- **HOOK**: Attention-grabbing opening (3 fragments + catchphrase)
- **BIO**: Full biography narrative with:
  - At least 8 year stamps
  - Actor's age mentioned at least twice
  - A tension-raising question around 80-90 seconds
  - Humorous callbacks throughout

## Project Structure

```
JGL_Assistant/
├── main.py                    # Main application entry point
├── production_script_generator.py  # Script generation logic
├── phonetic_generator.py      # Phonetic conversion for TTS
├── requirements.txt           # Python dependencies
├── .env                      # API key configuration (not in git)
├── .gitignore               # Git ignore file
├── output/                  # Generated scripts
│   └── scripts/            # Text files (original & phonetic)
└── dev/                    # Development files
    └── llm/               # JSON backups
```

## Cost

Approximate cost per actor:
- Original script (o3 model): ~$0.01-0.02
- Phonetic script (gpt-4o-mini): ~$0.001
- Total: ~$0.02 per complete script set

## License

MIT License

## Contributing

Pull requests are welcome. For major changes, please open an issue first.