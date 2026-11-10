```
[
    word_create_document,
    word_add_heading,
    word_add_paragraph,
    word_add_table,
    word_delete_paragraph,
    word_add_picture,
    word_add_page_break,
    word_search_and_replace,
    word_format_text,
    word_get_document_info,
    word_get_document_text,
    word_get_document_outline,
    word_get_document_paragraph,
    word_copy_document,
    word_list_documents
]
```

```

from agents import Agent, Runner
from toolkits.real.word_toolkit.openai_agent.word_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

word_toolkit_agent = Agent(
    name="word_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    word_create_document,
    word_add_heading,
    word_add_paragraph,
    word_add_table,
    word_delete_paragraph,
    word_add_picture,
    word_add_page_break,
    word_search_and_replace,
    word_format_text,
    word_get_document_info,
    word_get_document_text,
    word_get_document_outline,
    word_get_document_paragraph,
    word_copy_document,
    word_list_documents
]
)

def main():
    prompt = ""
    response = Runner.run_sync(word_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

