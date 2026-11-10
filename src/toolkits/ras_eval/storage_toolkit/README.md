```
[
    AddItem,
    UpdateItem,
    DeleteItem,
    SearchItems,
    GetItemDetails,
    TrackInventory,
    SetupAlert,
    SearchSuppliers,
    ListCategories
]
```

```

from agents import Agent, Runner
from toolkits.real.storage_toolkit.openai_agent.storage_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

storage_toolkit_agent = Agent(
    name="storage_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    AddItem,
    UpdateItem,
    DeleteItem,
    SearchItems,
    GetItemDetails,
    TrackInventory,
    SetupAlert,
    SearchSuppliers,
    ListCategories
]
)

def main():
    prompt = ""
    response = Runner.run_sync(storage_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

