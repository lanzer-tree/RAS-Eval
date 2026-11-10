```
[
    UploadFile,
    DownloadFile,
    ListFilesAndFolders,
    CreateFolder,
    ShareItem,
    DeleteDropboxItem,
    SearchDropboxItems,
    GetItemMetadata
]
```

```

from agents import Agent, Runner
from toolkits.real.dropbox_toolkit.openai_agent.dropbox_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

dropbox_toolkit_agent = Agent(
    name="dropbox_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    UploadFile,
    DownloadFile,
    ListFilesAndFolders,
    CreateFolder,
    ShareItem,
    DeleteDropboxItem,
    SearchDropboxItems,
    GetItemMetadata
]
)

def main():
    prompt = ""
    response = Runner.run_sync(dropbox_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

