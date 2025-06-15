# OpenAI API Cost Analysis for Script Generation

## Overview
Analyzing the cost implications of different approaches for the script generation agent.

**Last Updated**: June 15, 2025 - Now with actual production data!

## Key Considerations

### 1. Actual Token Usage (from Production)
- **Input tokens**: ~2,700 (includes full prompt + system instructions)
- **Output tokens**: 1,000-3,000 (varies by script complexity)
- **Reasoning tokens**: ~180% of output tokens (with high reasoning effort)
- **Total per request**: 3,700-8,000 tokens

### 2. Cost Comparison

#### Option A: Full Prompt Every Time
- Input tokens per request: ~285 tokens
- No persistent state needed
- Simple implementation

#### Option B: Persistent Agent with Instructions
- Initial setup: Store base instructions in agent
- Per request: Only send actor name + minimal context
- Input tokens per request: ~50-100 tokens (significant reduction)

#### Option C: Fine-tuned Model
- Train a model specifically for biography scripts
- Minimal prompt needed per request
- Higher upfront cost but lowest per-request cost

### 3. OpenAI Agents SDK Specifics

The SDK doesn't inherently save tokens by storing instructions. Each API call still sends the full context. However, the SDK provides:

1. **Better Organization**: Clean separation of concerns
2. **Tracing & Debugging**: Built-in monitoring
3. **Error Handling**: Robust retry logic
4. **Future-proofing**: Easy to switch models or add tools

### 4. Recommendations

**For your use case, I recommend:**

1. **Short term (Development/Testing)**: Use the Agents SDK with the full prompt template. This gives you:
   - Flexibility to iterate on the prompt
   - Easy A/B testing of different instructions
   - Built-in tracing to debug issues

2. **Medium term (Production)**: Consider creating a custom GPT or Assistant via the Assistants API:
   - Store instructions persistently
   - Reduce per-request token usage by ~70%
   - Maintain conversation context if needed

3. **Long term (Scale)**: Fine-tune a model:
   - Lowest per-request cost
   - Fastest response times
   - Most consistent outputs

## Cost Calculations

### Actual o3 Pricing (as of June 2025)
- **o3 model**: $2/1M input tokens, $8/1M output tokens
- **o4-mini**: ~$1/1M input tokens, ~$4/1M output tokens

### Real Production Costs

#### Script Generation (o3 with high reasoning):
- Input: 2,700 tokens × $2/1M = $0.0054
- Output: 3,000 tokens × $8/1M = $0.024
- **Total per script**: $0.013-$0.016

#### Phonetic Conversion (o4-mini):
- Input: ~1,000 tokens × $1/1M = $0.001
- Output: ~1,000 tokens × $4/1M = $0.004
- **Total per phonetic**: ~$0.001

#### Combined Cost per Actor:
- **Total: $0.014-$0.017 per complete script set**

### At Scale (1,000 scripts/month):
- Script generation: ~$15/month
- Phonetic conversion: ~$1/month
- **Total monthly cost: ~$16**

### Cost Optimization Insights:
1. **Reasoning tokens are expensive**: ~180% of output tokens
2. **High reasoning worth it**: Better quality scripts, fewer retries
3. **o4-mini efficient**: Good balance for phonetic conversion
4. **Folder system saves money**: Reuse existing scripts when possible

## Next Steps

1. Start with the simple full-prompt approach
2. Monitor actual token usage with the SDK's tracing
3. Optimize once you have real usage data
4. Consider Assistants API when ready for production