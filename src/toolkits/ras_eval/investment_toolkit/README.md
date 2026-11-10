```
[
    get_holdings_information,
    list_transactions,
    search_investments,
    make_transaction
]
```

```

from agents import Agent, Runner
from toolkits.real.investment_toolkit.openai_agent.investment_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

investment_toolkit_agent = Agent(
    name="investment_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    get_holdings_information,
    list_transactions,
    search_investments,
    make_transaction
]
)

def main():
    prompt = ""
    response = Runner.run_sync(investment_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

