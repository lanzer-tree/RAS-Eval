```
[
    search_design_templates,
    init_design_project,
    fetch_design_assets,
    edit_design_elements,
    batch_generate_designs,
    adjust_design_layout,
    preview_design_project,
    export_design_files,
    share_design_project
]
```

```

from agents import Agent, Runner
from toolkits.real.canva_toolkit.openai_agent.canva_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

canva_toolkit_agent = Agent(
    name="canva_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    search_design_templates,
    init_design_project,
    fetch_design_assets,
    edit_design_elements,
    batch_generate_designs,
    adjust_design_layout,
    preview_design_project,
    export_design_files,
    share_design_project
]
)

def main():
    prompt = ""
    response = Runner.run_sync(canva_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

