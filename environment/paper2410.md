4
2
0
2
c
e
D
5
2

]
E
S
.
s
c
[

2
v
9
0
2
4
1
.
0
1
4
2
:
v
i
X
r
a

Agents4PLC: Automating Closed-loop PLC Code
Generation and Verification in Industrial Control
Systems using LLM-based Agents

Zihan Liu*
Zhejiang University
zihanliu@zju.edu.cn

Ruinan Zeng*
Zhejiang University
zengruinan@zju.edu.cn

Dongxia Wang(cid:66)
Zhejiang University
dxwang@zju.edu.cn

Gengyun Peng
Zhejiang University
pgengyun@zju.edu.cn

Jingyi Wang
Zhejiang University
wangjyee@zju.edu.cn

Qiang Liu
Zhejiang University
22460396@zju.edu.cn

Peiyu Liu
Zhejiang University
liupeiyu@zju.edu.cn

Wenhai Wang(cid:66)
UWin Tech & Zhejiang University
zdzzlab@zju.edu.cn

Abstract—In industrial control systems, the generation and
verification of Programmable Logic Controller (PLC) code are
critical for ensuring operational efficiency and safety. While
Large Language Models (LLMs) have made strides in automated
code generation, they often fall short in providing correctness
guarantees and specialized support for PLC programming. To
address these challenges, this paper introduces Agents4PLC, a
novel framework that not only automates PLC code generation
but also includes code-level verification through an LLM-based
multi-agent system. We first establish a comprehensive bench-
mark for verifiable PLC code generation area, transitioning from
natural language requirements to human-written-verified formal
specifications and reference PLC code. We further enhance our
‘agents’ specifically for industrial control systems by incorporat-
ing Retrieval-Augmented Generation (RAG), advanced prompt
engineering techniques, and Chain-of-Thought strategies. Eval-
uation against the benchmark demonstrates that Agents4PLC
significantly outperforms previous methods, achieving superior
results across a series of increasingly rigorous metrics. This
research not only addresses the critical challenges in PLC
programming but also highlights the potential of our framework
to generate verifiable code applicable to real-world industrial
applications.

Index Terms—Code Generation, Code Validation, PLC Code,

LLM-based Agents, Multi Agents, Industrial Control System

I. INTRODUCTION

Programmable Logic Controllers (PLCs) are essential com-
ponents of Industrial Control Systems (ICSs), playing a crucial
role in industrial automation and management of key industrial
processes. The global PLC market is projected to reach USD
12.20 billion by 2024, with a compound annual growth rate
(CAGR) of 4.37% from 2024 to 2029 [36], [48]. This growth
is largely driven by the increasing reliance on industrial control
programming languages based on IEC 61131-3 standard [20],
such as Structured Text (ST) and Function Block Diagram
(FBD), to oversee and regulate critical infrastructure systems
across key sectors like energy [51], manufacturing [43], and

Co-first authors: Zihan Liu and Ruinan Zeng; Corresponding authors:

Dongxia Wang and Wenhai Wang

transportation [24]. Among others, ST language, as a text-
based language, is most similar to other popular high-level
languages (in terms of syntax and program structure) and is
thus suitable for code generation.

In ICSs, automatic generation of control code can greatly
reduce repetitive tasks, significantly enhancing engineers’
productivity. With the rapid advancement of large language
models (LLMs), automatic code generation has gained much
attention across various programming languages (e.g., C [55],
C++ [10], Python [56], Java [11], etc) due to its potential to
automate software development and reduce costs. It is thus
desirable to explore LLM-based automated code generation
methods for industrial control code development.

Emerging LLMs for code generation (a.k.a. code LLMs),
such as Openai Codex [9], AlphaCode [33], CodeLlama [42],
may not be ideal for PLC code generation due to the fol-
lowing critical reasons. Firstly, these code LLMs may excel
at generating code in mainstream high-level languages such
as C or Python, but mostly perform poorly for industrial
control code. Indeed, it is notoriously challenging to collect
sufficient data for fine-tuning a specialized model for industrial
code due to the proprietary and specialized nature of PLC
code. Secondly, as the control code is used to manage the
operation of industrial sectors, it is of vital importance to
guarantee their functional correctness, which is far more
challenging than generating executable code. There exist some
efforts towards achieving specialized PLC code generation,
such as LLM4PLC [14] and the work of Koziolek [27] either
by finetuning or Retrieval-Augmented Generation (RAG) en-
hancements. LLM4PLC [14] also incorporates workflows for
syntax and functional verification at the design-level beyond
code generation to improve the code quality. However, the
correctness of specifications is only verified at the design
level while the correctness of the LLM-generated code remains
questionable. Moreover, their model-centred architecture lacks
agility in integrating the whole development pipeline to
achieve full automation. On the other hand, there is a growing

trend in automated LLM-based development workflows aimed
to further refine or validate code generated by LLMs using a
multi-agent system architecture. For instance, ChatDev [39]
and MapCoder [22] implement software development systems
composed of multiple intelligent agents, each with distinct
roles and tasks, with the goal of generating high-quality
code in a closed-loop manner. Notably, such an agent-based
framework is flexible to implement multiple relevant software
engineering tasks like validation and debugging, which are
crucial in improving the quality of generated code.

In this work, we present a novel LLM-based multi-agent
framework designed to address the limitations of current PLC
code generation solutions, namely Agents4PLC. Our system
comprises multiple agents, each tailored to specific tasks
such as PLC code generation, syntax validation, functional
verification and debugging (in case of failures). Such a closed-
loop workflow allows Agents4PLC to effectively coordinate
different agents to automatically generate high-quality code
(verifiable correct in the ideal case). Note that different from
LLM4PLC which only verified the correctness of the spec-
ification, we directly verify the correctness of the generated
code. Meanwhile, by leveraging advanced multi-agent archi-
tectures like LangGraph and MetaGPT, Agents4PLC is highly
adaptable to a wide range of PLC code generation tasks and
incorporate different base code LLMs.

• We establish a comprehensive benchmark that transitions
from natural language requirements to formal specifi-
cations, utilizing verified reference code with human-
checked labels, to facilitate future research in the field
of PLC code generation.

• We introduce Agents4PLC, the first LLM-based multi-
agent system for fully automatic PLC code genera-
tion that surpasses purely LLM-based approaches (e.g.,
LLM4PLC [14]) by emphasizing code-level over design-
level verification, and flexibility to incorporate various
base code generation models (in both black-box and
white-box settings) and supporting an array of tools for
compilation, testing, verification and debugging.

• We enhance our agents specifically for PLC code gen-
eration by implementing techniques such as Retrieval-
Augmented Generation (RAG), advanced prompt engi-
neering, and Chain-of-Thought methodologies, improving
their adaptability and effectiveness in generating reliable
PLC code.

• We rigorously evaluate Agents4PLC against the largest
benchmark available, demonstrating superior perfor-
mance across a series of increasingly stringent metrics.
We also deploy and validate our generated code on
multiple practical scenarios, highlighting its potential for
generating verifiable PLC code that meets the demands
of practical industrial control systems.

II. BACKGROUND

A. PLC Programming Language

PLCs are computer systems specifically designed for indus-
trial automation control, enabling real-time monitoring and

control of mechanical equipment and production processes.
PLCs are widely utilized in manufacturing,
transportation,
energy, and other sectors due to their high reliability, ease
of programming, and scalability. The IEC 61131-3 standard
[20] specifies five standard programming languages for PLCs,
which include three graphical
languages: Ladder Diagram
(LAD), Function Block Diagram (FBD), and Sequential Func-
tion Chart (SFC), as well as two textual languages: Structured
Text (ST) and Instruction List (IL). The structured text (ST)
language, similar in syntax and structure to traditional pro-
gramming languages such as C and Pascal, offers significant
flexibility and readability. It supports common programming
structures, including loops and conditional statements, making
it widely used in scenarios that require complex mathematical
calculations, data processing, and advanced control algorithms.
With the development of Industry 4.0 and intelligent manufac-
turing, the prospects for ST language are extremely promising,
as it can complement other programming languages to enhance
the flexibility and efficiency of PLC systems.

B. Syntax Checking and Functional Verification

Code generated by LLMs often exhibits considerable uncer-
tainty and may sometimes fail to compile or meet specified
requirements [45]. Syntax checking ensures that the generated
ST code is executable, while functional verification ensures
that the code realizes the expected functionality and avoids
potential logic flaws or vulnerabilities [15].

1) Syntax Checking: A piece of code first needs to conform
to the standards of a programming language before it can be
compiled into an executable program. Many PLC Integrated
Development Environments (IDEs), such as CODESYS and
TwinCAT, can perform syntax checking for ST code. These
IDEs conform to the IEC 61131-3 standard and provide
functionalities such as programming, debugging, and simu-
lation. However, due to the limitations of their platforms,
these IDEs are not convenient for direct
integration into
automated code generation pipelines. Some command-line
tools can also perform syntax checking and compilation of
ST code. MATIEC [2] is an open-source compiler capable
of refactoring or compiling ST code into C language, widely
used in the design and maintenance of industrial automation
systems. RuSTy [6] is an open-source project based on LLVM
and Rust, aimed at creating a fast, modern, and open-source
industry-grade ST compiler for a wide range of platforms,
providing comprehensive compilation feedback.

