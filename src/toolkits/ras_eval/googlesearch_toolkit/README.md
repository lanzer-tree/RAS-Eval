```
[
    web_search,
    image_search,
    video_search,
    news_search,
    get_search_trends,
    get_search_history
]
```

```

from agents import Agent, Runner
from toolkits.real.googlesearch_toolkit.openai_agent.googlesearch_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

googlesearch_toolkit_agent = Agent(
    name="googlesearch_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    web_search,
    image_search,
    video_search,
    news_search,
    get_search_trends,
    get_search_history
]
)

def main():
    prompt = ""
    response = Runner.run_sync(googlesearch_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

