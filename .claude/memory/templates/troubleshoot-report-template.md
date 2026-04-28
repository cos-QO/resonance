# Troubleshoot Report: {BRIEF_DESCRIPTION}

**TS-ID**: {TS-YYYYMMDD-XXX}
**Date**: {YYYY-MM-DD}
**Invoked by**: {AGENT_NAME}
**Issue**: {ONE_LINE_DESCRIPTION}
**Status**: Complete
**Confidence**: {HIGH/MEDIUM/LOW}
**Investigation Duration**: {X} minutes

---

## Investigation Summary

{BRIEF_OVERVIEW_OF_WHAT_WAS_INVESTIGATED}

**Coordination File**: `/.claude/memory/temp/troubleshoot-{TIMESTAMP}-coordination.md`
**Investigation Method**: 3 parallel instances (error analysis, context, patterns)

---

## Investigation Cost

**Total Tokens Used**: {TOTAL_TOKENS} tokens (across all 3 instances)
**Estimated Cost**: ~${COST} USD (Claude Haiku pricing)
**Cost Comparison**: vs ~${SONNET_COST} USD with Sonnet - **{SAVINGS_PERCENT}% savings**

**Breakdown**:
- Instance 1 (Error Analysis): {INSTANCE_1_TOKENS} tokens (~${INSTANCE_1_COST})
- Instance 2 (Context Investigation): {INSTANCE_2_TOKENS} tokens (~${INSTANCE_2_COST})
- Instance 3 (Pattern Search): {INSTANCE_3_TOKENS} tokens (~${INSTANCE_3_COST})

**Model**: Claude Haiku 4.5 (optimized for cost-effective parallel investigations)

**Example Values** (typical investigation):
```yaml
total_tokens: 85000
haiku_cost: $0.08
sonnet_cost: $0.28
savings: 71%

breakdown:
  instance_1: 28000 tokens (~$0.027)
  instance_2: 30000 tokens (~$0.029)
  instance_3: 27000 tokens (~$0.024)
```

**Cost Efficiency Notes**:
- Haiku provides excellent quality for investigation tasks at 70% lower cost
- Parallel investigation (3 instances) still cheaper than sequential Sonnet
- Cost savings allow more frequent investigations without budget concerns

---

## Root Cause

{CLEAR_SPECIFIC_STATEMENT_OF_ROOT_CAUSE}

### Why This is the Root Cause
- {EVIDENCE_1}
- {EVIDENCE_2}
- {EVIDENCE_3}

### Confidence Assessment
**Level**: {HIGH/MEDIUM/LOW}
**Reasoning**: {WHY_THIS_CONFIDENCE_LEVEL}

---

## Evidence Trail

### Instance 1: Error Analysis
**Focus**: Error messages, stack traces, error patterns
**Duration**: {X} minutes

**Findings**:
- {FINDING_1}
- {FINDING_2}
- {FINDING_3}

**Key Insights**:
{SUMMARY_OF_ERROR_ANALYSIS}

---

### Instance 2: Context Investigation
**Focus**: Code context, git history, environment, data flow
**Duration**: {X} minutes

**Findings**:
- {FINDING_1}
- {FINDING_2}
- {FINDING_3}

**Key Insights**:
{SUMMARY_OF_CONTEXT_FINDINGS}

**Recent Changes**:
- {TIMESTAMP}: {CHANGE_1}
- {TIMESTAMP}: {CHANGE_2}

**Environmental Factors**:
- {FACTOR_1}
- {FACTOR_2}

---

### Instance 3: Pattern Search
**Focus**: Similar errors, code patterns, anti-patterns
**Duration**: {X} minutes

**Findings**:
- {FINDING_1}
- {FINDING_2}
- {FINDING_3}

**Similar Errors Found**: {COUNT} occurrences
**Related Code Patterns**: {DESCRIPTION}
**Anti-Patterns Detected**:
- {ANTI_PATTERN_1}
- {ANTI_PATTERN_2}

---

## Synthesis

### How Findings Converge

{EXPLANATION_OF_HOW_ALL_3_INSTANCES_POINT_TO_SAME_ROOT_CAUSE}

**Evidence Correlation**:
- Instance 1 shows {ERROR_EVIDENCE}
- Instance 2 shows {CONTEXT_EVIDENCE}
- Instance 3 shows {PATTERN_EVIDENCE}
- **Conclusion**: {ROOT_CAUSE_STATEMENT}

### Cross-Instance Insights

{ANY_INSIGHTS_THAT_EMERGED_FROM_INSTANCES_COLLABORATING}

---

## Impact Assessment

**Severity**: {CRITICAL/HIGH/MEDIUM/LOW}
**Affected Areas**:
- {AREA_1}
- {AREA_2}

**User Impact**: {DESCRIPTION}
**Frequency**: {ALWAYS/OFTEN/SOMETIMES/RARE}
**Blast Radius**: {WHAT_ELSE_COULD_BREAK}

---

## Recommended Solutions

### Quick Fix (Immediate)
**What**: {WORKAROUND_DESCRIPTION}
**Where**: {FILE:LINE}
**How**: {IMPLEMENTATION_STEPS}
**Agent Assignment**: {AGENT_NAME}
**Time Estimate**: {X} minutes
**Risk**: {POTENTIAL_SIDE_EFFECTS}
**Limitations**: {WHAT_THIS_DOESNT_SOLVE}