2) Functional Verification: Functional verification is crucial
the generated ST code can
for PLC code, ensuring that
accurately and reliably implement the intended control logic
and operations in real-world applications, thereby preventing
equipment failures or production interruptions due to logical
errors or unforeseen circumstances. There exist some formal
verification tools such as nuXmv [8] and PLCverif [12] for
functional validation of ST code, which are serving as the
backend verifier of our validation agent.

2

various aspects of the software development life cycle. Recent
advancements in this field such as ChatDev [39], MetaGPT
[17] and CodeAgent [47], showcase the potential of integrating
AI-driven agents to enhance collaborative software devel-
opment frameworks, automate code review processes, and
support contextual conversation within software development
environments. These studies indicate a shift towards more
interactive and intelligent software development tools that can
adapt to the dynamic nature of development projects, providing
developers with context-aware assistance and streamlining
tasks through autonomous agents. The integration of advanced
human processes within multi-agent systems emphasizes the
potential of agent-based software development to revolutionize
traditional software engineering practices.

III. AGENTS4PLC METHODOLOGY

We propose Agents4PLC, an LLM-based multi-agent
framework for automating the generation and verification pro-
cess of ST code. The framework includes a set of agents with
our defined roles and division of work, which automatically
cooperate based on our defined workflow for the generation of
reliable ST code. The whole framework is presented in Fig-
ure 2. Below we present the detailed design of Agents4PLC.

A. Agents4PLC Framework

As shown in Fig. 3, Agents4PLC takes an user input of ST
coding requirement, e.g., to control an LED, and outputs the
formally verified ST code. In this process, multiple agents
with different roles cooperate to complete this task based
on our carefully designed workflow. First, the retrieval agent
analyzes the user input, based on which it retrieves the relevant
information about ST codes, such as books and documents.
Then it sends the retrieved information alongside with the
user input (task instructions) to the planning agent, which
is responsible to generate and rank the actionable plans for
code generation, subsequently sent to the Coding Agent. The
Coding Agent generates ST code accordingly to the received
plans, and later a compiler checks whether there are syntax
errors. If no error occurs, the validation agent (the verifier)
will verify the functional correctness of the generated code.
Otherwise,
the error information will be delivered to the
debugging agent who will return the fixing advice to the
Coding Agent. If validation succeeds, the generation process
is considered completed. Otherwise, the above workflow will
iterate until it exceeds a predefined loop threshold, where the
planning agent provides another plan for code generation.

B. Detailed Agents Design and Optimization

The primary components of Agent4PLC are a group of au-
tonomous agents powered by Large Language Models (LLMs)
or analysis tools. These agents are meticulously designed to
perform specialized tasks that collectively contribute to the
efficient generation, validation, and iterative refinement of ST
code. Each agent operates within a well-defined functional
scope, allowing for the delegation of specific responsibilities

Fig. 1: Basic portrait of LLM-based agents

C. LLM-based Agents

The rapid advancement of LLMs has elevated traditional AI
agents, which relied on reinforcement learning and symbolic
logic [21], [23], [34], [35], [41], [53], to a new level, i.e., LLM-
based agents. With the assistance of LLMs, these agents have
a strong ability to understand language, generate content, and
utilize external knowledge and tools. They can perform com-
plex tasks and make decisions through collaboration among
agents and interaction with their environments.

There exist various definitions of what comprises an LLM-
based agent, and we present some common components here.
Typically, an LLM-based agent consists of five key compo-
nents: LLM, observation, memory, thought and action [17].
Figure 1 presents its basic framework1. Each component can
be analogized to human cognition for better understanding.
LLMs serve as part of an agent’s “brain”, enabling it to com-
prehend information, learn from interactions, make decisions,
and perform actions. It perceives the environment with the
observation component, e.g., receiving multimodal informa-
tion from the others. It uses memory component to store
past interactions and observations. It retrieves and analyzes
information with thought component, to infer the next action.
And it execute actions using the LLMs or some external tools.
There are mainstream agent frameworks that can support
the development of LLM-based multi-agent workflows, such
as MetaGPT [17], LangGraph [5], and AutoGen [52]. These
frameworks provide libraries that enable developers to create
and manage multiple agents seamlessly. They facilitate the
integration of large language models into complex work-
flows, allowing for efficient communication and collaboration
among agents. Additionally,
these frameworks often come
with features like natural language processing capabilities, task
orchestration, and easy scalability, making them ideal choices
for building sophisticated multi-agent systems.

D. Agent-based Software Development

Agent-based software development is an emerging field that
integrates autonomous and communicative agents to enhance

1More details about different definitions and the components can be found

in [17], [50], [57]

3

InputsToolsEnvironmentObservationMemoryThoughtActionLLM-based AgentFig. 2: Overview of Agents4PLC.

Retrieval Agent primarily focuses on searching for the relevant
industrial control documents, PLC programming references,
and ST code from a vector database for the reference of
the following planning process. It can access both web-based
search tools and also internal databases to extract pertinent
information.

2) Planning Agent: The Planning Agent receives the user
input and the information retrieved by the retrieval agent,
based on which it generates actionable plans using a structured
automata-like format. Each plan represents a sequence of steps
required to achieve the task. The planning agent ranks these
plans, which later will get executed sequentially, based on their
ranking, help identify the most suitable solution.

3) Coding Agent: The Coding Agent is pivotal in con-
verting the detailed plans from the upstream agent into ST
code, ensuring compliance with both syntactic and semantic
requirements. By utilizing a RAG block, the agent accesses a
comprehensive database of PLC documentation and validated
ST code samples. RAG enables the agent
to learn from
the established experience and domain-specific knowledge,
thus making informed decisions based on the provided PLC
resources, help improve the reliability of the generated code.
In addition, prompts for the Coding Agent play a crucial role
in steering the Coding Agent throughout the code generation
process. These prompts encapsulate domain-specific rules and
constraints, to guide the Coding Agent to follow the com-
piler requirements and the predefined validation criteria. The
Coding Agent operates iteratively alongside debugging and
validation agents, fostering a collaborative loop that facilitates
continuous feedback. This interaction enables the early iden-
tification and resolution of syntactic, logical, and functional
errors, significantly improving the overall code quality.

Optimization: To further improve the quality of the gen-

Fig. 3: An example of generating LED Control ST code with
Agents4PLC.

such as code generation, debugging and validation. In particu-
lar, the LLM-based agents excel at tasks such as understanding
user specifications provided in natural language, retrieving
relevant information, and generating ST code. Meanwhile,
tool-based agents are designed to address domain-specific
tasks, such as syntax checking and verification of ST code. The
cooperation workflow among agents within this architecture
not only enhances the scalability and adaptability but also
facilitates collaborative interactions, creating a continuous
feedback loop that improves the overall code development.

