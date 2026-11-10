```
[
    block_domain,
    unblock_domain,
    verify_domain,
    search_threats,
    get_threat_details,
    search_policy,
    create_policy,
    update_policy,
    delete_policy,
    get_policy_details,
    search_logs,
    get_log_details,
    generate_report
]
```

```

from agents import Agent, Runner
from toolkits.real.cisco_toolkit.openai_agent.cisco_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

cisco_toolkit_agent = Agent(
    name="cisco_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    block_domain,
    unblock_domain,
    verify_domain,
    search_threats,
    get_threat_details,
    search_policy,
    create_policy,
    update_policy,
    delete_policy,
    get_policy_details,
    search_logs,
    get_log_details,
    generate_report
]
)

def main():
    prompt = ""
    response = Runner.run_sync(cisco_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

