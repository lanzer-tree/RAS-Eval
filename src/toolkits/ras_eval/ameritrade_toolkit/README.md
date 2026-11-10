```
[
    GetHoldingsInformation,
    GetBalance,
    GetStockInformation,
    TradeStock
]
```

```

from agents import Agent, Runner
from toolkits.real.ameritrade_toolkit.openai_agent.ameritrade_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

ameritrade_toolkit_agent = Agent(
    name="ameritrade_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    GetHoldingsInformation,
    GetBalance,
    GetStockInformation,
    TradeStock
]
)

def main():
    prompt = ""
    response = Runner.run_sync(ameritrade_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