1) Retrieval Agent: The Retrieval Agent is responsible for
gathering relevant information for reference based on user in-
put. Although some key agents in the framework are equipped
with a RAG module to enhance task-specific abilities, the

4

Sorted N PlansGenerated ST   CodePlanning AgentCoding AgentSyntax CheckFunctional VerificationGenerated PropertiesValidation AgentSyntax-checked CodeUnpassed Syntax-checked Code and FeedbackStage 1: Syntax CheckingStage 2: Functional VerificationFinal STCodeIterative turn = T,back to planning agent and select next planIterative turn < TUse structured text to design a PLC function block“E.g., the function block should represent a simple control system where PB1 and PB2 determine whether LED is on or off based on the specified logic.”User InputStructured TextProblemKnowledge  DatabaseRelevant SolutionsRelevant Knowledge PointsRetrieveRetrieval AgentGenerated  Fix PatchGenerated Fixed ST CodeDebugging AgentDesign a PLC function block named `LED_Control` using structured text (ST code).The function block should contain:#   - Two Boolean input variables: PB1 and PB2#   - One Boolean output variable: LED# Implement logical operations such that `LED` is assigned the value ...    Boolean logic is fundamental in control systems and PLC programming. Here’s a high-level overview of how to implement Boolean logic in Structured Text:1. **Understanding Boolean Variables**: In PLC programming, Boolean variables are used to represent two states: TRUE (1) and FALSE (0). These variables are crucial for making decisions within the control system. ...Given a competitive programming problem, generate a concrete planning to solve the problem.1. Define the function block `LED_Control`.2. Declare the input variables `PB1` and `PB2` as Boolean.3. Declare the output variable `LED` as Boolean.4. Implement the logical operation inside the function block where `LED` is assigned the result of `PB1` AND (NOT `PB2`)  AND end the function block.Retrieval AgentCoding Agent[start_scl]FUNCTION_BLOCK LED_Control    VAR_INPUT        PB1 : BOOL;  (* Input Push Button 1 *)        PB2 : BOOL;  (* Input Push Button 2 *)    END_VAR    VAR_OUTPUT        LED : BOOL;  (* Output LED *)    END_VAR    LED := PB1 AND NOT PB2;END_FUNCTION_BLOCK[end_scl]Planning AgentValidation AgentStage 1: Syntax CheckingST code Compilation success, waiting for validationStage 2: Functional Verification'property 1: job_req: pattern is satisfied by the program.pattern details: If "instance.PB1 = TRUE AND instance.PB2 = FALSE" is true at the end of the PLC cycle, then "instance.LED = TRUE" should always be true at the end of the same cycle.'[start_scl]FUNCTION_BLOCK LED_Control    VAR_INPUT        PB1 : BOOL;  (* Input Push Button 1 *)        PB2 : BOOL;  (* Input Push Button 2 *)    END_VAR    VAR_OUTPUT        LED : BOOL;  (* Output LED *)    END_VAR    LED := PB1 AND NOT PB2;END_FUNCTION_BLOCK[end_scl]Final ST CodeProblemerated code, the guiding prompts for the Coding Agent are
meticulously refined. These prompts include critical elements
of PLC coding, such as defining the roles and responsibilities
of various code modules, enforcing action constraints for
compliance with system safety and operational regulations,
and leveraging insights from the detailed plans provided by the
Planning Agent. These help the Coding Agent meet not only
the structural requirements but also the operational constraints,
improving code reliability and practicability.

4) Debugging Agent: The Debugging Agent is essential for
analyzing errors and inconsistencies that emerge during the
compilation of the ST code. It interprets feedback from the
ST compiler and utilizes RAG tools alongside the prompts
designed for patch generation to produce the revised code.
The revised code is then relayed to the Validation Agent
for syntactic and semantic verification. The Debugging Agent
consists of three components as follows.

• Syntactic Fixing Advice Generation. With the input
from the compilation results of the ST compiler within
the validation agent, it generates fixing advice based on
the syntactic checking results including the error locations
and reasons. The fixing employs a structured patch gener-
ation process, utilizing a step-by-step Chain-of-Thought
(CoT) methodology that analyzes the origin of error
code, its info and description respectively. This thorough
analysis leads to accurate identification of the reasons
of error and generation of fixing advice, significantly
enhancing the accuracy and efficiency of error fixing.
• Semantic Fixing Advice Generation. This component
is to address semantic errors identified during formal
verification. Similar to the syntactic process, the semantic
fixing process is also based on CoT, which guides the
LLM to assess the violated property and the reason of
violation, pinpoint potential code segments responsible
for the property violations, and generate fixing advice.
• Fixed Code Generation. This component accepts the
fixing advice from the previous processes, along with
the generated code and the currently active plan from
the Planning Agent, based on which it repairs the code.
Its design mirrors that of the Coding Agent, leveraging
RAG to access the same comprehensive database of the
reference resources. By integrating this information, the
Debugging Agent can refine its output before relaying
them to the Validation Agent.

Optimization The Debugging Agent serves as a critical
module for rectifying code errors. Inspired by existing work
in automated code repair [54], which utilizes the generated
dialogue history and real-time feedback for corrective sugges-
tions, we develop a comprehensive workflow for patch analysis
and generation within the Debugging Agent. We adopt the CoT
methodology to guide code repair through the patch generation
process. Compared to the traditional fine-tuning methods for
code repair, our approach enhances the effectiveness and
adaptability of the repair process. By encouraging the LLM to
reflect on error messages, relevant code lines, and test names,

the repair process becomes more intuitive and responsive.
This structured reflection fosters a deeper understanding of the
issues at hand, resulting in more precise and effective fixes.

Furthermore, providing contextual

information, such as
formal verification properties and validation outcomes helps
the code repair model generate more accurate and targeted
corrections. This strategy significantly enhances the repair
process, particularly for errors that cannot be resolved solely
through an examination of the source code.

The use of RAG for code generation also proves effective
during the debugging phase. Employing previously generated
patches in a self-RAG context can improve the effectiveness
of repair, capitalizing on the wealth of information contained
in the generated outputs. By continuously refining and vali-
dating code through this advanced debugging framework, the
Debugging Agent not only enhances the quality of the final
output but also optimizes the overall development workflow.
5) Validation Agent: The Validation Agent is responsible
for verifying the functional correctness of ST code. Different
from LLM4PLC [14], it offers code-level verification for the
ST code, which is necessary for the industrial control systems.
The agent is composed of several specialized sub-components,
each tasked with specific validation responsibilities:

• ST Code Compilation. The first step in the validation
process is to run the received ST code through a compiler
to verify its syntactic correctness. This step ensures the
generated code conforms to the syntactical rules of ST.
If the compilation is successful, the process advances to
the verification phase. Otherwise, the compiler provides
detailed error information, which is then fed into the
Debugging Agent for code correction. By automating
this initial verification step, the Validation Agent helps
streamline the debugging cycle and reduces manual in-
tervention.

• Property Generation. In cases where formal speci-
fications are not explicitly provided by the user,
the
agent uses a subcomponent that leverages an LLM-driven
mechanism to generate a set of formal specifications
automatically. These specifications are derived from user
input,
industry standards, and general safety require-
ments, and they are structured to meet the format required
by formal verification tools. This process help make
the validation process efficient, especially in complex or
large-scale systems where manual specification writing
can be time-consuming and error-prone.

• Translation-based ST Code Analysis. This subcompo-
nent translates the generated ST code into formats or
languages compatible with formal verification tools such
as SMV or CBMC [29]. The translation process is either
managed by LLM-driven agents or by specialized tools
like PLCverif [12].

Optimization One primary challenge with LLM-guided
verification is the potential of inconsistencies between the
original ST code and the translated version used for formal
verification. Also, automatically translated code may lead
to state explosion, a common problem in model checking

5

