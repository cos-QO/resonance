# LLM Integration Standards

> Scope: Application LLM integration standards (providers, routing, env). Stable by default; changes require PM/Product Manager approval and rationale in `/.claude/memory/standards/CHANGELOG.md`.

## Overview
Comprehensive standards for LLM integration using OpenRouter API and multi-model architecture for optimal cost, performance, and capability distribution.

## Architecture Standards

### Primary Provider: OpenRouter
- **Base URL**: `https://openrouter.ai/api/v1`
- **Benefits**: Model diversity, cost optimization, unified API
- **Models**: Claude-3.5-Sonnet, GPT-4o, GPT-4o-mini, and others
- **Billing**: Per-token pricing with usage tracking

### Model Selection Strategy

#### **Primary Models:**
```json
{
  "reasoning": "claude-3.5-sonnet-20241022",
  "general": "openai/gpt-4o",
  "cost_efficient": "openai/gpt-4o-mini",
  "creative": "anthropic/claude-3-opus",
  "code": "openai/o1-preview"
}
```

#### **Model Assignment Guidelines:**
- **Claude-3.5-Sonnet**: Complex reasoning, analysis, planning
- **GPT-4o**: General purpose, balanced performance
- **GPT-4o-mini**: High-volume, cost-sensitive operations
- **Claude-3-Opus**: Creative writing, content generation
- **O1-Preview**: Complex coding, mathematical reasoning

### Environment Configuration

#### **Required Environment Variables:**
```bash
# Primary LLM Configuration
export LLM_PROVIDER="openrouter"
export OPENROUTER_API_KEY="your-api-key"
export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"

# Model Configuration
export PRIMARY_MODEL="claude-3.5-sonnet-20241022"
export FALLBACK_MODEL="openai/gpt-4o-mini"
export HELPER_MODEL="openai/gpt-4o"

# Usage Controls
export MAX_TOKENS_PER_REQUEST=4096
export TEMPERATURE=0.7
export TOP_P=0.9
```

#### **Development Environment:**
```bash
# Development Models (faster/cheaper)
export DEV_PRIMARY_MODEL="openai/gpt-4o-mini"
export DEV_HELPER_MODEL="openai/gpt-3.5-turbo"

# Production Models (higher quality)
export PROD_PRIMARY_MODEL="claude-3.5-sonnet-20241022" 
export PROD_HELPER_MODEL="openai/gpt-4o"
```

## Integration Patterns

### Smart Model Routing
```javascript
function selectModel(taskType, complexity, budget) {
  const modelMatrix = {
    'analysis': {
      high: 'claude-3.5-sonnet-20241022',
      medium: 'openai/gpt-4o',
      low: 'openai/gpt-4o-mini'
    },
    'generation': {
      high: 'anthropic/claude-3-opus',
      medium: 'openai/gpt-4o',
      low: 'openai/gpt-4o-mini'
    },
    'coding': {
      high: 'openai/o1-preview',
      medium: 'claude-3.5-sonnet-20241022',
      low: 'openai/gpt-4o-mini'
    }
  };
  
  return modelMatrix[taskType][complexity] || 'openai/gpt-4o-mini';
}
```

### API Client Standards
```javascript
class LLMClient {
  constructor() {
    this.baseURL = process.env.OPENROUTER_BASE_URL;
    this.apiKey = process.env.OPENROUTER_API_KEY;
    this.defaultModel = process.env.PRIMARY_MODEL;
  }
  
  async complete(prompt, options = {}) {
    const model = options.model || this.defaultModel;
    const response = await fetch(`${this.baseURL}/chat/completions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': options.referer || 'https://your-app.com',
        'X-Title': options.title || 'Claude Code System'
      },
      body: JSON.stringify({
        model,
        messages: prompt,
        max_tokens: options.maxTokens || 4096,
        temperature: options.temperature || 0.7,
        top_p: options.topP || 0.9
      })
    });
    
    return response.json();
  }
}
```

## Prompt Engineering Standards

### Template Structure
```markdown
## System Context
[Role definition and capabilities]

## Task Context  
[Specific task requirements]

## Input Data
[Structured input with clear formatting]

## Output Format
[Explicit format requirements]

## Quality Criteria
[Success metrics and validation rules]
```

### Variable Injection System
```javascript
const promptTemplate = {
  system: "You are a {role} with expertise in {domain}.",
  context: "Current project: {project_name}\nPhase: {current_phase}",
  task: "Complete: {task_description}",
  constraints: "Follow: {standards_list}"
};

