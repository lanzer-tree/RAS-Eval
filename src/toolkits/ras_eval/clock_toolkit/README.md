```
[
    set_alarm,
    cancel_alarm,
    get_current_time,
    timer,
    clear_alarms
]
```

```

from agents import Agent, Runner
from toolkits.real.clock_toolkit.openai_agent.clock_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

clock_toolkit_agent = Agent(
    name="clock_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    set_alarm,
    cancel_alarm,
    get_current_time,
    timer,
    clear_alarms
]
)

def main():
    prompt = ""
    response = Runner.run_sync(clock_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

