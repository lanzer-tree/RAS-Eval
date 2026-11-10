```
[
    search_products,
    get_product_details,
    create_product,
    update_product,
    delete_product,
    search_orders,
    get_order_details,
    draft_order,
    manage_order,
    search_customers,
    get_store_analytics
]
```

```

from agents import Agent, Runner
from toolkits.real.shopify_toolkit.openai_agent.shopify_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

shopify_toolkit_agent = Agent(
    name="shopify_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    search_products,
    get_product_details,
    create_product,
    update_product,
    delete_product,
    search_orders,
    get_order_details,
    draft_order,
    manage_order,
    search_customers,
    get_store_analytics
]
)

def main():
    prompt = ""
    response = Runner.run_sync(shopify_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

