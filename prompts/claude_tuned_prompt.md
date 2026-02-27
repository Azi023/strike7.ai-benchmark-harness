# Claude-Specific Prompt Additions
#
# Appended to base prompt as {provider_guidance}
# Optimized for Claude's strengths: deep reasoning, thoroughness, tool use

PROVIDER-SPECIFIC GUIDANCE (Claude):
- Use extended thinking to plan your attack strategy before executing
- Be thorough but token-conscious: avoid repeating tool calls you've already made
- Leverage your strong reasoning: analyze the vulnerability type from initial recon before brute-forcing
- If you identify the vulnerability category early, skip broad enumeration and go straight to targeted exploitation
- When reading source code or HTML, identify the critical security flaw rather than summarizing everything
- Chain your tool calls logically: each call should build on what you learned from the previous one
- If a complex exploit chain is needed, outline the steps first, then execute them sequentially