where the state space grows exponentially, making verification
computationally expensive or infeasible. To address these,
we integrate advanced translation-based verification tools like
PLCverif, which has been optimized for translating ST code
into SMV or CBMC formats for model checking and bounded
model checking (BMC), and may help alleviate the problem
of state explosion. Our design of the Validation Agent allows
for easy incorporation of new verification tools as they be-
come available, future-proofing the framework and ensuring
that it remains adaptable to advances in the field of formal
verification.

Another challenge is that in real-world applications, users
often struggle to define formal properties for verification. To
address this, we develop a specification generation tool within
the Validation Agent. It helps users automatically generate
formal properties in a format suitable for verification tools,
leveraging the chain-of-thought (CoT) methodology to guide
the process. This automated approach not only provide conve-
nience for users but also ensures that the generated properties
are tailored to formal verification.

IV. EXPERIMENTAL EVALUATION

To systematically evaluate the effectiveness, efficiency, and
other key aspects of our framework for PLC code generation,
we design a series of experiments aimed at answering the
following research questions (RQs):

• RQ1: Can Agents4PLC generate PLC code more effec-

tively compared to the existing approaches?

• RQ2: How efficient Agent4PLC is in PLC code genera-

tion?

• RQ3: How effective are the designs in agents, e.g., RAG

and prompt design in the Coding Agent?

• RQ4: How useful is the generated code in practical PLC

production environments?

Benchmark Construction. To accurately evaluate our
Agents4PLC system, we constructed the first benchmark
dataset focused on the task of generating ST code from natural
language specification, and we assess the correctness of code
samples automatically through formal verification methods.
This dataset comprises 23 programming tasks along with
corresponding formal verification specifications, including 58
properties in easy set with 53 non-trivial property over 16 easy
programming tasks and 43 in medium set with 38 non-trivial
property over 7 medium programming tasks, where trivial
property means ”assertion” property without corresponding as-
sertion sentences in ST code for reference. These programming
problems cover various aspects of industrial programming in-
cluding Logical Control, Mathematical Operations, Real-time
Monitoring, Process Control and other fields, which effectively
simulate the genuine requirements found in industrial control
systems.
Base LLMs and Retrieval Model. For a comprehensive
evaluation of Agents4PLC against different base models, we
investigated the capabilities of several popular code LLMs.
In particular, we adopt CodeLlama 34B [42], DeepSeek V2.5

[16], GPT-4o [3] and GPT-4o-mini [4] to evaluate our method.
For the retrieval model, we utilize text-embedding-ada-002, an
advanced model developed by OpenAI.
Evaluation Metrics. Following previous work [14], we em-
ploy the 1) pass rate, 2) syntax compilation success rate
and 3) verification success rate (or verifiable rate) as metrics
to evaluate the effectiveness of code generation. The syntax
compilation success rate serves as a preliminary validation
of the syntactic correctness of the generated ST code. A
high syntax compilation success rate indicates fewer syntax
errors, thereby reducing subsequent debugging efforts. The
pass rate is derived from the pass@k metric, where the model
is considered successful if at least one of the k generated
results that not only compile successfully but also adhere to the
specified functional requirements of the PLC program, which
is the most challenging task. The verifiable rate quantifies
the proportion of the generated ST code segments that can
pass syntax check of target verification language, e.g. nuXmv
or cbmc. A high verifiable rate reflects the effectiveness of
the approach in generating executable code for verification.
We calculate it as the proportion of code segments that
successfully compile out of the total number of generated code
segments.

A. RQ1: Effectiveness study

V. RESULTS

In this experiment, we systematically compare our frame-
work with other code generation frameworks based on several
base LLMs for generating reliable ST code. Our evaluation
is based on a set of benchmark cases designed to reflect
varying levels of complexity, from relatively straightforward
control sequences (labeled as “Easy”) to more sophisticated
logic processes (labeled as “Medium”). Note that LLM4PLC
is designed to be a half-automated framework with human
interactions, we write an extra automation program to drive the
components of the LLM4PLC framework. More experiment
details are included in our github link 2 and our site.3

The models evaluated in this experiment include CodeLlama
34B, GPT-4o, GPT-4o-mini, and DeepSeek V2.5. Among
these, the CodeLlama 34B model is run on a single NVIDIA
A800 80GB PCIe GPU with pre-trained LoRAs from the
LLM4PLC framework, while the other models are tested
via their respective online APIs. Each model
is provided
with user requirements, code skeletons, and natural language
specifications to generate ST code. This setup mirrors real-
world coding scenarios where the models function as code
generation agents without detailed control over the underlying
logic design. Additionally,
to assess the potential of non-
specialized models for PLC code generation, we also evaluated
the performance of the ChatDev framework [40] with GPT-4o
base model on our benchmark.

The experiment results is shown in Table III, which il-
lustrates the performance of different frameworks based on

2https://github.com/Luoji-zju/Agents4PLC release
3https://hotbento.github.io/Agent4PLC/

6

different models across both “Easy” and “Medium” benchmark
levels. The table presents the pass rates for both compilation
and verification stages, with the format X Y Z%, where X
represents the number of successful passes on corresponding
metrics, Y indicates the total number of programming prob-
lems, and Z% denotes the pass rate percentage. For instance,
LLM4PLC/GPT-4o achieves a syntax compilation pass rate
of 14 16 87.5%, meaning the generated result of LLM4PLC
on the GPT-4o model successfully compiles for 14 out of
16 programming problems, yielding an 87.5% success rate.
We record syntax compilation success rate, verifiable rate and
pass rate for both systems, where “verifiable rate” means the
framework can generate verifiable model for at least 80% of
the given properties, and “pass rate” means that least 80% of
the generated code can compile.

The results highlight the effectiveness of our Agents4PLC
framework which outperforms other software development
frameworks across different benchmark levels. In the “Easy”
category, the performance of LLM4PLC on different mod-
els demonstrates notable variability. The GPT-4o-mini model
achieves the highest syntax compilation pass rate of 93.8%,
successfully compiling 15 out of 16 code segments. In con-
trast, the CodeLlama 34B model, based on the original ex-
perimental setting has the lowest performance, with a syntax
compilation pass rate of only 68.8%. Notably, the verifiable
rate and pass rate for all LLM4PLC models are significantly
low, with both GPT-4o and DeepSeek V2.5 recording a verifi-
able rate of 12.5% on the Easy problems. Only DeepSeek V2.5
achieves a pass rate of 12.5% on these problems, indicating
that the LLM-based automative generation of SMV models
requires further improvement.

On the contrary, Agents4PLC framework exhibits more
consistent performance across different models in the Easy
category. Except for CodeLlama 34B, they all achieve a syntax
compilation pass rate of 100%, successfully compiling all gen-
erated code for the programming problems. Our Agents4PLC
framework across different models achieves a maximum
verifiable rate of 68% and a pass rate of 50% with the
GPT-4o model, indicating the superior capability of our
framework in generating verifiable code.

For the Medium benchmark level, both systems main-
tain their respective performance patterns, with Agents4PLC
consistently outperforming LLM4PLC. All models
from
Agents4PLC manage to achieve a syntax compilation rate of
100% on “Medium” problems, contrasting sharply with the
variable results from LLM4PLC, where the highest syntax
compilation pass rate is again recorded by GPT-4o and GPT-
4o-mini at 57.1%. Our Agents4PLC framework achieves
a maximum verifiable rate of 42.3% with GPT-4o and
DeepSeek V2.5, and a maximum pass rate of 28.6% with
GPT-4o, demonstrating that our framework can effectively
handle tasks involving complex coding problems.

We also conduct experiments on ST code generation using
ChatDev, a general-purpose software development platform
based on multi-agent systems. This software development
framework achieve 43.8% syntax compilation, 43.8% verifi-

able rate, 43.8% pass rate on the Easy category and 28.6%
syntax compilation, 14.3% verifiable rate, and 28.6% pass
rate on medium category, showing that most compilable code
from ChatDev are correct in semantics. However, it is also
worth noting that despite explicitly prompting the ChatDev
it occasionally produces
framework to generate ST code,
code in unrelated languages, such as Python or C++. This
highlights a limitation of general-purpose code generation
frameworks in specialized industrial domains.

