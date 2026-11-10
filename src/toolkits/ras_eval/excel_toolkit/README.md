```
[
    excel_create_workbook,
    excel_add_sheet,
    excel_delete_sheet,
    excel_write_cell,
    excel_read_cell,
    excel_format_cell,
    excel_read_sheet,
    excel_list_sheets
]
```

```

from agents import Agent, Runner
from toolkits.real.excel_toolkit.openai_agent.excel_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

excel_toolkit_agent = Agent(
    name="excel_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    excel_create_workbook,
    excel_add_sheet,
    excel_delete_sheet,
    excel_write_cell,
    excel_read_cell,
    excel_format_cell,
    excel_read_sheet,
    excel_list_sheets
]
)

def main():
    prompt = ""
    response = Runner.run_sync(excel_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

