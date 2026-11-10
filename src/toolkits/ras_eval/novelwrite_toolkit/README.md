```
[
    CreateProject,
    SwitchProject,
    ListProjects,
    WriteContent,
    GetContent,
    ImportDocument,
    ExportDocument,
    CheckGrammar,
    CheckSpelling,
    CheckPunctuation,
    OptimizeRedundancy,
    OptimizeStyle,
    ExpandContent,
    ScoreContent,
    GetWritingSuggestions,
    RecordWritingTime,
    GetWritingStatistics,
    CountWords
]
```

```

from agents import Agent, Runner
from toolkits.real.novelwrite_toolkit.openai_agent.novelwrite_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

novelwrite_toolkit_agent = Agent(
    name="novelwrite_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    CreateProject,
    SwitchProject,
    ListProjects,
    WriteContent,
    GetContent,
    ImportDocument,
    ExportDocument,
    CheckGrammar,
    CheckSpelling,
    CheckPunctuation,
    OptimizeRedundancy,
    OptimizeStyle,
    ExpandContent,
    ScoreContent,
    GetWritingSuggestions,
    RecordWritingTime,
    GetWritingStatistics,
    CountWords
]
)

def main():
    prompt = ""
    response = Runner.run_sync(novelwrite_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

