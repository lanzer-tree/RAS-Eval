```
[
    search_merchants,
    get_merchant_detail,
    search_takeaway_products,
    get_product_detail,
    create_order,
    get_order_status,
    modify_order,
    cancel_order,
    get_order_history
]
```

```

from agents import Agent, Runner
from toolkits.real.take_away_toolkit.openai_agent.take_away_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

take_away_toolkit_agent = Agent(
    name="take_away_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    search_merchants,
    get_merchant_detail,
    search_takeaway_products,
    get_product_detail,
    create_order,
    get_order_status,
    modify_order,
    cancel_order,
    get_order_history
]
)

def main():
    prompt = ""
    response = Runner.run_sync(take_away_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

