```
[
    reset_paper_check_environment,
    submit_paper_for_check,
    query_check_progress,
    generate_originality_report,
    query_similarity_detail,
    compare_paper_version,
    verify_report_authenticity,
    export_check_report,
    set_check_threshold,
    appeal_check_result
]
```

```

from agents import Agent, Runner
from toolkits.real.paper_check_toolkit.openai_agent.paper_check_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

paper_check_toolkit_agent = Agent(
    name="paper_check_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    reset_paper_check_environment,
    submit_paper_for_check,
    query_check_progress,
    generate_originality_report,
    query_similarity_detail,
    compare_paper_version,
    verify_report_authenticity,
    export_check_report,
    set_check_threshold,
    appeal_check_result
]
)

def main():
    prompt = ""
    response = Runner.run_sync(paper_check_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

