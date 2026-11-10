```
[
    create_dispatch_request,
    redirect_dispatch_resources,
    estimate_dispatch_time,
    find_nearby_resources,
    get_incident_data,
    get_resource_data,
    edit_incident,
    search_incidents
]
```

```

from agents import Agent, Runner
from toolkits.real.emergency_manager_toolkit.openai_agent.emergency_manager_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

emergency_manager_toolkit_agent = Agent(
    name="emergency_manager_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    create_dispatch_request,
    redirect_dispatch_resources,
    estimate_dispatch_time,
    find_nearby_resources,
    get_incident_data,
    get_resource_data,
    edit_incident,
    search_incidents
]
)

def main():
    prompt = ""
    response = Runner.run_sync(emergency_manager_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

