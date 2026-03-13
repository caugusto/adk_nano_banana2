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
from vertexai import agent_engines

sys.path.append(os.path.dirname(__file__))
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# --- Force API Endpoint globally for Vertex AI ---
# If VertexAI init is picking up a regional Endpoint for the SDK itself,
# we need to redirect the SDK to Vertex-global endpoints
os.environ["VERTEX_AI_API_ENDPOINT"] = "us-central1-aiplatform.googleapis.com" # Internal endpoint mapping usually handles this

DEPLOYMENT_LOCATION = "us-central1"
GCS_BUCKET = os.environ.get("GCS_BUCKET")

ENV_VARS = {
    "GOOGLE_CLOUD_LOCATION": "global",
    "LOCAL_DEV": "False",
}

AGENT_REQUIREMENTS = [
    "google-cloud-aiplatform[adk,agent_engines]",
    "pandas",
    "pydantic",
    "cloudpickle",
    "google-genai",
]

def deploy_agent():
    vertexai.init(
        project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
        location=DEPLOYMENT_LOCATION,
        staging_bucket=GCS_BUCKET,
    )
    
    import agent
    root_agent = agent.root_agent

    # Update orchestrator model reference to avoid region inference locks
    if hasattr(root_agent, 'model'):
         root_agent.model = 'gemini-3.1-flash-lite-preview'

    agent_display_name = "adk_nano_banana2"

    print(f"Updating deployment of agent '{agent_display_name}'...")
    
    try:
        existing_agents = agent_engines.list()
        target_agent = None
        for a in existing_agents:
            if a.display_name == agent_display_name:
                target_agent = a
                break
                
        if target_agent:
            print(f"Updating agent: {target_agent.name}")
            remote_agent = agent_engines.update(
                target_agent.name,
                agent_engine=root_agent,
                requirements=AGENT_REQUIREMENTS,
                env_vars=ENV_VARS,
                extra_packages=["."],
            )
            print("Update triggered.")
        else:
             print("No agent found. Creating new agent...")
             remote_agent = agent_engines.create(
                 agent_engine=root_agent,
                 requirements=AGENT_REQUIREMENTS,
                 env_vars=ENV_VARS,
                 extra_packages=["."],
                 display_name=agent_display_name,
             )
             print(f"Creation triggered. Agent: {remote_agent.name}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    deploy_agent()
