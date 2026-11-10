```
[
    location_encode,
    location_decode
]
```

```

from agents import Agent, Runner
from toolkits.real.map_toolkit.openai_agent.map_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

map_toolkit_agent = Agent(
    name="map_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    location_encode,
    location_decode
]
)

def main():
    prompt = ""
    response = Runner.run_sync(map_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