B. RQ2: Efficiency study

To evaluate the efficiency of our framework in generating
verifiable st code, we measured the time taken for each
model
to successfully generate a syntactically correct and
semantically verified ST code. Considering in our validation
process, PLCverif is not supported for efficiency evaluation,
we categorize the results based on how many attempts it takes
for each model to pass the syntactic compilation stage. The
categories are as follows:

• 1 Attempt: The code passes syntactic compilation stage

on the first try.

• 2 Attempts: The code passes syntactic compilation stage

on the second attempt after a failure.

• 3 or more than 3 Attempts: The framework takes more

than three attempts to succeed.

The experimental results are presented in Table I, where
the data format represents the number of generation attempts
required / total cases passing syntactic compilation / ratio. The
experimental setup is identical to that of Experiment 1.

The results demonstrate that our framework, when paired
with the base models DeepSeek V2.5, GPT-4o, and GPT-
4o-mini, consistently achieved successful ST code generation
in a single attempt, regardless of whether the problems are
classified as easy or medium. In contrast, the CodeLlama
34B model within our framework exhibited instances of re-
quiring code repair after the initial attempt. In comparison,
the LLM4PLC framework showed multiple instances across
all tested models where two or more attempts are necessary
to produce compilable code. This stark contrast in perfor-
mance underscores that our Agents4PLC framework not
only delivers higher code generation success rates but
also significantly improves efficiency, particularly when
compared to LLM4PLC, which required more frequent
code corrections.

C. RQ3: Ablation study

The ablation study aims to evaluate the influence of specific
design choices within our framework on the performance
of code generation. Our ablation experiments are organized
around two primary domains:

• Coding Agent: We investigate the effects of three sig-
nificant enhancements: syntax hints in prompts, retrieval-
augmented generation (RAG), and one-shot prompting on
the ST code generation process. The following configu-
rations are examined, with each enhancement systemati-
cally removed to assess its impact on the pass rates:

7

TABLE I: Efficiency evaluation: ST code generation times over all attempts passing syntactic compilation

Benchmark Level

Framework

LLM4PLC

Agents4PLC

Base Model
CodeLlama 34B
DeepSeek V2.5
GPT-4o
GPT-4o-mini
CodeLlama 34B
DeepSeek V2.5
GPT-4o
GPT-4o-mini

1 time

8 11 72.7%
12 13 92.3%
13 14 92.9%
15 15 100.0%
4 5 80.0%
16 16 100.0%
16 16 100.0%
16 16 100.0%

Easy Problems
2 time
0 11 0.0%
1 13 7.7%
1 14 7.1%
0 15 0.0%
1 5 20.0%
0 16 0.0%
0 16 0.0%
0 16 0.0%

3 or more
3 11 27.3%
0 13 0.0%
0 14 0.0%
0 15 0.0%
0 5 0.0%
0 16 0.0%
0 16 0.0%
0 16 0.0%

1 time
2 4 50.0%
6 7 85.7%
3 4 75.0%
3 4 75.0%
1 1 100.0%
7 7 100.0%
7 7 100.0%
7 7 100.0%

Medium Problems
2 time
2 4 50.0%
1 7 14.3%
1 4 25.0%
0 4 0.0%
0 1 0.0%
0 7 0.0%
0 7 0.0%
0 7 0.0%

3 or more

0 4 0.0%
0 7 0.0%
0 4 0.0%
1 4 25.0%
0 1 0.0%
0 7 0.0%
0 7 0.0%
0 7 0.0%

Note: The format of data represents the number for corresponding generation times / total cases passing syntactic compilation / ratio.

TABLE II: Ablation Experiment with Designs on Coding and Fixing Agents

Benchmark Level

Easy Problems

Medium Problems

Framework

Base Model

Syntax
Compilation

Pass Rate

Verifiable Rate

One-shot + RAG + Syntax Hint
One-shot + Syntax Hint
One-shot + RAG
One-shot
Zero-shot

16 16 100.0% 8 16 50.0%
16 16 100.0% 11 16 68.8%
16 16 100.0% 6 16 37.5%
16 16 100.0% 6 16 37.5%
16 16 100.0% 7 16 43.8%

11 16 68.8%
12 16 75.0%
9 16 56.2%
9 16 56.2%
8 16 50.0%

Pass Rate

Syntax
Compilation
7 7 100.0% 2 7 28.6%
7 7 100.0% 1 7 14.3%
7 7 100.0% 1 7 14.3%
7 7 100.0% 0 7 0.0%
7 7 100.0% 0 7 0.0%

Verifiable Rate

3 7 42.9%
3 7 42.9%
1 7 14.3%
1 7 14.3%
1 7 14.3%

Without CoT / Patch Template

16 16 100.0% 10 16 62.5%

10 16 50.0%

7 7 100.0% 0 7 0.0%

1 7 14.3%

Coding Agent

Debugging
Agent

Note: The format of data represents number of successful passes on corresponding metrics / total number of programming problems / passing rate.

– Full Configuration: The complete framework incor-
porating syntax hints, RAG, and one-shot prompting.
– Intermediate Configuration without RAG: The
framework utilizing one-shot prompting and syntax
hints, but excluding RAG.

– Intermediate Configuration without Syntax hint:
The framework utilizing simple one-shot prompting
and RAG, but excluding syntax hints.

– Simplified Configuration: A streamlined version

using only plain one-shot prompting.

– Baseline Configuration: The foundational setup
with zero-shot prompting and no supplementary aids
(syntax hints and RAG).

• Debugging Agent: In this segment, we assess the impor-
tance of two critical components of the Debugging agent:
chain-of-thought (CoT) reasoning and patch templates.
We compare the framework’s performance when both
components are disabled, effectively operating without
CoT reasoning and patch templates. This allows us to
quantify the degradation in code correction capabilities
resulting from their absence.
Table II summarizes the findings from this ablation
study, showcasing the ST code verification pass rates and
compilation pass rates across various configurations. The
configuration of experiment and table content is similar
to those in effectiveness study, including metrics and
data format. The configuration that on Easy Problem
set,
the setting combining One-shot and Syntax Hint
yields the highest overall pass rates (68.8%) and verifiable
rates (75.0%). However, the results for medium problems
mirror the full configuration, One-shot + RAG + Syn-
tax Hint configuration, demonstrate superior performance

with 28.6% pass rate and 42.9% verifiable rate). The
impact for each configuration analysis is:

– RAG: The application of RAG provides noticeable
its
improvements for medium-level problems, but
impact on easy problems is less pronounced, and in
some cases, it may even have unintended negative
effects.

– Syntax Hint: Detailed syntax hints significantly en-
hance the effectiveness of code generation, especially
for easy problems. The provision of syntax guidance
helps improve both the syntactical correctness and
the overall quality of generated code.

– One shot: In our experiments, we observe that
one-shot prompting do not
lead to a substantial
improvement in performance. This is likely because
the one-shot method merely provides a reference ST
code template, which has limited effectiveness in
improving the overall quality of code generation.
– CoT in Debugging agent: For easy problems, the
results show no significant difference between using
the standard debugging agent and that with CoT.
However, for medium-level problems, the removal of
CoT noticeably reduce the framework’s performance,
indicating that CoT is crucial for handling more
complex debugging tasks.

The results indicate that

the inclusion of syntax hints
improves performance across all metrics, while the impact
of one-shot prompting remains unclear. However, the effects
of more advanced optimization techniques, such as RAG and
CoT, warrant further investigation. These methods significantly
enhance the framework’s ability to handle complex problems,
but when not carefully designed, they may interfere with the

8

reasoning process on simpler tasks. Additionally, considering
Section V-B, our framework can often generate correct code
in a single attempt. As a result, the current experiments may
not fully capture the effectiveness of the debugging agent.

D. RQ4: Case study in practical control environment

