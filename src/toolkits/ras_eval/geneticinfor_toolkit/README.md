```
[
    get_genetic_data,
    get_health_recommendations,
    get_genetic_insights,
    set_data_privacy,
    list_third_party_apps,
    share_data,
    download_data,
    update_data,
    delete_genetic_data
]
```

```

from agents import Agent, Runner
from toolkits.real.geneticinfor_toolkit.openai_agent.geneticinfor_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

geneticinfor_toolkit_agent = Agent(
    name="geneticinfor_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    get_genetic_data,
    get_health_recommendations,
    get_genetic_insights,
    set_data_privacy,
    list_third_party_apps,
    share_data,
    download_data,
    update_data,
    delete_genetic_data
]
)

def main():
    prompt = ""
    response = Runner.run_sync(geneticinfor_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

