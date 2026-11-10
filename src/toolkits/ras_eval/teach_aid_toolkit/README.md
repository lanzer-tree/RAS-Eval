```
[
    manage_course,
    batch_import_students,
    manage_course_resources,
    publish_assignment,
    grade_assignment,
    manage_grade_book,
    process_student_interaction,
    send_notification,
    sync_teaching_data
]
```

```

from agents import Agent, Runner
from toolkits.real.teach_aid_toolkit.openai_agent.teach_aid_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

teach_aid_toolkit_agent = Agent(
    name="teach_aid_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    manage_course,
    batch_import_students,
    manage_course_resources,
    publish_assignment,
    grade_assignment,
    manage_grade_book,
    process_student_interaction,
    send_notification,
    sync_teaching_data
]
)

def main():
    prompt = ""
    response = Runner.run_sync(teach_aid_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

