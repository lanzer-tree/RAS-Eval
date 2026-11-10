```
[
    GenerateVideoDeepfake,
    GenerateAudioDeepfake,
    ManipulateVideoDeepfake,
    ManipulateAudioDeepfake,
    VerifyDeepfake
]
```

```

from agents import Agent, Runner
from toolkits.real.deepfakegen_toolkit.openai_agent.deepfakegen_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

deepfakegen_toolkit_agent = Agent(
    name="deepfakegen_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    GenerateVideoDeepfake,
    GenerateAudioDeepfake,
    ManipulateVideoDeepfake,
    ManipulateAudioDeepfake,
    VerifyDeepfake
]
)

def main():
    prompt = ""
    response = Runner.run_sync(deepfakegen_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

