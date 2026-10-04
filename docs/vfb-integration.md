# VFB Integration

VFB supports an educational circuit-tracing overlay only. The analogy is: user input resembles sensory input, model reasoning resembles processing, tool calls resemble outputs, and approval gates resemble inhibition. VFB data is not used to detect, score, or block attacks.

The client must use VFB's published MCP/API endpoint behind a timeout and feature flag. It must display source attribution and gracefully fall back to the local explanation when unavailable.