### Permanent Fix (Long-term)
**What**: {ROOT_CAUSE_SOLUTION}
**Where**: {FILES_TO_MODIFY}
**How**: {DETAILED_IMPLEMENTATION}
**Why This Prevents Recurrence**: {EXPLANATION}

**Agent Assignments**:
- **Developer**: {IMPLEMENTATION_TASK}
- **Tester**: {VERIFICATION_TASK}
- **Documenter**: {DOCUMENTATION_TASK}
- **{OTHER_AGENT}**: {TASK_IF_APPLICABLE}

**Time Estimate**: {X} minutes
**Dependencies**: {ANY_BLOCKERS_OR_PREREQUISITES}

---

## Prevention Measures

### Tests to Add
- **Test 1**: {TEST_DESCRIPTION}
  - **Type**: {UNIT/INTEGRATION/E2E}
  - **Purpose**: {WHAT_THIS_CATCHES}
  - **Agent**: Tester

- **Test 2**: {TEST_DESCRIPTION}
  - **Type**: {UNIT/INTEGRATION/E2E}
  - **Purpose**: {WHAT_THIS_CATCHES}
  - **Agent**: Tester

### Monitoring to Implement
- **Metric 1**: {WHAT_TO_MONITOR}
  - **Alert Threshold**: {WHEN_TO_ALERT}
  - **Purpose**: {EARLY_DETECTION}

- **Metric 2**: {WHAT_TO_MONITOR}
  - **Alert Threshold**: {WHEN_TO_ALERT}
  - **Purpose**: {EARLY_DETECTION}

### Documentation Updates
- **What**: {WHAT_TO_DOCUMENT}
- **Where**: {LOCATION}
- **Purpose**: {KNOWLEDGE_SHARING}
- **Agent**: Documenter

### Process Improvements
- **Improvement 1**: {PROCESS_CHANGE}
  - **Why**: {PREVENTS_SIMILAR_ISSUES}
  - **Owner**: {AGENT_OR_ROLE}

- **Improvement 2**: {PROCESS_CHANGE}
  - **Why**: {PREVENTS_SIMILAR_ISSUES}
  - **Owner**: {AGENT_OR_ROLE}

---

## Related Findings

{ANY_ADDITIONAL_ISSUES_DISCOVERED_DURING_INVESTIGATION}

**Related TS-IDs**:
- {TS-ID-1}: {BRIEF_DESCRIPTION}
- {TS-ID-2}: {BRIEF_DESCRIPTION}

---

## References

### Investigation Files
- **Coordination File**: `/.claude/memory/temp/troubleshoot-{TIMESTAMP}-coordination.md`
- **Error Logs**: {LOCATION_IF_APPLICABLE}
- **Related Files**:
  - {FILE_1:LINE_RANGE}
  - {FILE_2:LINE_RANGE}

### Codebase References
- **Entry Point**: {FILE:LINE}
- **Failure Point**: {FILE:LINE}
- **Related Functions**:
  - {FUNCTION_1} in {FILE_1}
  - {FUNCTION_2} in {FILE_2}

### External Resources
- **Documentation**: {LINKS_IF_APPLICABLE}
- **Similar Issues**: {GITHUB_ISSUES_STACKOVERFLOW_ETC}

---

## Timeline

- **{TIMESTAMP}**: Investigation started
- **{TIMESTAMP}**: Instance 1 completed error analysis
- **{TIMESTAMP}**: Instance 2 completed context investigation
- **{TIMESTAMP}**: Instance 3 completed pattern search
- **{TIMESTAMP}**: Synthesis completed
- **{TIMESTAMP}**: Final report generated

---

## Lessons Learned

1. **{LESSON_1}**: {DESCRIPTION}
2. **{LESSON_2}**: {DESCRIPTION}
3. **{LESSON_3}**: {DESCRIPTION}

**Similar Issues to Watch For**:
- {ISSUE_1}
- {ISSUE_2}

---

## Next Steps

**Immediate** (within 1 hour):
- [ ] {QUICK_FIX_TASK}

**Short-term** (within 1 day):
- [ ] {PERMANENT_FIX_TASK}
- [ ] {TEST_TASK}

**Long-term** (within 1 week):
- [ ] {DOCUMENTATION_TASK}
- [ ] {PROCESS_IMPROVEMENT_TASK}

---

**Report Generated**: {TIMESTAMP}
**Generated by**: Troubleshooter
**For**: {INVOKING_AGENT}
**Shared with**: PM, {OTHER_AGENTS}

---

## Template Usage Notes

**When creating a report from this template**:

1. Replace all `{PLACEHOLDER}` values with actual data
2. Remove sections not applicable (e.g., if no related TS-IDs)
3. Add additional sections if needed (e.g., security implications)
4. Ensure all 3 instance findings are documented
5. Include clear agent assignments for all recommendations
6. Assign unique TS-ID following format: TS-YYYYMMDD-XXX
7. Save to `/.claude/memory/reports/troubleshooting/TS-{id}.md`
8. Reference coordination file for full investigation trail
