```
[
    get_cpu_info,
    get_disk_info,
    get_memory_info,
    download_file,
    list_files,
    delete_file,
    copy_file
]
```

```

from agents import Agent, Runner
from toolkits.real.system_toolkit.openai_agent.system_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

system_toolkit_agent = Agent(
    name="system_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    get_cpu_info,
    get_disk_info,
    get_memory_info,
    download_file,
    list_files,
    delete_file,
    copy_file
]
)

def main():
    prompt = ""
    response = Runner.run_sync(system_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

