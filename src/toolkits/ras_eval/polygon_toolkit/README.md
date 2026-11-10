```
[
    get_aggs,
    list_aggs,
    get_grouped_daily_aggs,
    get_daily_open_close_agg,
    get_previous_close_agg
]
```

```

from agents import Agent, Runner
from toolkits.real.polygon_toolkit.openai_agent.polygon_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

polygon_toolkit_agent = Agent(
    name="polygon_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    get_aggs,
    list_aggs,
    get_grouped_daily_aggs,
    get_daily_open_close_agg,
    get_previous_close_agg
]
)

def main():
    prompt = ""
    response = Runner.run_sync(polygon_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