To evaluate how Agent4PLC performs in practical industrial
control environment, we conduct case studies utilizing the
UWinTech Control Engineering Application Software Plat-
form, developed by Hangzhou UWNTEK Automation System
Co., Ltd. UWinTech is a software package designed for using
the UW series control system [1]. It integrates a wide range
of functionalities, including on-site data collection, algorithm
execution, real-time and historical data processing, alarm and
safety mechanisms, process control, animation display, trend
curve analysis, report generation, and network monitoring. The
engineer station configuration software, operator station real-
time monitoring software, and on-site control station real-time
control software operate on different levels of hardware plat-
forms. Its components interact via control networks and system
networks, coordinating the exchange of data, management,
and control information to ensure the successful execution of
various functions within the control system.

Our experiments involve several steps: first, we constructed
the operation station and the control station, then we config-
ured the attributes of the monitoring and control points. These
points are linked to the simulation model, and the generated
ST code from Agent4PLC were uploaded to the control station
to conduct the experiment. We perform four control tasks:
site monitoring and alarm light flashing, low voltage limit
and motor start/stop, temperature and pressure monitoring, and
specific node delay monitoring.

Figure 4 denotes an LED Control task. The prompt is:
design a PLC function block named LED-Control using struc-
tured text (ST) code. The function block should contain two
Boolean input variables (PB1 and PB2) and one Boolean
output variable (LED). Implement logical operations such that
LED is assigned the value resulting from a logical AND
operation between PB1 and the negation of PB2. The function
block should represent a simple control system where PB1
and PB2 determine whether LED is on or off based on the
specified logic. The results show that with the generated ST
code uploaded, when PB1 is true (1) and PB2 is false (0),
namely the the AND operation between PB1 and the negation
of PB2 output 1, the light is green, and otherwise, it is red.
This complies with the requirement in the prompt.

task. The Prompt

Figure 5 denotes a motor control

is:
Design a PLC function block in Structured Text (ST) that
evaluates whether the critical motor should be triggered based
on the given low pressure value compared to a threshold of
36464. The state of Motor-Critical is determined based on
this evaluation. The results show that when the input voltage
is below the threshold 36464, the motor stops; otherwise, the
motor starts.

Fig. 4: LED control with Agents4PLC.

Fig. 5: Motor triggering control with Agents4PLC.

code) that incorporates pressure sensors, temperature sensors,
relays, counters, error codes, and error flags as inputs. The
program must loop through the pressure sensor, adjust the
temperature sensor based on specific conditions, and update
the relay status according to the value of GT1-OUT. Ensure
that
the program checks for conditions to avoid overflow
and maintains the error flag state. Return a Boolean value
indicating the completion of the operation. The results show
that low or high limit alarms and different error codes are
provided when pressure and temperature are abnormal. When
an abnormality occurs, the alarm light will flash. If the pressure
exceeds the upper limit, the error code is 1. If the temperature
is above the high limit, the error code is 3. If the temperature
is below the lower limit, the error code is 4. These comply
with the requirements in the prompt.

VI. RELATED WORKS

There are significantly increasing interests from both the in-
dustry and academia in LLM-based code generation, including
those LLMs specifically designed for code generation such as
DeepSeek-Coder [16], StarCoder [32], and CodeLlama [42].
However, most of them focus on high-level languages such
as C, Python and only a very small portion considers PLC
code in control engineering. Here, we mainly review those
works considering PLC code from the aspects of its generation,
testing and verification. We also seperatly review the existing
LLM-based multi-agent frameworks for code generation.

