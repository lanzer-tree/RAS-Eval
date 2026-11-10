```
[
    CreateNote,
    ReadNote,
    UpdateNote,
    DeleteNote,
    CreateNotebook,
    ReadNotebook,
    UpdateNotebook,
    DeleteNotebook,
    SearchNotes,
    ManageNoteSharingLevel,
    SearchNotebooks
]
```

```

from agents import Agent, Runner
from toolkits.real.evernote_manager_toolkit.openai_agent.evernote_manager_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

evernote_manager_toolkit_agent = Agent(
    name="evernote_manager_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    CreateNote,
    ReadNote,
    UpdateNote,
    DeleteNote,
    CreateNotebook,
    ReadNotebook,
    UpdateNotebook,
    DeleteNotebook,
    SearchNotes,
    ManageNoteSharingLevel,
    SearchNotebooks
]
)

def main():
    prompt = ""
    response = Runner.run_sync(evernote_manager_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

