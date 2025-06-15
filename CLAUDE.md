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
- Maintain the 780-830 word count requirement
- Keep the callback mechanism without labels
- Ensure «???» markers for uncertain facts
- Never add cost info to script text files

### When Working with Models
- Use o3 with high reasoning effort for scripts
- Use o4-mini (NOT gpt-4o-mini) for phonetic conversion
- Always track actual token usage when available
- Report costs to console, not in files

### File Organization
- All actor files go in `output/actors/[actor_name]/`
- Use normalized names (lowercase, underscores)
- Handle case-insensitive folder matching
- Standard naming: `[actor]_script.txt`, `[actor]_PHONETIC_script.txt`

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

## Next Steps (Phase 2)
The project is ready for video planning implementation:
- Script chunking (3-10 second segments)
- AI prompt generation for images/videos
- Music description generation
- Integration with `[actor]_step2_data.json`

## Important Notes
- Always use high reasoning effort in production
- Cost tracking must show actual API usage
- Folder system is mandatory for all new features
- Maintain backwards compatibility with existing scripts