# Claude Assistant Instructions

## Project Understanding
This is the JGL Assistant project - an AI-powered biography script generator for YouTube videos. When working on this project:

1. **Primary Goal**: Generate high-quality, TTS-ready biography scripts about actors/celebrities
2. **Style**: Sports-documentary narrator voice targeting 45-65 year old audience
3. **Technical Stack**: Python, OpenAI API (o3 and o4-mini models)

## Key Commands
- `/gogit` - Commit and push changes to git
- `/fresh` - Start fresh context
- `/next` - Continue to next task
- `/reviewIT` - Review recent changes

## Code Guidelines

### When Modifying Script Generation
- Always preserve the 11 prompt guidelines
- No strict word count gatekeeping (accept any length)
- Keep the callback mechanism without labels
- Ensure «???» markers for uncertain facts
- Never add cost info to script text files
- Only require HOOK and BIO sections for validation

### When Working with Models
- Use o3 with high reasoning effort for scripts
- Use o4-mini (NOT gpt-4o-mini) for phonetic conversion
- Always track actual token usage when available
- Report costs to console AND save to cost_tracking.json
- Each operation adds timestamped entry with model, cost, and usage

### File Organization
- All actor files go in `output/actors/[actor_name]/`
- Use normalized names (lowercase, underscores)
- Handle case-insensitive folder matching
- Standard naming:
  - `[actor]_script.txt` - Main biography script
  - `[actor]_PHONETIC_script.txt` - TTS-ready version
  - `[actor]_storyboard.json` - 45+ shot breakdown
  - `[actor]_music_plan.json` - 3 AI music prompts
  - `[actor]_image_metadata.json` - Downloaded image info
  - `[actor]_cost_tracking.json` - API cost tracking
  - `images/` - Downloaded images (1B.jpg, 1C.png, etc.)

## Testing Approach
- Test with short actor names first (saves tokens)
- Monitor script_generation.log for issues
- Check for callback labeling problems
- Verify folder creation and file placement

## Common Issues & Solutions
1. **"Callback 1:" appearing**: Update prompt to emphasize no labels
2. **High costs**: Check reasoning tokens (can be 180%+ of output)
3. **Model confusion**: o4-mini vs gpt-4o-mini (use o4-mini)
4. **Case sensitivity**: Use folder_manager.normalize_actor_name()
5. **Script rejection**: Now accepts any script with HOOK/BIO sections
6. **Image download failures**: Enhanced searcher retries with next results
7. **Watermarked images**: Avoids known watermark domains (Getty, Shutterstock)

## Next Steps (Phase 2-3)
The project has implemented:
- ✓ Script chunking (3-10 second segments) via storyboard
- ✓ AI prompt generation for images/videos
- ✓ Music description generation
- ✓ Google Image search and download (Step 3)
- ✓ All saved in actor-specific folders

Ready for Phase 4:
- AI image generation (FLUX/SDXL)
- Video clip searching
- Final assembly

## Important Notes
- Always use high reasoning effort in production
- Cost tracking must show actual API usage
- Folder system is mandatory for all new features
- Maintain backwards compatibility with existing scripts
- Cost tracking JSON persists all operations per actor
- Google API: 100 free searches/day, track usage in .google_api_usage.json
- Images named with shot# + letter (1B, 1C, etc) - A reserved for AI images
- Enhanced image searcher: validates, deduplicates, retries, generates thumbnails
- Downloads 10 images per shot using threading for speed
- Tracks failed domains to avoid problematic sources