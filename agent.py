import os
import sys

# Load .env file for local development
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip().strip('"').strip("'")

import vertexai
from google import genai
from google.genai import types
from google.adk.agents.llm_agent import Agent

# Initialize Vertex AI for local evaluation support (CLI)
if os.environ.get("LOCAL_DEV") != "False":
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"
    PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
    LOCATION = os.environ.get("MODEL_LOCATION", os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"))
    
    if not PROJECT_ID:
        print("ERROR: GOOGLE_CLOUD_PROJECT environment variable not set.", file=sys.stderr)
        print("Please set it in your environment or create a .env file.", file=sys.stderr)
        sys.exit(1)
        
    print(f"DEBUG: Initializing Vertex AI with project={PROJECT_ID}, location={LOCATION}", file=sys.stderr)
    vertexai.init(project=PROJECT_ID, location=LOCATION)

# Setup Load Artifacts tool

from google.adk.tools.load_artifacts_tool import load_artifacts_tool

# Define tools directly in the file for single-module stability

def test_tool(**kwargs) -> str:
    """A simple test tool to verify if tools execute at all."""
    print("--- DEBUG TOOL: test_tool triggered ---", file=sys.stderr)
    return "Test Tool executed successfully!"

async def read_reference_file(filename: str, tool_context=None, **kwargs) -> str:
    """Reads uploaded reference file."""
    print(f"--- DEBUG TOOL START: read_reference_file({filename}) ---", file=sys.stderr)
    if tool_context:
         print(f"DEBUG TOOL: tool_context type is {type(tool_context)}", file=sys.stderr)
    else:
         print("DEBUG TOOL: tool_context is None", file=sys.stderr)
         return "Error: Context not provided to tool."
    
    try:
         if hasattr(tool_context, 'load_artifact'):
              print(f"DEBUG TOOL: Calling load_artifact for {filename}", file=sys.stderr)
              if asyncio.iscoroutinefunction(tool_context.load_artifact):
                   artifact = await tool_context.load_artifact(filename)
              else:
                   artifact = tool_context.load_artifact(filename)
              return artifact.text if hasattr(artifact, 'text') else str(artifact)
         print("DEBUG TOOL: tool_context has no load_artifact attribute", file=sys.stderr)
         return f"Context {type(tool_context)} has no load_artifact."
    except Exception as e:
          return f"Error reading {filename}: {str(e)}"

async def generate_image_tool(prompt: str, reference_images: list[str] = None, tool_context=None, **kwargs) -> dict:
    """Generates image and saves it as an artifact for rendering."""
    print(f"--- DEBUG TOOL START: generate_image_tool ---", file=sys.stderr)
    print(f"DEBUG TOOL: Prompt='{prompt[:50]}...'", file=sys.stderr)
    print(f"DEBUG TOOL: reference_images={reference_images}", file=sys.stderr)
    
    if tool_context:
         print(f"DEBUG TOOL: tool_context type is {type(tool_context)}", file=sys.stderr)
    else:
         print("DEBUG TOOL: tool_context is None", file=sys.stderr)
         
    client = genai.Client(vertexai=True)
    parts = []
    
    # LOAD REFERENCE IMAGES IF PROVIDED
    if reference_images and tool_context:
         for img_name in reference_images:
              try:
                   print(f"DEBUG TOOL: Loading reference image {img_name}", file=sys.stderr)
                   import asyncio
                   if asyncio.iscoroutinefunction(tool_context.load_artifact):
                        artifact = await tool_context.load_artifact(img_name)
                   else:
                        artifact = tool_context.load_artifact(img_name)
                        
                   print(f"DEBUG TOOL: Loaded {img_name} type {type(artifact)}", file=sys.stderr)
                   
                   # Append the artifact directly if it's already a Part or Part-like
                   if hasattr(artifact, 'inline_data') and artifact.inline_data:
                        print(f"DEBUG TOOL: Appending Part inline_data length {len(artifact.inline_data.data)}", file=sys.stderr)
                        parts.append(artifact)
                   elif hasattr(artifact, 'text') and artifact.text:
                        print("DEBUG TOOL: Artifact is text, skipping image append.", file=sys.stderr)
                   else:
                        # Fallback try to read bytes if it's a file wrapper
                        if hasattr(artifact, 'read'):
                             data = artifact.read()
                             parts.append(types.Part.from_bytes(data=data, mime_type="image/png"))
                             
              except Exception as e:
                    print(f"DEBUG TOOL: Error loading reference {img_name}: {str(e)}", file=sys.stderr)

    # Append the prompt text
    parts.append(types.Part.from_text(text=prompt))
    
    contents = [
        types.Content(
            role="user",
            parts=parts
        )
    ]
    
    try:
         print("DEBUG TOOL: Triggering generate_content for image...", file=sys.stderr)
         config = types.GenerateContentConfig(
             response_modalities=["IMAGE"],
             image_config=types.ImageConfig(
                 aspect_ratio="1:1",
                 image_size="1K",
                 output_mime_type="image/png",
             )
         )
         
         response = client.models.generate_content(
             model='gemini-3.1-flash-image-preview',
             contents=contents,
             config=config
         )
         print("DEBUG TOOL: generate_content call succeeded.", file=sys.stderr)
         
         candidate = response.candidates[0]
         img_part = None
         for part in candidate.content.parts:
              if hasattr(part, 'inline_data') and part.inline_data:
                   img_part = part
                   break
                   
         if not img_part:
              return {"status": "error", "error": "No image data in response candidate."}
              
         image_bytes = img_part.inline_data.data
         
         if tool_context and hasattr(tool_context, 'save_artifact'):
              print("DEBUG TOOL: Saving artifact generated_image.png ...", file=sys.stderr)
              blob_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
              
              import inspect
              res = tool_context.save_artifact(filename="generated_image.png", artifact=blob_part)
              
              if inspect.isawaitable(res):
                   print("DEBUG TOOL: save_artifact returned awaitable, awaiting...", file=sys.stderr)
                   res = await res
                   
              print(f"DEBUG TOOL: Artifact saved successfully. Res: {res}", file=sys.stderr)
              sys.stderr.flush()
              
              return {
                  "status": "success", 
                  "message": "Image generated and saved as artifact.",
                  "artifact_name": "generated_image.png"
              }
              
         print("DEBUG TOOL: tool_context has no save_artifact method.", file=sys.stderr)
         return {"status": "error", "error": "Unable to save artifact context missing."}
         
    except Exception as e:
         print(f"DEBUG TOOL: generate_content call failed: {str(e)}", file=sys.stderr)
         sys.stderr.flush()
         return {"status": "error", "error": str(e)}

# Setup Agent

root_agent = Agent(
    model='gemini-3.1-flash-lite-preview',
    name='image_generator_orchestrator',
    description="An agent that orchestrates reading reference files and generating images.",
    instruction=(
         "You are an expert image generation assistant. "
         "Your goal is to generate an image based on the user's prompt and any uploaded reference files. "
         "0. **Call `test_tool` first** to confirm that functions can trigger on this container. "
         "1. **Identify References**: Look for uploaded files (e.g., CSV, text, images) or **previously generated images** from the session history (e.g., `generated_image.png`). "
         "2. **Read Content**: If there are text or CSV files mentioned, use `read_reference_file` to understand their content. "
         "3. **Synthesize Prompt**: Combine the user's prompt and any reference context into a detailed descriptive prompt for image generation. "
         "4. **Recursive Editing**: If the user is asking to modify, update, or iterate on a previously generated image, include `generated_image.png` in the list of reference images. Synthesize a prompt that describes the desired change relative to the previous context to help maintain consistency. "
         "5. **Identify Images**: For new uploads, identify their filenames as style or content references. "
         "6. Call `generate_image_tool` with your synthesized prompt and the list of reference image filenames. "
         "7. Inform the user that the image has been generated."
    ),
    tools=[load_artifacts_tool, test_tool, read_reference_file, generate_image_tool],
)

# Local ADK CLI Support: Wrap into App to bypass folder hyphen naming locks
if os.environ.get("LOCAL_DEV") != "False":
    try:
         from google.adk.apps.app import App
         app = App(name="adk_nano_banana2", root_agent=root_agent)
         print("DEBUG: Wrapped root_agent in App for local CLI modes.", file=sys.stderr)
    except ImportError:
         pass
