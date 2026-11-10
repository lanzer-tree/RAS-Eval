```
[
    reset_readassistant_environment,
    search_reading_resource,
    parse_reading_content,
    explain_difficult_content,
    track_reading_progress,
    add_reading_notes,
    query_reading_notes,
    generate_reading_plan,
    recommend_related_resources
]
```

```

from agents import Agent, Runner
from toolkits.real.readassistant_toolkit.openai_agent.readassistant_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

readassistant_toolkit_agent = Agent(
    name="readassistant_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    reset_readassistant_environment,
    search_reading_resource,
    parse_reading_content,
    explain_difficult_content,
    track_reading_progress,
    add_reading_notes,
    query_reading_notes,
    generate_reading_plan,
    recommend_related_resources
]
)

def main():
    prompt = ""
    response = Runner.run_sync(readassistant_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

