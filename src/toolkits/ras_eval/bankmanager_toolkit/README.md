```
[
    GetAccountInformation,
    TransferFunds,
    SearchPayee,
    PayBill,
    GetAccountStatement,
    SearchTransactions
]
```

```

from agents import Agent, Runner
from toolkits.real.bankmanager_toolkit.openai_agent.bankmanager_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

bankmanager_toolkit_agent = Agent(
    name="bankmanager_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    GetAccountInformation,
    TransferFunds,
    SearchPayee,
    PayBill,
    GetAccountStatement,
    SearchTransactions
]
)

def main():
    prompt = ""
    response = Runner.run_sync(bankmanager_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

