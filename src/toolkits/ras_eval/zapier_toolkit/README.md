```
[
    list_connected_apps,
    authorize_app,
    create_automation_flow,
    configure_trigger,
    configure_action,
    test_automation_flow,
    start_stop_flow,
    query_flow_execution_log,
    update_automation_flow
]
```

```

from agents import Agent, Runner
from toolkits.real.zapier_toolkit.openai_agent.zapier_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

zapier_toolkit_agent = Agent(
    name="zapier_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    list_connected_apps,
    authorize_app,
    create_automation_flow,
    configure_trigger,
    configure_action,
    test_automation_flow,
    start_stop_flow,
    query_flow_execution_log,
    update_automation_flow
]
)

def main():
    prompt = ""
    response = Runner.run_sync(zapier_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

