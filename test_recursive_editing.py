import asyncio
import os
# Load .env file for local development
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip().strip('"').strip("'")

import sys
import vertexai

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Re-init Vertex AI with target workspace project
vertexai.init(project=os.environ.get("GOOGLE_CLOUD_PROJECT"), location="us-central1")

import agent
root_agent = agent.root_agent

async def main():
    print("--- 🧪 Turn 1: Initial Image Generation 🧪 ---")
    responses1 = []
    # Using a string first
    try:
        async for event in root_agent.run_async("Generate a realistic photo of a baby playing with a toy T-Rex in a green park."):
             print(f"EVENT 1: {event}")
             responses1.append(event)
    except Exception as e:
         import traceback
         traceback.print_exc()
         print(f"Turn 1 crashed: {e}")
         return

    print("\n--- 🧪 Turn 2: Recursive Editing 🧪 ---")
    responses2 = []
    try:
        # In a real session, history is appended. If run_async is stateless,
        # it won't see history. Let's see if we can pass a list of Content nodes
        # or if Agent supports a session object.
        # For simulation, we can see if it picks up `generated_image.png` if it exists on disk.
        # But instructions rely on Orchestrator identifying it from "session history".
        # If run_async is stateful, this second call should work.
        async for event in root_agent.run_async("Now turn this into a cartoon, maintaining the pose."):
             print(f"EVENT 2: {event}")
             responses2.append(event)
             
    except Exception as e:
         print(f"Turn 2 crashed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
