```
[
    DeploySmartContract,
    CallSmartContractFunction,
    TransferEther,
    CreateEthereumAccount,
    ImportEthereumAccount,
    EstimateGasCost,
    CompileSolidity,
    SignMessage,
    VerifyMessage,
    QueryEthereumData
]
```

```

from agents import Agent, Runner
from toolkits.real.ethereum_toolkit.openai_agent.ethereum_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

ethereum_toolkit_agent = Agent(
    name="ethereum_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    DeploySmartContract,
    CallSmartContractFunction,
    TransferEther,
    CreateEthereumAccount,
    ImportEthereumAccount,
    EstimateGasCost,
    CompileSolidity,
    SignMessage,
    VerifyMessage,
    QueryEthereumData
]
)

def main():
    prompt = ""
    response = Runner.run_sync(ethereum_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

