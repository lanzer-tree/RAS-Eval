```
[
    QueryClassroom,
    BorrowClassroom,
    GetClassroomSchedule,
    CheckSelfStudyClassroom,
    ReportClassroomRepair
]
```

```

from agents import Agent, Runner
from toolkits.real.classroom_toolkit.openai_agent.classroom_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

classroom_toolkit_agent = Agent(
    name="classroom_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    QueryClassroom,
    BorrowClassroom,
    GetClassroomSchedule,
    CheckSelfStudyClassroom,
    ReportClassroomRepair
]
)

def main():
    prompt = ""
    response = Runner.run_sync(classroom_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

