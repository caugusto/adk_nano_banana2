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

import vertexai
from vertexai import agent_engines

def test_live():
    # Initialize Vertex AI with target workspace project
    vertexai.init(project=os.environ.get("GOOGLE_CLOUD_PROJECT"), location="us-central1")
    
    agent_engine_id = "9116920619588386816"  # Update with your Agent ID from deployment output

    print(f"Loading deployed agent: {agent_engine_id} ...")
    
    try:
         agent_engine = agent_engines.get(
              f"projects/{os.environ.get('GOOGLE_CLOUD_PROJECT')}/locations/us-central1/reasoningEngines/{agent_engine_id}"
         )
         
         print("Agent retrieved successfully.")
         print(f"Display Name: {agent_engine.display_name}")
         print(f"Resource Name: {agent_engine.resource_name}")
         print(f"Creation Time: {agent_engine.create_time}")
         print("\nAgent is active and serving.")
         return

         
    except Exception as e:
         print(f"Error calling live agent: {e}")

if __name__ == "__main__":
    test_live()
