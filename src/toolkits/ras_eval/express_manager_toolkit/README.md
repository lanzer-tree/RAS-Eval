```
[
    GetQuote,
    CreateShipmentLabel,
    GetShipmentDetails,
    ManageShipment,
    SearchShipment,
    SearchSavedAddresses,
    search_express_products,
    search_express_orders,
    get_express_order_details
]
```

```

from agents import Agent, Runner
from toolkits.real.express_manager_toolkit.openai_agent.express_manager_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

express_manager_toolkit_agent = Agent(
    name="express_manager_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    GetQuote,
    CreateShipmentLabel,
    GetShipmentDetails,
    ManageShipment,
    SearchShipment,
    SearchSavedAddresses,
    search_express_products,
    search_express_orders,
    get_express_order_details
]
)

def main():
    prompt = ""
    response = Runner.run_sync(express_manager_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

