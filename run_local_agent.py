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

vertexai.init(project=os.environ.get("GOOGLE_CLOUD_PROJECT"), location="us-central1")

import agent
root_agent = agent.root_agent

async def main():
    print("--- Executing Local Agent `run_async` ---")
    try:
        responses = []
        # Using positional argument or input=
        # Standard ADK signature often uses positionals or kwargs inspection
        async for event in root_agent.run_async("Hi, call test_tool first"):
            print(f"EVENT: {event}")
            responses.append(event)
        
        print("\n--- Final Output ---")
        for r in responses:
             print(r)
             
    except Exception as e:
         import traceback
         traceback.print_exc()
         print(f"Local execution crashed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
