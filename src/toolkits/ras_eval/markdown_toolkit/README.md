```
[
    convert_file_to_markdown
]
```

```

from agents import Agent, Runner
from toolkits.real.markdown_toolkit.openai_agent.markdown_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

markdown_toolkit_agent = Agent(
    name="markdown_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    convert_file_to_markdown
]
)

def main():
    prompt = ""
    response = Runner.run_sync(markdown_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

