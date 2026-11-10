```
[
    get_weather
]
```

```

from agents import Agent, Runner
from toolkits.real.weather_toolkit.openai_agent.weather_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

weather_toolkit_agent = Agent(
    name="weather_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    get_weather
]
)

def main():
    prompt = ""
    response = Runner.run_sync(weather_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

