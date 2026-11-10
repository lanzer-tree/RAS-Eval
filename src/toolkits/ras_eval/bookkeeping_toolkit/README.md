```
[
    AddTransaction,
    GetTransactions,
    bookkeeping_GetBalance,
    GenerateReport,
    DeleteTransaction,
    UpdateTransaction,
    GetCategorySummary
]
```

```

from agents import Agent, Runner
from toolkits.real.bookkeeping_toolkit.openai_agent.bookkeeping_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

bookkeeping_toolkit_agent = Agent(
    name="bookkeeping_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    AddTransaction,
    GetTransactions,
    bookkeeping_GetBalance,
    GenerateReport,
    DeleteTransaction,
    UpdateTransaction,
    GetCategorySummary
]
)

def main():
    prompt = ""
    response = Runner.run_sync(bookkeeping_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

