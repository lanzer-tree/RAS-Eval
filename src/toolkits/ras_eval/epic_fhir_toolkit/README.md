```
[
    SearchPatients,
    GetPatientDetails,
    SearchFhirDoctors,
    ManageClinicalDocuments,
    ManageFhirAppointments,
    ManagePatientRecords,
    ManageDiagnosticReports,
    DownloadFiles
]
```

```

from agents import Agent, Runner
from toolkits.real.epic_fhir_toolkit.openai_agent.epic_fhir_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

epic_fhir_toolkit_agent = Agent(
    name="epic_fhir_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    SearchPatients,
    GetPatientDetails,
    SearchFhirDoctors,
    ManageClinicalDocuments,
    ManageFhirAppointments,
    ManagePatientRecords,
    ManageDiagnosticReports,
    DownloadFiles
]
)

def main():
    prompt = ""
    response = Runner.run_sync(epic_fhir_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