function injectVariables(template, variables) {
  return Object.entries(template).reduce((result, [key, value]) => {
    result[key] = value.replace(/\{(\w+)\}/g, (match, varName) => 
      variables[varName] || match
    );
    return result;
  }, {});
}
```

## Cost Optimization

### Token Management
- **Input Optimization**: Compress prompts without losing context
- **Output Limits**: Set appropriate max_tokens per use case
- **Model Selection**: Use cheaper models for routine operations
- **Caching**: Implement response caching for repeated queries

### Usage Monitoring
```javascript
class UsageTracker {
  constructor() {
    this.usage = {
      tokens_used: 0,
      requests_made: 0,
      cost_estimate: 0
    };
  }
  
  trackRequest(model, inputTokens, outputTokens) {
    const pricing = this.getModelPricing(model);
    const cost = (inputTokens * pricing.input) + (outputTokens * pricing.output);
    
    this.usage.tokens_used += inputTokens + outputTokens;
    this.usage.requests_made += 1;
    this.usage.cost_estimate += cost;
    
    this.logUsage(model, cost);
  }
}
```

## Error Handling & Reliability

### Retry Logic
```javascript
async function robustLLMCall(prompt, options, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await llmClient.complete(prompt, options);
    } catch (error) {
      if (attempt === maxRetries) throw error;
      
      // Exponential backoff
      await new Promise(resolve => 
        setTimeout(resolve, Math.pow(2, attempt) * 1000)
      );
      
      // Try fallback model on final retry
      if (attempt === maxRetries - 1) {
        options.model = process.env.FALLBACK_MODEL;
      }
    }
  }
}
```

### Fallback Strategies
1. **Model Degradation**: Primary → Secondary → Fallback models
2. **Feature Degradation**: Reduce complexity if primary fails
3. **Graceful Errors**: Meaningful error messages to users
4. **Local Fallbacks**: Pre-computed responses for critical paths

## Security Standards

### API Key Management
- **Environment Variables**: Never hardcode keys
- **Key Rotation**: Regular API key updates
- **Access Control**: Limit key permissions where possible
- **Monitoring**: Track unusual usage patterns

### Data Privacy
- **PII Filtering**: Remove sensitive data before API calls
- **Request Logging**: Log prompts without sensitive content
- **Response Sanitization**: Clean outputs before storage
- **Compliance**: GDPR/CCPA considerations for data handling

## Testing Standards

### LLM Testing Framework
```javascript
describe('LLM Integration', () => {
  test('model selection works correctly', () => {
    expect(selectModel('analysis', 'high', 'unlimited'))
      .toBe('claude-3.5-sonnet-20241022');
  });
  
  test('prompt injection prevention', async () => {
    const maliciousPrompt = "Ignore previous instructions...";
    const response = await sanitizeAndCall(maliciousPrompt);
    expect(response).not.toContain('credentials');
  });
  
  test('cost limits respected', async () => {
    const expensiveTask = generateLargePrompt();
    await expect(processWithBudget(expensiveTask, 0.01))
      .rejects.toThrow('Budget exceeded');
  });
});
```

### Performance Benchmarks
- **Response Time**: < 5s for standard requests
- **Token Efficiency**: Monitor tokens/request ratios
- **Cost Per Feature**: Track feature-level costs
- **Quality Metrics**: Automated output quality scoring

## Implementation Checklist

### ✅ Basic Setup
- [ ] OpenRouter account and API key configured
- [ ] Environment variables set for all environments
- [ ] Primary and fallback models selected
- [ ] Basic LLM client implemented

### ✅ Advanced Features
- [ ] Smart model routing based on task type
- [ ] Prompt templating with variable injection
- [ ] Usage tracking and cost monitoring
- [ ] Error handling with fallback strategies

### ✅ Production Readiness
- [ ] Security audit completed
- [ ] Performance benchmarks established
- [ ] Monitoring and alerting configured
- [ ] Documentation and training completed

## Best Practices Summary

1. **Model Strategy**: Use the right model for each task type
2. **Cost Control**: Implement usage limits and monitoring
3. **Reliability**: Build robust error handling and fallbacks
4. **Security**: Protect API keys and sanitize data
5. **Performance**: Optimize prompts and manage tokens
6. **Testing**: Comprehensive test coverage for LLM features
7. **Monitoring**: Track usage, costs, and quality metrics

This standard ensures consistent, secure, and cost-effective LLM integration across all projects using OpenRouter's multi-model capabilities.