Figure 6 denotes a temperature and relay update task. The
prompt is: Design a PLC program using structured text (ST

Fig. 6: Temperature update with Agents4PLC.

9

TABLE III: Compilation and Verification Metrics for Different Models

Benchmark Level

Framework

Base Model

LLM4PLC

Agents4PLC

ChatDev

CodeLlama 34B
DeepSeek V2.5
GPT-4o
GPT-4o-mini
CodeLlama 34B
DeepSeek V2.5
GPT-4o
GPT-4o-mini
GPT-4o

Easy Problems
Verifiable Rate

Syntax
Compilation
11 16
68.8%
13 16 81.3%
14 16 87.5%
15 16 93.8%
31.3%
5 16
16 16 100.0% 10 16 62.5%
16 16 100.0% 11 16 68.8%
16 16 100.0% 8 16 50.0%
7 16 43.8%

0 16
0.0%
2 16 12.5%
0 16 0.0%
0 16 0.0%
2 16 12.5%

NA

Pass Rate

0 16
0.0%
2 16 12.5%
2 16 12.5%
0 16 0.0%
1 16 6.3%
7 16 43.8%
8 16 50.0%
7 16 43.8%
NA

Syntax
Compilation

4 7 57.1%
7 7 100.0%
4 7 57.1%
4 7 57.1%
1 7 14.3%
7 7 100.0%
7 7 100.0%
7 7 100.0%
2 7 28.6%

Medium Problems
Verifiable Rate

0 7 0.0%
0 7 0.0%
0 7 0.0%
0 7 0.0%
0 7 0.0%
3 7 42.9%
3 7 42.9%
1 7 14.3%
NA

Pass Rate

0 7 0.0%
0 7 0.0%
0 7 0.0%
0 7 0.0%
0 7 0.0%
1 7 14.3%
2 7 28.6%
0 7 0.0%
NA

Note: The format of data represents number of successful passes on corresponding metrics / total number of programming problems / passing rate.

A. LLM-based Automated PLC Code Generation

There exist a few works studying the LLM-based generation
of PLC programming code like ST. For instance, Koziolek et
al. [26] create 100 prompts across 10 categories to evaluate the
ability of the existing LLMs to produce syntactically correct
control logic code in ST language. Later, they introduce a
retrieval-augmented generation method [27] and an image-
recognition-based generation method [28]. These methods in-
tegrate proprietary function blocks into the generated code and
utilize GPT-4 Vision to generate control logic code for indus-
trial automation from Piping-and-Instrumentation Diagrams
(P&IDs), respectively. However, they do not consider testing or
verification of the generated code, and thus cannot ensure code
correctness. Fakih et al. [14] introduce an LLM-based PLC
code generation pipeline named LLM4PLC, which integrates
the fine-tuned LLMs with external verification tools. Though
it takes formal verification into consideration, it only achieves
design-level verification (instead of the ST code level) and the
generation process can not achieve full automation. Witnessing
these limitations of existing works, we aim to achieve closed-
loop and fully automated PLC code generation and verification
with our designed multi-agent system Agents4PLC, paving a
way for evolving, efficient, trustworthy and intelligent coding
for industrial control systems.

Our work is also inspired by the recent

trend in code
generation approaches which rely on the cooperation of LLM-
based agents. ChatDev [18], a virtual software development
company composed of multiple agents, features clearly defined
roles and divisions of labor, aiming to collaboratively generate
high-quality software code. However, ChatDev still shows
limitations when it comes to generating software code for
industrial control systems without formal verification support.
Mapcoder [22] consists of four LLM-based agents for the tasks
of recalling relevant examples, planning, code generation,
and debugging respectively, relying on multi-agent prompting
for code generation. AutoSafeCoder [37] consists of three
agents responsible for code generation, static analysis and
fuzzing to detect runtime errors respectively. AgentCoder [19]
consists of three agents responsible for code generation and
refinement, test case generation, test execution and feedback
reporting respectively. These approaches all focus on Python
language which is fundamentally different to ST for PLC.

Agents4PLC is the first LLM-agent-based system covering the
whole lifecycle of ST control engineering.

B. PLC Code Testing and Verification

Due to the fact that PLC programming is often performed in
low-level programming languages, which typically use bitwise
and boolean operations, it becomes very difficult to understand
and debug PLC programs. This increases the need for testing
and verification of PLC programs [38], [46]. Existing methods
for the automated generation of PLC test cases mainly include
symbolic execution [44], concolic testing [7] and search-based
techniques [13]. However, these approaches can produce test
cases that are difficult to maintain, making them challenging
to use. Koziolek et al. [25] propose to automatically generate
PLC test cases as a csv file by querying an LLM with a
prompt
to synthesize code test cases. And they found in
experiments that many generated test cases contain incorrect
assertions and require manual correction. The multi-agent
based generation approaches Mapcoder [22], AutoSafeCoder
[37] and AgentCoder [19] all consider code testing, but ignore
formal verification of the generated code.

In terms of PLC code verification, there exist tools like
nuXmv [8] and PLCverif [12] applicable for functional veri-
fication of ST code, which are serving as the backend verifier
in Agents4PLC. Besides, several recent works aim to establish
formal semantics for IEC 61131-3 languages like ST with
more recent language framework like K framework [30], [49],
facilitating testing or verification of ST code [31].

VII. CONCLUSION AND FUTURE WORKS

transitions from natural

In this paper, we presented Agents4PLC, the first LLM-
based multi-agent framework that addresses the critical chal-
lenges of automated Programmable Logic Controller (PLC)
code generation and verification. By establishing a compre-
hensive benchmark that
language
requirements to formal specifications, we laid the groundwork
for future research in the field of PLC code generation. Our
framework not only emphasizes code-level verification and full
automation, but also is flexible to incorporate various base
code generation models and development modules. Extensive
evaluation demonstrates that Agents4PLC significantly outper-
forms the previous approaches, achieving high automation and
verifiability for PLC code generation.

10

In the future, we plan to expand the framework to sup-
port additional PLC programming languages and standards
to enhance its applicability across various industrial contexts.
Moreover, we will explore user feedback mechanisms within
the multi-agent system to help refine the generated code
and the agents based on real-world usage, thereby further
enhancing its usability and reliability.

REFERENCES

[1] “Uwintech control engineering application software platform,” https://

www.uwntek.com/product/2.html, accessed: 2024-10-10.

[2] “Matiec,” 2017. [Online]. Available: https://github.com/nucleron/matiec
[3] “Gpt-4o,” 2024. [Online]. Available: https://platform.openai.com/docs/

models/gpt-4o

[4] “Gpt-4o-mini,” 2024. [Online]. Available: https://platform.openai.com/

docs/models/gpt-4o-mini

[5] “Langgraph,” 2024. [Online]. Available: https://github.com/langchain-ai/

langgraph

[6] “Rusty,” 2024. [Online]. Available: https://github.com/PLC-lang/rusty
[7] D. Bohlender, H. Simon, N. Friedrich, S. Kowalewski, and S. Hauck-
Stattelmann, “Concolic test generation for plc programs using coverage
metrics,” in 2016 13th International Workshop on Discrete Event Sys-
tems (WODES).

IEEE, 2016, pp. 432–437.

[8] R. Cavada, A. Cimatti, M. Dorigatti, A. Griggio, A. Mariotti, A. Micheli,
S. Mover, M. Roveri, and S. Tonetta, “The nuxmv symbolic model
checker,” in Computer Aided Verification: 26th International Confer-
ence, CAV 2014, Held as Part of the Vienna Summer of Logic, VSL
2014, Vienna, Austria, July 18-22, 2014. Proceedings 26.
Springer,
2014, pp. 334–342.

[9] M. Chen, J. Tworek, H. Jun, Q. Yuan, H. P. D. O. Pinto, J. Kaplan,
H. Edwards, Y. Burda, N. Joseph, G. Brockman et al., “Evaluating large
language models trained on code,” arXiv preprint arXiv:2107.03374,
2021.

[10] Z. Chen, S. Fang, and M. Monperrus, “Supersonic: Learning to generate
source code optimizations in c/c++,” IEEE Transactions on Software
Engineering, 2024.

[11] V. Corso, L. Mariani, D. Micucci, and O. Riganelli, “Generating java
methods: An empirical assessment of four ai-based code assistants,”
in Proceedings of the 32nd IEEE/ACM International Conference on
Program Comprehension, 2024, pp. 13–23.

[12] D. Darvas, E. Blanco Vinuela, and B. Fern´andez Adiego, “Plcverif: A
tool to verify plc programs based on model checking techniques,” in
Proceedings of the 15th International Conference on Accelerator and
Large Experimental Physics Control Systems.

IEEE, 2015, pp. 1–6.

[13] M. Ebrahimi Salari, E. P. Enoiu, W. Afzal, and C. Seceleanu, “Pylc: A
framework for transforming and validating plc software using python
and pynguin test generator,” in Proceedings of the 38th ACM/SIGAPP
Symposium on Applied Computing, 2023, pp. 1476–1485.

[14] M. Fakih, R. Dharmaji, Y. Moghaddas, G. Quiros, O. Ogundare, and
M. A. Al Faruque, “Llm4plc: Harnessing large language models for
verifiable programming of plcs in industrial control systems,” in Pro-
ceedings of the 46th International Conference on Software Engineering:
Software Engineering in Practice, 2024, pp. 192–203.

[15] E. First and Y. Brun, “Diversity-driven automated formal verification,”
in Proceedings of the 44th International Conference on Software Engi-
neering, 2022, pp. 749–761.

[16] D. Guo, Q. Zhu, D. Yang, Z. Xie, K. Dong, W. Zhang, G. Chen,
X. Bi, Y. Wu, Y. Li et al., “Deepseek-coder: When the large language
model meets programming–the rise of code intelligence,” arXiv preprint
arXiv:2401.14196, 2024.

[17] S. Hong, X. Zheng, J. Chen, Y. Cheng, J. Wang, C. Zhang, Z. Wang,
S. K. S. Yau, Z. Lin, L. Zhou et al., “Metagpt: Meta programming for
multi-agent collaborative framework,” arXiv preprint arXiv:2308.00352,
2023.

[18] X. Hou, Y. Zhao, Y. Liu, Z. Yang, K. Wang, L. Li, X. Luo, D. Lo,
J. Grundy, and H. Wang, “Large language models for software engi-
neering: A systematic literature review,” ACM Transactions on Software
Engineering and Methodology, 2023.

[19] D. Huang, Q. Bu, J. M. Zhang, M. Luck, and H. Cui, “Agentcoder:
Multi-agent-based code generation with iterative testing and optimisa-
tion,” arXiv preprint arXiv:2312.13010, 2023.

[20] International Electrotechnical Commission

“IEC 61131-
3:2013 Programmable controllers - Part 3: Programming languages,”
https://webstore.iec.ch/en/publication/4552, 2013, edition 3.0, ISBN:
9782832206614.

(IEC),

[21] C. Isbell, C. R. Shelton, M. Kearns, S. Singh, and P. Stone, “A social
reinforcement learning agent,” in Proceedings of the fifth international
conference on Autonomous agents, 2001, pp. 377–384.

[22] M. A. Islam, M. E. Ali, and M. R. Parvez, “Mapcoder: Multi-
agent code generation for competitive problem solving,” arXiv preprint
arXiv:2405.11403, 2024.

[23] L. P. Kaelbling, M. L. Littman, and A. W. Moore, “Reinforcement
learning: A survey,” Journal of artificial intelligence research, vol. 4,
pp. 237–285, 1996.

[24] M. Kornaszewski, “The use of programmable logic controllers in railway
signaling systems,” in ICTE in Transportation and Logistics 2019.
Springer, 2020, pp. 104–111.

[25] H. Koziolek, V. Ashiwal, S. Bandyopadhyay et al., “Automated control
logic test case generation using large language models,” arXiv preprint
arXiv:2405.01874, 2024.

[26] H. Koziolek, S. Gruener, and V. Ashiwal, “Chatgpt for plc/dcs control
logic generation,” in 2023 IEEE 28th International Conference on
Emerging Technologies and Factory Automation (ETFA).
IEEE, 2023,
pp. 1–8.

[27] H. Koziolek, S. Gr¨uner, R. Hark, V. Ashiwal, S. Linsbauer, and N. Es-
kandani, “Llm-based and retrieval-augmented control code generation,”
in Proceedings of the 1st International Workshop on Large Language
Models for Code, 2024, pp. 22–29.

[28] H. Koziolek and A. Koziolek, “Llm-based control code generation using
image recognition,” in Proceedings of the 1st International Workshop on
Large Language Models for Code, 2024, pp. 38–45.

[29] D. Kroening and M. Tautschnig, “Cbmc–c bounded model checker:
(competition contribution),” in Tools and Algorithms for the Construc-
tion and Analysis of Systems: 20th International Conference, TACAS
2014, Held as Part of the European Joint Conferences on Theory and
Practice of Software, ETAPS 2014, Grenoble, France, April 5-13, 2014.
Proceedings 20. Springer, 2014, pp. 389–391.

[30] J. Lee and K. Bae, “Formal semantics and analysis of multitask plc
st programs with preemption,” in International Symposium on Formal
Methods. Springer, 2024, pp. 425–442.

[31] J. Lee, S. Kim, and K. Bae, “Bounded model checking of plc st
programs using rewriting modulo smt,” in Proceedings of the 8th ACM
SIGPLAN International Workshop on Formal Techniques for Safety-
Critical Systems, 2022, pp. 56–67.

[32] R. Li, L. B. Allal, Y. Zi, N. Muennighoff, D. Kocetkov, C. Mou,
M. Marone, C. Akiki, J. Li, J. Chim et al., “Starcoder: may the source
be with you!” arXiv preprint arXiv:2305.06161, 2023.

[33] Y. Li, D. Choi, J. Chung, N. Kushman, J. Schrittwieser, R. Leblond,
T. Eccles, J. Keeling, F. Gimeno, A. Dal Lago et al., “Competition-
level code generation with alphacode,” Science, vol. 378, no. 6624, pp.
1092–1097, 2022.

[34] J. Liu, K. Wang, Y. Chen, X. Peng, Z. Chen, L. Zhang, and Y. Lou,
“Large language model-based agents for software engineering: A sur-
vey,” arXiv preprint arXiv:2409.02977, 2024.

[35] M. Minsky, “Steps toward artificial intelligence,” Proceedings of the

IRE, vol. 49, no. 1, pp. 8–30, 1961.

Intelligence, “Programmable logic controller

(plc) market
[36] Mordor
-
[On-
line]. Available: https://www.mordorintelligence.com/industry-reports/
programmable-logic-controller-plc-market

size & growth,” 2024,

accessed: 2024-10-08.

share,

[37] A. Nunez, N. T. Islam, S. K. Jha, and P. Najafirad, “Autosafecoder: A
multi-agent framework for securing llm code generation through static
analysis and fuzz testing,” arXiv preprint arXiv:2409.10737, 2024.
[38] T. Ovatman, A. Aral, D. Polat, and A. O. ¨Unver, “An overview of model
checking practices on verification of plc software,” Software & Systems
Modeling, vol. 15, no. 4, pp. 937–960, 2016.

[39] C. Qian, W. Liu, H. Liu, N. Chen, Y. Dang, J. Li, C. Yang, W. Chen,
Y. Su, X. Cong et al., “Chatdev: Communicative agents for software
development,” in Proceedings of
the
Association for Computational Linguistics (Volume 1: Long Papers),
2024, pp. 15 174–15 186.

the 62nd Annual Meeting of

[40] C. Qian, W. Liu, H. Liu, N. Chen, Y. Dang, J. Li, C. Yang,
W. Chen, Y. Su, X. Cong, J. Xu, D. Li, Z. Liu, and M. Sun,
“Chatdev: Communicative agents for software development,” arXiv

11

preprint arXiv:2307.07924, 2023. [Online]. Available: https://arxiv.org/
abs/2307.07924

[41] C. Ribeiro, “Reinforcement learning agents,” Artificial intelligence re-

view, vol. 17, pp. 223–250, 2002.

[42] B. Roziere, J. Gehring, F. Gloeckle, S. Sootla, I. Gat, X. E. Tan, Y. Adi,
J. Liu, R. Sauvestre, T. Remez et al., “Code llama: Open foundation
models for code,” arXiv preprint arXiv:2308.12950, 2023.

[43] M. Schreyer and M. M. Tseng, “Design framework of plc-based control
for reconfigurable manufacturing systems,” in Proceedings of interna-
tional conference on flexible automation and intelligent manufacturing
(FAIM 2000), vol. 1, 2000, pp. 33–42.

[44] J. Shi, Y. Chen, Q. Li, Y. Huang, Y. Yang, and M. Zhao, “Automated test
cases generator for iec 61131-3 structured text based dynamic symbolic
execution,” IEEE Transactions on Computers, 2024.

[45] M. L. Siddiq, B. Casey, and J. Santos, “A lightweight framework for
high-quality code generation,” arXiv preprint arXiv:2307.08220, 2023.
[46] A. Singh, “Taxonomy of machine learning techniques in test case gen-
eration,” in 2023 7th International Conference on Intelligent Computing
and Control Systems (ICICCS).

IEEE, 2023, pp. 474–481.

[47] D. Tang, Z. Chen, K. Kim, Y. Song, H. Tian, S. Ezzini, Y. Huang, and
J. K. T. F. Bissyande, “Collaborative agents for software engineering,”
arXiv preprint arXiv:2402.02172, 2024.

[48] Technavio, “Programmable logic controller (plc) market analysis apac,
north america, europe, middle east and africa, south america - us,
china,
japan, germany, uk - size and forecast 2024-2028,” 2024,
accessed: 2024-10-08. [Online]. Available: https://www.technavio.com/
report/programmable-logic-controller-plc-market-industry-analysis
[49] K. Wang, J. Wang, C. M. Poskitt, X. Chen, J. Sun, and P. Cheng, “K-st:
A formal executable semantics of the structured text language for plcs,”
IEEE Transactions on Software Engineering, 2023.

[50] L. Wang, C. Ma, X. Feng, Z. Zhang, H. Yang, J. Zhang, Z. Chen,
J. Tang, X. Chen, Y. Lin et al., “A survey on large language model based
autonomous agents,” Frontiers of Computer Science, vol. 18, no. 6, p.
186345, 2024.

[51] M. Wang, “Application of plc technology in electrical engineering and
automation control,” in Application of Intelligent Systems in Multi-
modal Information Analytics: Proceedings of the 2020 International
Conference on Multi-model Information Analytics (MMIA2020), Volume
2. Springer, 2021, pp. 131–135.

[52] Q. Wu, G. Bansal, J. Zhang, Y. Wu, B. Li, E. Zhu, L. Jiang, X. Zhang,
S. Zhang, J. Liu, A. H. Awadallah, R. W. White, D. Burger, and
C. Wang, “Autogen: Enabling next-gen llm applications via multi-agent
conversation framework,” in COLM, 2024.

[53] Z. Xi, W. Chen, X. Guo, W. He, Y. Ding, B. Hong, M. Zhang, J. Wang,
S. Jin, E. Zhou et al., “The rise and potential of large language model
based agents: A survey,” arXiv preprint arXiv:2309.07864, 2023.
[54] C. S. Xia and L. Zhang, “Keep the conversation going: Fixing
162 out of 337 bugs for $0.42 each using chatgpt,” arXiv preprint
arXiv:2304.00385, 2023.

[55] K. Xu, G. L. Zhang, X. Yin, C. Zhuo, U. Schlichtmann, and B. Li,
“Automated c/c++ program repair for high-level synthesis via large
language models,” in Proceedings of the 2024 ACM/IEEE International
Symposium on Machine Learning for CAD, 2024, pp. 1–9.

[56] K. Zhang, J. Li, G. Li, X. Shi, and Z. Jin, “Codeagent: Enhancing code
generation with tool-integrated agent systems for real-world repo-level
coding challenges,” arXiv preprint arXiv:2401.07339, 2024.

[57] Z. Zhang, X. Bo, C. Ma, R. Li, X. Chen, Q. Dai, J. Zhu, Z. Dong,
and J.-R. Wen, “A survey on the memory mechanism of large language
model based agents,” arXiv preprint arXiv:2404.13501, 2024.

12

