```
[
    find_device_id,
    get_device_status,
    set_device_state,
    add_schedule_action,
    delete_schedule_action,
    list_scheduled_actions
]
```

```

from agents import Agent, Runner
from toolkits.real.smarthome_toolkit.openai_agent.smarthome_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

smarthome_toolkit_agent = Agent(
    name="smarthome_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    find_device_id,
    get_device_status,
    set_device_state,
    add_schedule_action,
    delete_schedule_action,
    list_scheduled_actions
]
)

def main():
    prompt = ""
    response = Runner.run_sync(smarthome_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

