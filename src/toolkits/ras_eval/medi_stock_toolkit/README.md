```
[
    query_material_stock,
    add_material_warehousing,
    create_purchase_application,
    approve_purchase_order,
    update_material_stock,
    initiate_material_transfer,
    query_material_flow,
    set_material_alert,
    query_supplier_qualification
]
```

```

from agents import Agent, Runner
from toolkits.real.medi_stock_toolkit.openai_agent.medi_stock_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

medi_stock_toolkit_agent = Agent(
    name="medi_stock_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    query_material_stock,
    add_material_warehousing,
    create_purchase_application,
    approve_purchase_order,
    update_material_stock,
    initiate_material_transfer,
    query_material_flow,
    set_material_alert,
    query_supplier_qualification
]
)

def main():
    prompt = ""
    response = Runner.run_sync(medi_stock_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

