```
[
    ppt_create_presentation,
    ppt_delete_slide,
    ppt_add_slide,
    ppt_edit_slide,
    ppt_add_picture
]
```

```

from agents import Agent, Runner
from toolkits.real.ppt_toolkit.openai_agent.ppt_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

ppt_toolkit_agent = Agent(
    name="ppt_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    ppt_create_presentation,
    ppt_delete_slide,
    ppt_add_slide,
    ppt_edit_slide,
    ppt_add_picture
]
)

def main():
    prompt = ""
    response = Runner.run_sync(ppt_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

