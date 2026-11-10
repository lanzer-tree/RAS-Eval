```
[
    SearchPeople,
    GetPersonDetails,
    BackgroundCheck,
    VerifyIdentity,
    MonitorDataChanges,
    GetHistoricalData,
    AccessCourtRecords,
    GetCriminalHistory,
    ReversePhoneLookup,
    DownloadPublicRecord
]
```

```

from agents import Agent, Runner
from toolkits.real.spokeo_toolkit.openai_agent.spokeo_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

spokeo_toolkit_agent = Agent(
    name="spokeo_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    SearchPeople,
    GetPersonDetails,
    BackgroundCheck,
    VerifyIdentity,
    MonitorDataChanges,
    GetHistoricalData,
    AccessCourtRecords,
    GetCriminalHistory,
    ReversePhoneLookup,
    DownloadPublicRecord
]
)

def main():
    prompt = ""
    response = Runner.run_sync(spokeo_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

