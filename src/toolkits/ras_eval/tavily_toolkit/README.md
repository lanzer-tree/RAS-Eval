```
[
    tavily_search
]
```

```

from agents import Agent, Runner
from toolkits.real.tavily_toolkit.openai_agent.tavily_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

tavily_toolkit_agent = Agent(
    name="tavily_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    tavily_search
]
)

def main():
    prompt = ""
    response = Runner.run_sync(tavily_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

