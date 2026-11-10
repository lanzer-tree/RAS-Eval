```
[
    add_clothing,
    remove_clothing,
    suggest_outfit,
    save_outfit,
    get_outfits,
    list_clothing
]
```

```

from agents import Agent, Runner
from toolkits.real.wardrobe_manager_toolkit.openai_agent.wardrobe_manager_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

wardrobe_manager_toolkit_agent = Agent(
    name="wardrobe_manager_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    add_clothing,
    remove_clothing,
    suggest_outfit,
    save_outfit,
    get_outfits,
    list_clothing
]
)

def main():
    prompt = ""
    response = Runner.run_sync(wardrobe_manager_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

