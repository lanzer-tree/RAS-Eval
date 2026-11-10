```
[
    SearchConnectedServices,
    SearchTriggers,
    SearchActions,
    CreateApplet,
    SearchApplets,
    UpdateApplet,
    DeleteApplets
]
```

```

from agents import Agent, Runner
from toolkits.real.ifttt_toolkit.openai_agent.ifttt_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

ifttt_toolkit_agent = Agent(
    name="ifttt_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    SearchConnectedServices,
    SearchTriggers,
    SearchActions,
    CreateApplet,
    SearchApplets,
    UpdateApplet,
    DeleteApplets
]
)

def main():
    prompt = ""
    response = Runner.run_sync(ifttt_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

