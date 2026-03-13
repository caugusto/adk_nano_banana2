# 📘 Google ADK Artifacts & Gemini Enterprise Integration Guide

This guide outlines essential rules and safe patterns discovered for reading, saving, and displaying file **Artifacts** correctly when integrating Google Agent Development Kit (ADK) agents with **Gemini Enterprise**.

---

## 🚨 1. Strict Argument Naming Rule
When defining custom tools that interact with the live orchestrator (Canvas or reference documents), you **MUST** name your context parameter **`tool_context`** exactly.

```python
# ❌ INCORRECT - Will bypass injection and result in None or String
async def my_tool(filename: str, context=None):
    pass

# ✅ CORRECT - ADK matches 'tool_context' to inject the Context structure
async def my_tool(filename: str, tool_context=None, **kwargs):
    pass
```
* **Why**: ADK's `FunctionTool.run_async()` looks strictly for `'tool_context' in valid_params` to decide whether to inject the `Context` object structure into your function call.

---

## 🖼️ 2. Safe Image-to-Image Multimodal Handling
When building tools to **alter or edit** uploaded images (inpainting, Color changes), you must include the original image layout in full modal list inputs to prevent "Style Drift".

### ❌ Simple Prompt Approach (Causes Style Drift)
Just passing a synthesized prompt makes the model generate a **brand new illustration** from scratch instead of modifying the old one.

### ✅ Multimodal Context Approach
Load the reference artifact first and feed it into the multimodal input stack alongside the text instructions:

```python
async def generate_image_tool(prompt: str, reference_images: list[str] = None, tool_context=None, **kwargs):
    parts = []
    
    # Load original Canvas layout bytes first
    if reference_images and tool_context:
        for img_name in reference_images:
            artifact = await tool_context.load_artifact(img_name)
            if hasattr(artifact, 'inline_data'):
                parts.append(artifact)  # Append original Multimodal Part
                
    # Append edit command
    parts.append(types.Part.from_text(text=prompt))
    
    # Pass complete MULTIMODAL content to generate_content
    response = client.models.generate_content(
         model='gemini-3.1-flash-image-preview',
         contents=[types.Content(role="user", parts=parts)],
         config=config
    )
```

---

## 💾 3. Safe `save_artifact` Awaitable Rule
When saving media back into Gemini Enterprise view panes, do not rely on `asyncio.iscoroutinefunction(tool_context.save_artifact)`. Some framework decorators mask wrappers.

**Always use `inspect.isawaitable()` diagnostics:**

```python
import inspect

res = tool_context.save_artifact(filename="output.png", artifact=blob_part)

if inspect.isawaitable(res):
     # Safely await if the method wraps futures/async lock buffers
     res = await res
```

---

## 🛠️ 4. Listing Artifacts Loop Prevention
If your model starts endlessly calling custom definitions trying to "Locate files" inside deployment workspaces, include ADK's native lookup pathway into yours instead of supplying hardcoded returns:

```python
from google.adk.tools.load_artifacts_tool import load_artifacts_tool

root_agent = Agent(
    model='gemini-3.1-flash-lite-preview',
    # Provides full system lookup components supported natively on Reasoning Engine
    tools=[load_artifacts_tool, generate_image_tool], 
)
```
