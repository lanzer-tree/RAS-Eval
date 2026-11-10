```
[
    create_study_set,
    get_study_set,
    generate_recite_plan,
    start_quiz_practice,
    submit_quiz_answer,
    join_study_group,
    share_study_set,
    query_learning_progress,
    review_mistake_notebook
]
```

```

from agents import Agent, Runner
from toolkits.real.quizlet_toolkit.openai_agent.quizlet_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

quizlet_toolkit_agent = Agent(
    name="quizlet_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    create_study_set,
    get_study_set,
    generate_recite_plan,
    start_quiz_practice,
    submit_quiz_answer,
    join_study_group,
    share_study_set,
    query_learning_progress,
    review_mistake_notebook
]
)

def main():
    prompt = ""
    response = Runner.run_sync(quizlet_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

