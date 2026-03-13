import sys
import inspect
import asyncio
from google.genai import types

async def load_reference_image(img_name: str, tool_context) -> types.Part | None:
    """Safely loads a reference image artifact mapped inside Gemini Enterprise.
    
    Args:
        img_name: Filename of the uploaded image.
        tool_context: The ADK ToolContext injected by the orchestrator.
        
    Returns:
        A google.genai.types.Part object with inline_data, or None.
    """
    if not tool_context:
         print("Artifact Helper: tool_context is None", file=sys.stderr)
         return None
         
    try:
         if hasattr(tool_context, 'load_artifact'):
              # Safe async/sync hybrid invocation 
              if asyncio.iscoroutinefunction(tool_context.load_artifact):
                   artifact = await tool_context.load_artifact(img_name)
              else:
                   artifact = tool_context.load_artifact(img_name)
                   
              if hasattr(artifact, 'inline_data') and artifact.inline_data:
                   return artifact
              elif hasattr(artifact, 'text'):
                   print(f"Artifact Helper: {img_name} is text content, skipping image read.", file=sys.stderr)
                   
         print(f"Artifact Helper: tool_context missing load_artifact method", file=sys.stderr)
         return None
         
    except Exception as e:
         print(f"Artifact Helper: Error loading {img_name}: {str(e)}", file=sys.stderr)
         return None


async def save_image_artifact(filename: str, image_bytes: bytes, tool_context) -> bool:
    """Safely saves image bytes as an artifact rendering in Gemini Enterprise.
    
    Args:
        filename: Name to save the file as (e.g. 'generated.png').
        image_bytes: Raw PNG/JPEG byte stream data.
        tool_context: The ADK ToolContext injected by the orchestrator.
        
    Returns:
        True if save succeeded, False otherwise.
    """
    if not tool_context or not hasattr(tool_context, 'save_artifact'):
         print("Artifact Helper: tool_context missing save_artifact capabilities", file=sys.stderr)
         return False
         
    try:
         blob_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
         
         # Safe inspect.isawaitable buffer guards for descriptor decorators
         res = tool_context.save_artifact(filename=filename, artifact=blob_part)
         
         if inspect.isawaitable(res):
              await res
              
         sys.stderr.flush()
         return True
         
    except Exception as e:
         print(f"Artifact Helper: Error saving {filename}: {str(e)}", file=sys.stderr)
         sys.stderr.flush()
         return False
