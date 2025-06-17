3
2
0
2

v
o
N
1
2

]
E
S
.
s
c
[

1
v
5
8
7
2
1
.
1
1
3
2
:
v
i
X
r
a

Prompting Frameworks for Large Language Models: A Survey

XIAOXIA LIU, Zhejiang University, China
JINGYI WANG, Zhejiang University, China
JUN SUN, Singapore Management University, Singapore
XIAOHAN YUAN, Zhejiang University, China
GUOLIANG DONG, Singapore Management University, Singapore
PENG DI, Ant Group, China
WENHAI WANG, Zhejiang University, China
DONGXIA WANG*, Zhejiang University, China

Since the launch of ChatGPT, a powerful AI Chatbot developed by OpenAI, large language models (LLMs) have made significant
advancements in both academia and industry, bringing about a fundamental engineering paradigm shift in many areas. While
LLMs are powerful, it is also crucial to best use their power where “prompt” plays a core role. However, the booming LLMs
themselves, including excellent APIs like ChatGPT, have several inherent limitations: 1) temporal lag of training data, and 2)
the lack of physical capabilities to perform external actions. Recently, we have observed the trend of utilizing prompt-based
tools to better utilize the power of LLMs for downstream tasks, but a lack of systematic literature and standardized terminology,
partly due to the rapid evolution of this field. Therefore, in this work, we survey related prompting tools and promote the
concept of the “Prompting Framework" (PF), i.e. the framework for managing, simplifying, and facilitating interaction with
large language models. We define the lifecycle of the PF as a hierarchical structure, from bottom to top, namely: Data Level,
Base Level, Execute Level, and Service Level. We also systematically depict the overall landscape of the emerging PF field
and discuss potential future research and challenges. To continuously track the developments in this area, we maintain a
repository at https://github.com/lxx0628/Prompting-Framework-Survey, which can be a useful resource sharing platform for
both academic and industry in this field.

CCS Concepts: • Computing methodologies → Natural language processing; • Software and its engineering →
Development frameworks and environments.
Additional Key Words and Phrases: Large language models, prompting

INTRODUCTION

1
Since the release of ChatGPT 1, which attracted widespread social attention, research on large language models
(LLMs) has been in full swing in both academia and industry, resulting in a number of amazing products such as
PaLM [27], GPT-4 [82], and LLaMA [108, 109]. These LLMs have been shown to exhibit remarkable capabilities

1https://openai.com/blog/chatgpt/

*Corresponding author.
Authors’ addresses: Xiaoxia Liu, Zhejiang University, China, liuxiaoxia@zju.edu.cn; Jingyi Wang, Zhejiang University, China, wangjyee@zju.
edu.cn; Jun Sun, Singapore Management University, Singapore, junsun@smu.edu.sg; Xiaohan Yuan, Zhejiang University, China, 22332075@zju.
edu.cn; Guoliang Dong, Singapore Management University, Singapore, gldong@smu.edu.sg; Peng Di, Ant Group, China, dipeng.dp@antgroup.
com; Wenhai Wang, Zhejiang University, China, zdzzlab@zju.edu.cn; Dongxia Wang*, Zhejiang University, China, dxwang@zju.edu.cn.

Permission to make digital or hard copies of all or part of this work for personal or classroom use is granted without fee provided that
copies are not made or distributed for profit or commercial advantage and that copies bear this notice and the full citation on the first
page. Copyrights for components of this work owned by others than ACM must be honored. Abstracting with credit is permitted. To copy
otherwise, or republish, to post on servers or to redistribute to lists, requires prior specific permission and/or a fee. Request permissions from
permissions@acm.org.
© 2023 ACM.
ACM 0360-0300/2023/11-ART
https://doi.org/XXXXXXX.XXXXXXX

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

2

• Xiaoxia Liu, Jingyi Wang, Jun Sun, Xiaohan Yuan, Guoliang Dong, Peng Di, Wenhai Wang, and Dongxia Wang*

in approaching or even exceeding human-level performance in dialogue, text translation, and sentiment analysis
[2, 11, 25, 54], etc, potentially bringing in fundamental changes of many fields [18, 30, 38, 61, 65, 76, 123, 137].

The development of language models to the current flourishing state has undergone a series of evolutionary
processes: fully supervised learning → deep learning for NLP → “Pre-train, Fine-tune" → “Pre-train, Prompt, Predict"
[60, 135]. Initially, language models (LMs) applied a fully supervised learning paradigm, where task-specific models
were trained solely on the target task dataset, heavily relying on feature engineering [53, 80, 98]. Subsequently,
with the rise of deep learning, neural networks for NLP emerged, enabling the integration of feature learning and
model training, i.e., a network architecture designed to automatically learn data features [7, 8, 29, 72]. Later, as
the demand for LMs increased and to accommodate the growing number of NLP tasks, the “Pre-train, Fine-tune"
paradigm was introduced. In this paradigm, a model with a fixed architecture undergoes pre-training to predict
the probability of observed text data. Additional parameters are then introduced, and the model is fine-tuned
using task-specific objective functions to adapt the pre-trained LM to various downstream tasks [55, 100, 111, 128].
Then came the era of LLMs, where the trend shifted towards downstream tasks actively adapting to pre-trained
models. The paradigm of “Pre-train, Prompt, Predict" became mainstream and prompts successfully empowering
the LLMs to effortlessly tackle a wide range of complex and diverse tasks. By providing a suitable set of prompts,
a single language model trained entirely on context-based predictions can be employed to address various tasks
[13, 95]. Therefore, the quality and appropriateness of prompts are increasingly playing a crucial role in task
resolution [51, 120, 136]. Both the academic and industrial communities have shown growing attention and
interest in research related to prompts.

Numerous studies have demonstrated the necessity of employing appropriate methods to unleash the potential
of LLMs [116, 120, 129, 136]. In March 2023, OpenAI officially unveiled a significant innovation known as
ChatGPT plugins, which enable ChatGPT to utilize external tools, reflecting a clear response to the growing
demand for enhancing LLMs’ interaction capabilities with the external world. When analogized to humans, LLMs
can be regarded as the intelligent system’s brain, responsible for perceiving instructions and generating and
controlling a series of actions. Therefore, by combining their inherent knowledge and capabilities with external
tools such as search engines, computational utilities, visual models, and more, LLMs can perform a wide array of
real-world tasks, including real-time data retrieval, browser-based information retrieval, database access, precise
mathematical calculations, complex language generation, and image analysis, thus showcasing their potential
across diverse domains like education, healthcare, social media, finance, and natural sciences [64, 68, 78, 93].
Consequently, the development of tools that facilitate the optimization and streamlining of the interaction process
becomes crucial. In this paper, we collectively refer to these forward-looking tools as a proposed novel concept:
“Prompting Framework" (PF).

In general, Prompting Framework is the upper layer which enables LLMs to interact with the external world. A
prompting framework manages, simplifies, and facilitates such interactions, helping LLMs overcome fundamental
challenges like data lag or “brain in a vet”. Moreover, prompting frameworks also serve as the basic infrastructure
of recently emerging autonomous agents based on LLMs, such as AutoGPT [103], HuggingGPT [122], and
MetaGPT [46].

Since the release of the open-source project LangChain [20] by Harrison Chase in October 2022, it has garnered
attention from over 60,000 supporters on GitHub and stands as one of the most popular prompting frameworks to
date. LangChain is a framework for building applications with LLMs through composability. Besides LangChain,
our investigation encompasses various kinds of state-of-the-art prompting frameworks, including 1) Semantic
Kernel [112], LlamaIndex [59], and OpenDAN [83], which can be arguably considered as the operating systems
for LLMs, as well as 2) output restrictors for LLMs such as Guidance [69], TypeChat [70], NeMo-Guardrails [79],
and 3) language for interacting with LLMs, such as LMQL [10], gpt-jargon [14], SudoLang [40]. When referring
to prompting frameworks, a notable challenge arises due to the rapid pace of development in the domain, making
it difficult to track and stay informed about the multitude of methods dispersed across GitHub, preprint papers,

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

Prompting Frameworks for Large Language Models: A Survey •

3

Twitter, and top conferences/journals. Furthermore, the abundance of prompting framework approaches with
varying focuses makes it challenging to systematically categorize and compare them, hindering the selection
of the most suitable product for specific needs. Therefore, there is currently a lack of but an urgent need of
systematic literature and standardized terminology for introducing and comparing these tools that are essential
for better using LLMs’ capabilities.

In this survey, we introduce the concept of ‘Prompting Framework’, and provide a comprehensive and systematic
survey of existing prompting frameworks. We present categorization, comparative analysis, and evaluation criteria
for them, assess their applicability and limitations, and provide practical recommendations for their effective
utilization for real-world LLM-enabled tasks. Additionally, we discuss some useful toolkits related to prompts
that fall beyond the scope of Prompting Frameworks. We also present recommendations for future research. In a
nutshell, we make the following main contributions:

• We introduce the concept of Prompting Frameworks that garnered attention in both academia and industry,

and provided systematic and standardized definitions and terminology.

• We categorize the existing Prompting Frameworks into 3 classes, conduct a comprehensive comparison of
their strengths and limitations across various dimensions, and provide practical recommendations. Based
on the research findings, we present the future directions of the Prompting Framework and extensively
explore its potential development and challenges in more domains.

• We conduct extensive research beyond the scope of prompting frameworks, including works and tools
related to LLMs’ prompts and task execution of prompting frameworks. We put them together in our
GitHub repository to facilitate researchers’ access and exploration for further studies.

The rest of the article is structured as follows. Section 2 presents background knowledge of the Prompting
Framework, including the characteristics of LLMs and the necessity of the Propmpting Framework. Section 3
describes the investigation, including the methodologies and results. Section 4 provides the systematic definitions
and taxonomy of Prompting Frameworks. Section 6 presents the comparison and challenges across various
dimensions of various Prompting Frameworks. Section 5 reviews prompt-based work outside the scope of the
Prompting Framework but related to LLMs. Section 7 presents the future directions of the Prompting Framework
and the potential developments and challenges in more domains.

2 BACKGROUND
In this section, we present the background of the Prompting Framework, including the reasons behind its
emergence and the pertinent terminologies. We aim to address the following aspects: 1) elucidating the concept
of LLMs by tracing their development history, and 2) explicating the current capability limitations of LLMs to
underscore the necessity for the Prompting Framework.

2.1 Trends in Language Model: from LMs to 𝐿𝐿𝑀𝑠
Early language models were predictive models based on Markov assumptions using statistical learning methods,
also known as Statistical language models (SLM) [50, 52, 80, 106]. However, due to the limitations imposed by the
fully supervised learning approach, the curse of dimensionality was inevitably a challenge. With the rise of deep
learning, researchers turned to neural networks to enhance LM’s capabilities, leading to the emergence of Neural
Language Models (NLMs) [71, 73]. NLMs aims to establish a universal neural network framework for various
natural language processing (NLP) tasks. Subsequently, the introduction and popularity of the Transformer
architecture and self-attention mechanism [111] gave rise to a series of task-agnostic pre-trained models, such
as BERT and GPT, called Pre-trained language models (PLM), which promoted the emergence of the “pre-train,
fine-tune" paradigm [60]. PLMs have exhibited remarkable performance improvements across a wide range of
NLP tasks [33, 55, 63, 94].

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

4

• Xiaoxia Liu, Jingyi Wang, Jun Sun, Xiaohan Yuan, Guoliang Dong, Peng Di, Wenhai Wang, and Dongxia Wang*

Fig. 1. The timeline of representative prompting frameworks.

To further explore the performance of LMs, researchers have continuously increased the scale of model
parameters, the trend has shifted towards downstream tasks actively adapting to pre-trained models. The paradigm
of “Pre-train, Prompt, Predict" became mainstream [60]. Prompts are an important medium for interaction with
Language Models, usually in text form. In this process, the augmented models not only exhibit better performance
on various NLP tasks but also demonstrate remarkable “emergent abilities" [119], which were previously unseen
in smaller PLMs with similar architectures. For instance, ChatGPT can mimic human language style and logical
reasoning and also demonstrates outstanding contextual comprehension, which was absent in previous models
like GPT-2. Based on this new capability distinction, researchers refer to these emerging PLMs with hundreds of
billions of parameters as Large Language Models (LLMs) [47, 51, 120], such as ChatGPT, and GPT-4 [82]. With
this advancement, language models have completed the leap from LMs to LLMs and inspiring new prospects for
artificial general intelligence (AGI).

2.2 LLMs still “Brains in a Vat": Limitations and Mitigation
Analogous to humans, LLMs can be perceived as the brains of artificial intelligence systems, responsible for
perceiving instructional information and generating and controlling actions. Although there has been evidence
of “Emergent Abilities" [74, 117, 119, 126] in LLMs, which refers to the abilities that emerge in large-scale models
but have not been observed in smaller models and can be primarily categorized into four aspects: in-context
learning[36, 75, 115, 121], reasoning for complex content [56, 120, 136], instruction following [28, 85, 88, 116],
and creative capacity [16, 37, 133, 134].

However, the capacity limitations of LLMs cannot be ignored. Firstly, LLMs suffer from temporal lag in their
training data, such as ChatGPT’s latest training data being limited to September 2021 (at the time of paper writing).
LLMs are unable to access real-time information and trends, and they may struggle to accurately comprehend
specific terminology or domain-specific knowledge, occasionally leading to incomplete or erroneous responses,
even illusions [17, 19, 25, 32, 41, 57, 113]. Additionally, LLMs are bound by strict limitations on the number of
tokens they can process during interactions, severely restricting the amount of contextual information they can

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

Prompting Frameworks for Large Language Models: A Survey •

5

take in and process [9, 15, 127, 131]. Secondly, LLMs are incapable of direct interaction with external expert
models, such as utilizing search engines, querying databases, and invoking external tools, or APIs, which limits
their usability [68, 93, 135]. Furthermore, the majority of LLMs are offered as paid APIs, potentially imposing
financial burdens on individuals, organizations, and projects with limited resources when dealing with large-scale
or frequent requests [23, 84].

Based on the above challenges, it is thus desirable to overcome these barriers by bridging the gap between
LLMs and external applications. The adoption of Prompting Frameworks, such as Langchain and semantic kernel,
becomes imperative [22, 76]. These frameworks not only enable LLMs to stay constantly exposed to emerging
information but also enable the processing of long texts and documents, and facilitate seamless integration with
external applications.

3 SURVEY OVERVIEW
In this section, we provide a comprehensive description of our survey process. The domains of LLMs and associated
technologies are currently undergoing an unprecedented phase of rapid development. As a consequence, the
landscape of relevant research and achievements is characterized by its dispersed nature. Many contributions
have yet to be formally published in traditional academic journals or conferences. Instead, they are often
found on platforms like arXiv or as open-source toolkits available on GitHub. Some noteworthy developments
exist primarily within online communities on platforms such as Twitter, GitHub, and Discord, lacking formal
documentation. Furthermore, there is a notable absence of comprehensive review literature in the field, resulting
in a scarcity of established academic terminology and official definitions.

Our exploration of prompting frameworks begins with an in-depth examination of LangChain, recognized as one
of the most influential frameworks in this domain. We start by delving into LangChain’s official description, which
emphasizes the concept of “Building applications with Large Language Models (LLMs) through composability."
This primary phase of our research seeks to establish a foundational understanding of the terminology and
concepts central to these frameworks. We scrutinize and analyze terms such as “frameworks," “tools," “Agent,"
“Large Model," “prompt," and “toolkits." These keywords are thoughtfully selected to ensure an encompassing
perspective, allowing us to include a wide range of relevant materials and resources.

In our pursuit of a comprehensive examination, we conduct multiple rounds of keyword searches across diverse
platforms. This includes exhaustive searches on prominent repositories like GitHub and scholarly databases
such as arXiv. Additionally, we extend our exploration to encompass reputable conferences and journals within
the fields of artificial intelligence (AI) and natural language processing (NLP). These additional searches ensure
that we are not only capturing the latest developments but also accessing academic and research-oriented
materials of significance. Throughout this research process, our focus is to identify, collect, and analyze relevant
materials. In total, we amass substantial works comprising 49 open-source projects available on GitHub and a
significant number of academic papers. This methodical approach and rigorous examination of resources form the
cornerstone of our research into prompting frameworks, facilitating a thorough and well-rounded exploration.
Subsequently, our investigation delves into a meticulous and systematic assessment of the 49 works under
scrutiny. This comprehensive evaluation begins with an exhaustive review of their technical documentation,
wherein we scrutinize the minutiae of each work’s conceptual underpinnings, functional implementations, and
crucial code segments. We embark on an in-depth exploration, configuring and pragmatically employing these
tools to conduct a scientific and methodical analysis, evaluating their performance, efficiency, and applicability.
In detail, we conduct extensive testing and research, which involve running all the test cases provided in the
technical documentation and manually creating numerous more detailed test cases that better reflect real-world
requirements. Following the fundamental procedures of software testing, we begin with unit testing of each
individual module within the framework. Subsequently, we proceed to performance testing of modules assembled

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

6

• Xiaoxia Liu, Jingyi Wang, Jun Sun, Xiaohan Yuan, Guoliang Dong, Peng Di, Wenhai Wang, and Dongxia Wang*

according to requirements and standards in complex applications, thus accomplishing integration testing. Finally,
we conduct comprehensive system testing to validate and evaluate the capabilities claimed in these tasks, while
also organizing aspects related to user experience.

Finally, this multi-faceted examination enables us to identify the merits and limitations of each work, providing
us with a nuanced understanding of their capabilities and relevance to the overarching objectives of our survey.
Following this rigorous assessment, we judiciously select approximately 30 works that not only conform to the
conceptual prerequisites of the prompting framework but also stand out in the field. These selected works are
chosen to be included in our survey to ensure a comprehensive and representative illustration of the burgeoning
and dynamically evolving landscape of the prompting framework, which significantly shapes interactions between
individuals and LLMs.

Fig. 2. The workflow for facilitating interactions between LLMs and external entities using the Prompting Framework.

4 STATE-OF-THE-ART PROMPTING FRAMEWORK
In Sec.2, we analyze the current constraints and limitations of LLMs in practical applications. Despite these
limitations, LLMs exhibit remarkable emergence abilities. By combining LLMs with the Prompting Framework,
the limitations of LLMs can be mitigated to some extent, enabling the realization of more astonishing capabilities.
Therefore, in this section, we provide a systematic and comprehensive definition and description of the Prompting
Framework, which is crucial to break down the application barriers of LLMs and empowers them as critical tools
in real-world scenarios. We also classify the state-of-the-art Prompting Frameworks to provide a systematic
review of various approaches.

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

ImageTextVideoSpeechDocumentAzureHugging FaceClaudePaLMMetaEducationLegalAdvertising and MarketingFinanceScientific ResearchNews and MediaHealthcareOpenAIRawOutputConversationQuestionTaskCreativeExpert ModelDatabaseMathematical ToolsDocument ManagersSearch EnginesSocial MediaMultimodal Process ToolsOthersAgentMechanical Equipment..................Retail and E-commerceVehicleData LevelBaseLevelExecuteLevelServiceLevelPrompting FrameworkData LoadingData Process /Data to PromptAccess andConfigurationCoordinate Data TransferCoordinate and Respond to Configuration and Invocationbased on Specific Real-world TasksTask SchedulingExtend the Functionality of Different General In MoreDomain-Targeted MannerOperational Results or Intermediate DataControlFlowDataFlowData Propagation IterativelyInter-layer CommunicationIntra-layer SchedulingPrompting Frameworks for Large Language Models: A Survey •

7

4.1 Conceptualization
Prompt typically serves as a crucial medium for interacting with LLMs, taking the form of textual content. A
Framework is a general and extensible infrastructure that provides a structured approach and a set of guidelines.
Consequently, we provide the following definition of the Prompting Framework:

Prompting Framework (PF) is the framework for managing, simplifying, and facilitating interaction with
large language models, which adheres to four essential properties: modularity, abstraction, extensibility,
and standardization.

Specifically, modularity refers to breaking down the structure of the prompting framework into independent
modules for easy code management and reusability; abstraction refers to providing high-level, simplified interfaces
to hide complex implementation details in the prompting framework’s design; extensibility inclines to allow
users to customize and extend framework functionalities as needed, and standardization refers to consistency in
development to improve code maintainability and readability.

We categorize the workflow for facilitating interactions between LLMs and external entities using the Prompting
Framework into four hierarchical layers, arranged from bottom to top as Data Level, Base Level, Execute Level, and
Service Level. The Prompting Framework serves as the facilitator for inter-layer communication and intra-layer
scheduling. It is important to note that the interactions between different levels are non-linear. In the course of a
single task execution, data may iteratively propagate between various layers to accomplish intricate operations.
The following is a detailed exposition of these four levels and the role played by the prompting framework within
them:

4.1.1 Data Level. The Data Level is typically the foundational layer, serving as the most direct interface with the
external environment. The Data Level primarily handles tasks such as data transmission and preprocessing, while
being responsible for managing interactions with external data sources, such as databases or file systems. Within
this process, the prompting framework plays a pivotal role in achieving a unified approach to dealing with various
types of data, including text, images, videos, structured data, and documents. Simultaneously, the prompting
framework has the capability to transform raw, unprocessed input into well-crafted prompts tailored to specific
tasks or requirements, including question-answering, dialogue, and reasoning, facilitating more efficient and
effective interactions with high-performance models at the Base Level.

4.1.2 Base Level. The Base Level operates as a computational hub situated between the data level and the execute
level, serving as the analogical equivalent of the human brain or, in a computer analogy, the CPU. The Base Level
primarily takes responsibility for the management of LLMs as the computational and control center, involving
the reception and comprehension of instructions, execution of commands, and conducting various computations,
which supports knowledge management and decision-making processes. Throughout this process, the prompting
framework plays a critical role in coordinating data transfer and task scheduling. Furthermore, the prompting
framework facilitates user-friendly access and flexible configuration of LLMs and can even autonomously select
the most suitable LLMs for specific tasks.

4.1.3 Execute Level. The Execute Level constitutes a critical component of the business logic and is responsible for
interacting with LLMs to accomplish specific real-world tasks. The Execute Level maintains communication with
LLMs through the prompting framework collaboratively, and based on this, constructs tasks and takes appropriate
actions based on the interactive information obtained from the prompting framework, and coordinates and
responds to the configuration and invocation of models in alignment with LLMs to achieve the final completion
of tasks. The Execute Level represents the terminal stage of task execution and primarily consists of three parts.

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

8

• Xiaoxia Liu, Jingyi Wang, Jun Sun, Xiaohan Yuan, Guoliang Dong, Peng Di, Wenhai Wang, and Dongxia Wang*

Table 1. Representative Works of Prompting Frameworks.

Category

Subcategory

The Shell of LLMs
(LLM-SH)

Universal LLM-SH

Domain-Specific LLM-SH

Language for Interaction with LLMs
(LLM-LNG)

Programming LLM-LNG

Pseudocode LLM-LNG

Output Restrictors of LLMs
(LLM-RSTR)

Content LLM-RSTR

Structure LLM-RSTR

Representative Works
Haystack [90]
Semantic Kernel [112]
LangChain [20]
Griptape [44]
PromptFlow [48]
LLM-chain [105]
LinGoose [45]
LLMStack [26]
OpenDAN [83]
Hyv [107]
LlamaIndex [59]
embedchain [104]
AgentVerse [24]
SuperAGI [110]
Txtai [67]
AutoChain [42]
TermGPT [101]
Botpress [12]
LQML [10]
PromptLang [99]
SudoLang [40]
gpt-jargon [14]
NeMo-Guardrails [79]
Guardrails [102]
Guidance [69]
Promptify [86]
ReLLM [97]
TypeChat [70]

The first part involves directly utilizing the Raw Output of LLMs from the Base Level to complete tasks without
external assistance, representing the simplest business workflow. The second part entails selecting and invoking
one or several external specialized models based on the interactive information from the prompting framework
to handle aspects of task execution beyond the capabilities of LLMs, enabling the achievement of relatively
complex tasks. The third part involves the coordination and integration of LLMs with higher-order models, such
as interacting with various mechanical models (robotic arms, machines, vehicles, etc.) to realize LLM-based
embodied intelligence or engaging with different types of agents to create LLM-based intelligent autonomous
agents, further advancing the progress of Artificial General Intelligence (AGI).

Service Level. The Service Level resides at the top tier of the entire business workflow and is responsible
4.1.4
for facilitating the management, scheduling, and integration of advanced tasks within specific domains, in
coordination with the prompting framework. Service Level extends the functionality of different general in a
more targeted manner by interacting with the prompting framework, particularly in critical domains such as
education, healthcare, e-commerce, law, and finance.

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

Prompting Frameworks for Large Language Models: A Survey •

9

4.2 Taxonomy of Prompting Framework
Taking into consideration the technical features, design objectives, and application scenarios, the current prompt-
ing framework can be broadly covered by three types: The Shell of LLMs (LLM-SH), Language for Interaction with
LLMs (LLM-LNG), and Output Restrictors of LLMs (LLM-RSTR). In this section, we will elucidate the reasons for
this classification and provide a detailed description of the characteristics and distinctions among these various
types of prompting frameworks. The rationale behind designing the prompting framework is to facilitate the
interaction between LLMs and the external world, and different types of prompting frameworks manifest this
enhancement effect from different perspectives. LLM-SH functions are much like a shell or interface layer in
computer systems, emphasizing interaction with LLMs by facilitating their engagement with highly capable third
parties, thereby enabling stronger interaction between LLMs, users, and external models. LLM-LNG, on the other
hand, is designed to create a language (programming or pseudo-language) for interaction with LLMs, focusing
on providing users with a more concise and compact interaction channel. LLM-RSTR, meanwhile, achieves
controlled generation by emphasizing interactions with LLMs that are of higher quality and better aligned with
requirements. Furthermore, in the practical use of these tools, we have found that these three types of prompting
frameworks are often compatible with each other. In other words, depending on the requirements, multiple
different categories of prompting framework can be used in parallel within the same task-solving process.

4.2.1 The Shell of LLMs (LLM-SH). The shell of LLMs (LLM-SH) is a type of prompting framework aimed at
enhancing the capabilities of LLMs by enabling them to access various external tools and knowledge sources. In
traditional terms, a shell is often associated with an operating system, where the operating system’s shell serves
as a command-line interpreter that receives user input commands, interprets them, and passes them on to the
operating system for execution, facilitating users in efficiently and comprehensively utilizing the functionality
of the operating system. In other words, a shell can be viewed as a layer of encapsulation over the kernel,
bridging the communication gap between commands and applications. Similarly, the design motivation behind
LLM-SH, as a prompting framework, is to expand the action potential of LLMs. Specifically, with the assistance
of LLM-SH, LLMs can not only accomplish conventional NLP tasks such as question answering, sentiment
analysis, and information retrieval, but also higher-level functions across various domains including natural
sciences, healthcare, education, finance, computer science, which encompass image processing and analysis,
object detection, mathematical computations, database access, utilizing search engines, code comprehension and
generation, social media posting, weather forecasting, and more. The LLM-SH simplifies complex interactions
between LLMs and the external world, with a focus on improving their usability, universality, and scalability.
LLM-SH also supports customization, allowing configuration and tailoring to specific needs and requirements for
different application scenarios and specific domains.

In Tab. 1, we provide classification and representative works according to categories. It is worth noting that
we include many instances of “Agent", but this paper primarily investigates the Agent framework rather than
individual Agents. The distinction lies in the fact that LLMs-based Agents, exemplified by AutoGPT and BabyAGI
[77], emphasize the formulation of plans based on user-defined goals and the autonomous execution of these plans,
whose main contributions lie in task acceptance, comprehension, automated decision-making, and execution
processes. On the other hand, Agent frameworks, exemplified by SuperAGI [110] and AgentVerse [24] in the
table, focus on customizing and building, managing, and running Autonomous Agents according to user-specific
requirements. In simple terms, LLMs-based Agents are products primarily geared towards usage, whereas Agent
frameworks serve as auxiliary tools to assist users in assembling and maintaining Agents, with an emphasis on
construction.

There are two primary forms within LLM-SH. One is designed to support a wide range of applications and
domains and is referred to as Universal LLM-SH. The other is more specialized and focused on a specific domain,

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

10

• Xiaoxia Liu, Jingyi Wang, Jun Sun, Xiaohan Yuan, Guoliang Dong, Peng Di, Wenhai Wang, and Dongxia Wang*

such as Agent building and maintenance, data processing, or chat-bot building, and is known as Domain-Specific
LLM-SH.

Universal LLM-SH is designed with the intention of accommodating a wide range of application scenarios
and domains, offering extensive functionality and flexibility to meet the diverse needs of users, which typically
possess higher generality and scalability. Representative works include Haystack, Semantic Kernel, LangChain,
Griptape [44], PromptFlow [48], LLM-chain [105], LinGoose [45], LLMStack [26], OpenDAN [83], Hyv [107].

Domain-Specific LLM-SH is specifically designed for particular domains or application scenarios. They are
typically finely tuned and optimized for the requirements of that domain, often achieving better performance
and higher efficiency in completing specific tasks. Representative works include LlamaIndex [59] and Txtai [67],
which are data frameworks designed to assist in building LLM-based applications. For building and managing
LLM-based autonomous agents, we have AgentVerse [24] and SuperAGI [110], along with AutoChain [42]. In the
domain of creating LLM-powered bots, there are embedchain [104] and botpress [12]. Additionally, for giving
LLMs the capability to plan and execute terminal commands, there is TermGPT [101].

4.2.2 Language for Interaction with LLMs (LLM-LNG). Language for Interaction with LLMs (LLM-LNG) is
an innovative type of prompting framework designed to facilitate more concise, direct, and compact interactions
with LLMs by introducing a specialized language for programming.

Prompts serve as crucial intermediaries for interacting with LLMs and are typically presented in the form
of natural language text. However, the capabilities of pure natural language text are limited and can increase
complexity and cost when dealing with advanced tasks, sometimes even failing to yield accurate outputs. In
contrast to purely natural language prompts, languages that integrate both natural language and programming
logic are more structured, concise, and compact. They not only enhance reasoning performance but also provide
better support for various prompting methods, such as chain-of-thought reasoning and decision trees. Additionally,
they can offer improved support for control flow.

LLM-LNG comes in two primary forms: Programming LLM-LNG, which involves interactions with LLMs using
programming languages, and Pseudocode LLM-LNG, which interacts with LLMs using a pseudo-code language.
The main distinction between the two lies in their nature. Programming LLM-LNG belongs to the domain of
programming languages and adheres to complex syntax rules and structures, which require compliance with
specific syntax specifications to ensure program correctness and often require compilation or interpretation
to transform it into executable code. On the other hand, Pseudocode LLM-LNG provides a simpler and more
intuitive way of describing algorithms, combining natural language and structured coding with fewer formal
constraints. As a result, Programming LLM-LNG, due to the interpretation and compilation process, tends to be
more powerful in handling tasks and control flow. However, it also entails a steeper learning curve compared to
Pseudocode LLM-LNG. Each approach has its own advantages.

Programming LLM-LNG primarily involves designing a new programmable language for interacting with
LLMs by simulating the syntax and architecture of existing programming languages. Given the significant overlap
between user interactions with LLMs and the functionality of query languages, combining query language
and language model prompts is a logical approach. This expansion transforms prompts from pure text-based
prompts (natural language) to a combination of text prompts and scripts (natural language combined with
programming language), enhancing the intuitiveness of interactions. In compound prompts that blend natural
language with the programming language, constraints, and control flow are embedded into the instruction parsing
and output parsing processes of LLMs through structured query languages. This functionality aims to streamline
the reasoning process while reducing calls to resource-intensive underlying LLMs. Notable products in this
category include LMQL [10].

Pseudocode LLM-LNG is a more open-ended form that flexibly combines natural language with structured
coding, relying on the inherent capabilities of LLMs. Pseudocode is a wonderful method for outlining programs

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

Prompting Frameworks for Large Language Models: A Survey •

11

informally in natural language, without the constraints of specific syntax, which is like sketching out your ideas
before diving into detailed coding. The design of Pseudocode LLM-LNG is driven by the need to unlock the full
potential of LLMs, which possess strong capabilities but are hindered by inconvenient interactions or inaccurate
prompts. Therefore, Pseudocode LLM-LNG offers a standardized structure and syntax that is easy to understand
and interpret. It provides feasibility-verified template use cases or background explanations for communication
with LLMs, combining natural language with simple coding conventions. Representative works in this category
include PromptLang [99], SudoLang [40], and gpt-jargon [14].

4.2.3 Output Restrictors of LLMs (LLM-RSTR). Output Restrictors of LLMs (LLM-RSTR) are a type of
prompting framework designed to enable controlled generation by LLMs. The controlled generation problem
with LLMs pertains to how to ensure that the generated text meets specific requirements, constraints, or demands,
adapting to various application scenarios and professional domains. This involves control over multiple aspects
such as semantic content, output structure, and semantic style. Currently, due to the uncontrolled nature of
LLMs, the generated natural language text tends to be unstructured. Additionally, generated text may contain
potential risks like bias, misinformation, or inappropriate content. LLMs also struggle with off-topic responses and
maintaining consistency with predefined requirements. However, the application of LLM-RSTR can effectively
alleviate these issues. LLM-RSTR primarily focuses on controlled generation from two perspectives: Content
Control, referred to as Content LLM-RSTR, and Structure Control, referred to as Structure LLM-RSTR.

Content LLM-RSTR focuses on achieving controlled generation by LLMs in three main aspects: privacy
protection, security, and alignment with the topic and accuracy. As for privacy protection, Content LLM-RSTR
ensures that user-provided personal or sensitive information is not leaked or misused. Security control aims
to filter out unsafe, or dangerous content such as societal and cultural biases about gender, race, politics, and
inappropriate or offensive content, and also prevents the generation of false or misleading information, thereby
maintaining the accuracy and credibility of the generated content. The generated text should align with the user’s
or application’s topic or requirements to ensure the generated content is useful. Additionally, text generation
needs to maintain high accuracy, especially in specific domain applications such as medicine, law, or science.
Representative works in this category include NeMo-Guardrails [79] and Guardrails [102].

Structure LLM-RSTR plays a critical role in information processing, data management, and decision support,
enabling both computers and humans to better understand and utilize the information, for tasks such as database
management, search engine optimization, natural language processing (NLP), information extraction, data mining,
and analysis. Unstructured original output from LLMs is challenging to use in business or other applications.
Therefore, constraining and specifying the desired output text format is crucial. The most intuitive way to obtain
structured text as output from LLMs is to write extensive and cumbersome tutorials and templates to instruct
LLMs on what format the output should take. However, this is a time-consuming and complex process. The
design of Structure LLM-RSTR aims to address this issue, allowing users to interact with LLMs in a simpler, more
direct manner, and obtain structured outputs that are clear, easier to handle, and analyze. Representative works
in this category include Guidance, Promptify [86], ReLLM [97], and TypeChat [70].

4.3 Crucial Component in the Construction of Prompting Framework
After elucidating the concept of the prompting framework and conducting a comparative analysis, in this
section, we introduce one of the pivotal concerns within the prompting framework—specifically, the essential
components required when constructing a prompting framework. Given the rapid development of both LLMs
and the prompting framework itself, this field has not only given rise to numerous emerging technologies but
has also reactivated many traditional techniques.

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

12

• Xiaoxia Liu, Jingyi Wang, Jun Sun, Xiaohan Yuan, Guoliang Dong, Peng Di, Wenhai Wang, and Dongxia Wang*

4.3.1 Vector Database. In the midst of the ongoing AIGC revolution, a particular challenge lies in the capability
of large-scale storage and querying of unstructured data, such as images, videos, and text. Vector databases
offer developers the means to handle unstructured data in the form of vector embeddings, which becomes
especially crucial for the utilization and expansion of LLMs, for example, tools like OpenAI’s Retrieval plugin
rely on vector databases to assist users in retrieving relevant document excerpts from the data sources. A vector
database is a specialized database designed for storing and managing vector data. Vector data refers to data
composed of multiple numerical values, often representing specific features or attributes. Vectorization is the
process of transforming discrete variables, such as images and text, into continuous vector spaces. For example,
different-sized or content images can be mapped into vectors within the same space, or various lengths of text can
be mapped to a common vector space. In this space, adjacent vectors carry semantically similar meanings, and
the vector space is commonly referred to as the embedding space, the generated vectors are known as embedding
vectors or vector embeddings. The primary characteristics of vector databases include efficient storage and
querying of large-scale vector data. Typically, they employ queries based on vector similarity, retrieving data
based on the similarity between vectors. This querying approach finds applications in various scenarios like
image search, music recommendation, and text classification.

Vector databases depend on three key elements: vectorization (encoding), data structure, and distance cal-
culation. The quality of vectorization determines the upper limit of vector database performance, yet current
vectorization processes lack universality due to their strong dependence on data types. Properly constructing
data structures to manage vectors ensures computational and retrieval efficiency, which determines the lower
limit of vector database performance. Reasonable distance calculation between vectors can minimize resource
consumption.

In recent years, there has been a proliferation of specialized database products. For instance, Milvus[114] is
considered the world’s first true vector database product, with over 1000 enterprise users worldwide, making it
one of the most popular open-source vector databases globally. Pinecone[91], designed for machine learning
applications, offers speed, scalability, and support for various machine learning algorithms. Pinecone is also a
partner of OpenAI, and users can generate language embeddings using OpenAI’s Embedding API. Weaviate[34],
a vector database, can store as many as billions of vectors. Additionally, Weaviate has introduced a Plug-in for
ChatGPT, which has received recognition from OpenAI. The main distinction between Weaviate and Pinecone
lies in how they manage services. Pinecone handles data storage and resource management fully for users,
often in conjunction with AWS or GCP hosting. In contrast, Weaviate allows users to self-host their data while
providing supportive operations and services. For users who value retaining control and not relinquishing their
data entirely, Weaviate offers greater flexibility but may come with a relatively higher time cost.

4.3.2 Cache for LLMs. Fundamentally, every form of computation necessitates storage. Computation and
storage represent the two fundamental abstractions, yet they are mutually convertible: storage can be exchanged
for computation, and vice versa. Achieving an optimal trade-off is crucial in enhancing the input-output ratio.
Whether dealing with large-scale or small-scale models, they fundamentally encode global knowledge and
operational rules, serving as a compression of all human data. However, embedding all data into LLMs is
challenging. For instance, some assert that ChatGPT serves as a highly efficient compression encoding, albeit not
achieving lossless compression, in which the process inevitably introduces entropy reduction and information loss.
Encoding all information into neural networks results in an excessively bulky model with an enormous parameter
scale, leading to sluggish performance. Therefore, complete integration is unfeasible, implying the potential
necessity for external storage. Similar situations exist in computer architecture, where the CPU incorporates
on-chip SRAM, typically constrained in size due to the significantly higher cost of on-chip storage (100 times
more expensive than DRAM and 10,000 times more expensive than disk storage). Neural networks function as
on-chip storage for large models, with larger-scale models possessing more on-chip storage. However, utilizing

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

Prompting Frameworks for Large Language Models: A Survey •

13

neural networks for data storage proves costly, causing a rapid escalation in network scale. Hence, large models
require a more efficient data storage method beyond neural networks, known as memory of LLMs.

For instance, GPTCache[139] is a tool specifically designed to build semantic caches for storing LLMs’ responses.
It employs a modular design, including six main modules: LLM adapter, embedding generator, cache storage,
vector store, cache manager, and similarity evaluator. The system offers multiple implementation options for each
module, allowing users to customize their semantic cache to meet specific needs. Zep is a long-term memory
store designed for building conversational LLM applications, which supports storing, summarizing, embedding,
indexing, and enriching the history of LLM applications/chatbots. Zep[132] enables long-term memory persistence,
automatic summarization based on configurable message windows, vector search, and automatic memory token
counting.

4.4 Typical Applications of Prompting Framework
In this section, we elucidate some typical applications of the prompting framework throughout the entire lifecycle
of LLMs. These applications, situated at the closest proximity to the user at the application layer, are poised to
offer boundless insights and inspiration for future developers and users.

Integrated Application Platform. The initial goal of constructing the prompting framework was
4.4.1
to reduce the interaction barriers with LLMs and facilitate the development of LLM applications. Therefore,
after addressing prototype issues, the subsequent challenge is to assist these applications in transitioning to
practical development while ensuring implementation in a reliable and maintainable manner. Debugging, testing,
evaluating, and monitoring the intricate data and control flow within LLM systems are crucial steps in this
process, which ensures the robust deployment of LLMs in real-world production scenarios is of paramount
importance. Consequently, considering both immediate requirements and future strategic objectives, integrated
application platforms emerge as a typical application of the prompting framework.

For example, The newly developed LangSmith [20] by LangChain developers introduces innovative features
centered around five core pillars: debugging, testing, evaluation, monitoring, and usage metrics. LangSmith
facilitates the execution of these operations through a simple and intuitive user interface, significantly lowering the
barriers for developers without a software background. From a numerical perspective, many features of LLMs lack
intuitiveness, making visual representation essential. We observe that a thoughtfully designed user interface can
expedite user prototyping and work, as handling everything through code alone can be cumbersome. Furthermore,
visualizing the processes and intricate command chains of LLM systems proves valuable in understanding the
reasons behind specific outputs. As users construct more complex workflows, comprehending how queries
traverse different processes becomes challenging. Therefore, a user-friendly interface to visualize these processes
and record historical data represents a forward-looking innovative application.

4.4.2 LLM-based Agent. For a long time, autonomous agents have been a significant research topic. However,
before the advent of LLMs and related technologies, limitations in training data, training methods, and interaction
with the environment severely constrained the capabilities of agents. Consequently, agents struggled to make
decisions similar to humans and achieve remarkable performance. However, with the current prevalence of LLMs
and their outstanding capabilities, LLM-based autonomous agents have demonstrated immense potential in task
processing and autonomous decision-making.

In a broad sense, an agent refers to any system capable of thinking, interacting with the environment, operating
independently, and collaborating with other entities. In theory, given any objective, an agent should be able to
achieve it automatically. LLM-based Agents belong to AI systems that autonomously generate sub-agents, which
can execute tasks independently based on user requirements without the user’s direct intervention, following
the basic three sub-steps used by people to solve various problems: perception, decision-making, and action.

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

14

• Xiaoxia Liu, Jingyi Wang, Jun Sun, Xiaohan Yuan, Guoliang Dong, Peng Di, Wenhai Wang, and Dongxia Wang*

LLM-based Agents can handle tasks ranging from daily event analysis, marketing plan generation, and code
programming, to mathematical computations, among others. If ChatGPT follows user instructions, doing what
the user tells it to do, then an LLM-based Agent acts on what it deems should be done. In other words, LLM-
based Agents demonstrate a potential form of integration between LLMs and prompting frameworks. However,
it’s important to note that this is still an experimental concept and not a fully realized commercial product.
Currently, LLM-based autonomous agents typically follow a unified architecture, consisting of four main modules:
a configuration module representing agent attributes, a memory module for storing historical information, a
planning module for formulating future action strategies, and an action module for executing plan decisions.

AutoGPT [103], released on GitHub by Significant Gravitas, is a well-known autonomous agent capable of
executing actions based on LLMs’ autonomous decision results and external resources. AutoGPT uses a cyclic
evaluation strategy to assess the degree of goal achievement in real-time, determining whether a task is complete.
AutoGPT is mainly composed of three parts: task distribution, autonomous execution, and result output. The
autonomous execution module is the core of AutoGPT. Currently, AutoGPT can perform basic tasks such as
internet searches and information collection, long-term and short-term memory management, access to common
websites and platforms, and extension through plugins. HuggingGPT [122], developed by Zhejiang University and
Microsoft Research Asia, is a collaborative system that connects LLMs with the ML community (HuggingFace). It
can handle inputs from various modalities and address a wide range of complex AI tasks. In essence, HuggingGPT
takes introductions to all models on the HuggingFace community as input and runs them through models. Then,
based on the user’s input question, it parses matches and decides which model to use for solving the task. Similarly,
HuggingGPT’s workflow comprises four stages: task planning, model selection, task execution, and response
generation, which aligns closely with that of AutoGPT. In addition, AgentGPT [96] is a web-based solution
that allows for the configuration and deployment of autonomous AI agents, facilitating interactive experiences
with web users. CAMEL [3], short for “Communicative Agents for ’Mind’ Exploration of Large Scale Language
Models," implements a novel role-playing agent. GPTRPG [39] combines game design with large language models,
enabling the deployment of multiple agents to autonomously participate in online games by embedding AI agents
into the roles within the game environment using the OpenAI API.

5 RELATED PROMPTING TOOLS
In this section, we provide an extensive overview of prominent prompting tools that contribute to generating
higher-quality prompts or achieving advanced functionality through prompts. Since these tools do note possess
all four fundamental characteristics of prompting frameworks, namely modularity, abstraction, scalability, and
standardization, they are not classified as prompting frameworks. Nevertheless, the problems they address and
the functionalities they enable are also significant for future interactions with LLMs. Additionally, we introduce
some auxiliary tools that play a vital role in task completion of prompting frameworks. Links to these tools are
also organized in our GitHub repository.

Prompt is a powerful tool that enhances the flexibility and controllability of large language models (LLMs),
making them applicable across various domains. Through clever design and utilization of prompts, users can
guide the model to generate desired text, resulting in improved performance and effectiveness across various
tasks. It can be stated that a well-crafted prompt can significantly boost the productivity of LLMs. The significance
of predefined prompt templates, example libraries, or prompt optimization tools that template user-inputted
prompts for large language models lies in their ability to not only lower technical barriers, enabling non-technical
individuals to easily interact with the model, but also enhance interaction efficiency. In other words, users can
select suitable prompts from existing templates without the need to write their own from scratch. Furthermore,
since templates are designed and tested, they tend to be more precise and reliable, reducing errors caused by
unclear or vague user instructions.

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

Prompting Frameworks for Large Language Models: A Survey •

15

Prompt’s Template Library. Awesome ChatGPT Prompts [1] is an open-source website and application
created by JavaScript developer Fatih Kadir Akın, which contains over 160 prompt templates for ChatGPT,
allowing it to mimic a Linux terminal, JavaScript console, Excel page, and more. These prompts have been
collected from excellent real-world use cases. LangGPT [130] is designed to write high-quality prompts in
a structured, templated manner. It not only provides templates but also supports variable configuration and
references based on templates. PromptSource [4] is a toolkit for creating, sharing, and using natural language
prompts. PromptSource allows for the use of thousands of existing and newly created prompts, which are stored
in separate structured files and written in a simple template language called Jinja.

Optimizer for Prompts. OpenPrompt [35] provides a standardized, flexible, and extensible framework for
deploying prompt-based learning pipelines. It supports existing prompt learning methods and allows for the
design of custom prompt learning tasks. HumanPrompt [124] is a framework that makes it easier for humans
to design, manage, share, and use prompts and prompting methods. InstructZero [21] aims to optimize poorly
phrased prompts provided by users to LLMs, transforming them into well-structured and compliant prompts. The
optimization process primarily aligns humans with LLMs, rather than fine-tuning LLMs to align with humans, as
in instruction fine-tuning.

Evaluation of LLMs. Evaluating LLMs has always been a crucial topic to ensure their reliability, safety,
usability, and compliance while helping identify potential issues and improvement areas [5, 49, 58, 92]. Evals
[81] is a framework for evaluating LLMs and LLM systems and serves as an open-source registry of benchmarks.
Evals simplifies the process of constructing evaluations with minimal code while being straightforward to
use. PromptBench [138] is a framework for robustness evaluations of large language models under adversarial
prompts, which facilitates examining and analyzing interactions between large language models and various
prompts, providing a convenient infrastructure for simulating black-box adversarial prompt attacks and evaluating
performance. PromptInject [89] is a framework that modularly assembles prompts to provide quantitative analysis
of LLMs’ robustness against adversarial prompt attacks.

Fig. 3. The dimensions and metrics for comparative analysis.

6 COMPARISONS AND CHALLENGES
In this section, we provide a comparison of existing prompting frameworks from various dimensions and analyze
the challenges that prompting frameworks encounter in terms of development, practical implementation, and

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

16

• Xiaoxia Liu, Jingyi Wang, Jun Sun, Xiaohan Yuan, Guoliang Dong, Peng Di, Wenhai Wang, and Dongxia Wang*

further advancements. The dimensions and metrics for conducting the comparative analysis are shown in Fig.
3, and the detailed capability matrix based on the dimensions and metrics above of the mainstream prompting
framework is illustrated in Fig. 4.

Fig. 4. The capability matrix of representative prompting frameworks.

6.1 Comparative Analysis of Prompting Frameworks
We have examined the three macro dimensions of compatibility, capabilities and features, as well as documentation
and support. Within these dimensions, we have focused on more detailed key issues, providing a comprehensive
analysis and comparison of existing prompting frameworks, which offer systematic experiences and guidelines
for developers and users in their practical adoption of prompting frameworks and for further advancements.

6.1.1 Compatibility. Compatibility refers to the adaptability and interoperability of systems, software, hard-
ware, or other components in various environments or conditions. We primarily investigate the compatibility of
the prompting framework with programming languages and its compatibility with LLMs.

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

Handling Unconventional Input Content Exceeding LLM’s Token LimitNon-textual Contents BeyondLLMs’Capabilities Beneficial Effects of the ReasoningAcceleration of ReasoningRefining Outputs to Stipulated CriteriaControl of LLMs OutputsOutput’s ContentOutput’s StructureCapability of Utilizing External ToolsMaintenance of HistoricalInformationImpact of Invocation CostsDecrease LLMs Invocation FrequencyDecrease Token Processing During LLMs InvocationPrompting FrameworkLangChain!✅⛔✅✅✅✅✅✅Haystack✅!✅✅✅✅⛔✅✅Semantic Kernel✅!✅✅✅✅⛔✅✅GriptapePromptFlowLLM-chainLinGooseLLMStackOpenDANHyvUniversal LLM-SH!!!✅!✅✅✅✅⛔✅✅!✅⛔✅✅✅✅⛔✅✅!✅✅!✅✅✅✅⛔✅✅!✅⛔✅✅✅✅✅✅!!✅⛔✅✅✅✅✅✅!!✅⛔✅✅✅✅✅✅!⛔!!!✅✅✅✅⛔⛔LlamaIndex!✅⛔✅✅✅✅✅embedchainAgentVerseSuperAGITxtaiAutoChainTermGPTBotpressDomain-Specific LLM-SH!!✅!⛔!✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅⛔✅!⛔✅✅!⛔✅✅!✅✅⛔✅✅!✅✅⛔✅✅!⛔!✅⛔⛔!⛔⛔!!⛔⛔!✅!✅!⛔⛔✅✅!LLM-SHHandling Unconventional Input Content Exceeding LLM’s Token LimitNon-textual Contents BeyondLLMs’Capabilities Beneficial Effects of the ReasoningAcceleration of ReasoningRefining Outputs to Stipulated CriteriaControl of LLMs OutputsOutput’s ContentOutput’s StructureCapability of Utilizing External ToolsMaintenance of HistoricalInformationImpact of Invocation CostsDecrease LLMs Invocation FrequencyDecrease Token Processing During LLMs InvocationPrompting FrameworkLMQLProgram--ming LLM-LNG✅✅✅✅!⛔⛔✅!⛔SudoLangPromptLanggpt-jargonPseudocode LLM-LNG⛔⛔✅✅✅✅!!⛔⛔⛔⛔⛔⛔⛔⛔⛔✅✅✅⛔⛔⛔⛔⛔✅✅✅⛔⛔LLM-LNGHandling Unconventional Input Content Exceeding LLM’s Token LimitNon-textual Contents BeyondLLMs’Capabilities Beneficial Effects of the ReasoningAcceleration of ReasoningRefining Outputs to Stipulated CriteriaControl of LLMs OutputsOutput’s ContentOutput’s StructureCapability of Utilizing External ToolsMaintenance of HistoricalInformationImpact of Invocation CostsDecrease LLMs Invocation FrequencyDecrease Token Processing During LLMs InvocationPrompting FrameworkContent LLM-RSTRGuidancePromptifyReLLMStructure LLM-RSTRLLM-RSTRNeMo-GuardrailsGuardrailsTypeChat!✅!!⛔✅✅✅✅⛔⛔✅⛔⛔✅✅✅✅⛔✅⛔✅✅✅⛔✅⛔!!!⛔⛔⛔⛔⛔✅✅✅⛔⛔⛔⛔⛔⛔✅✅✅✅✅✅⛔⛔⛔✅✅!!⛔⛔⛔!⛔✅support partial supportnot supportPrompting Frameworks for Large Language Models: A Survey •

17

Compatibility of Programming Languages. Due to different development team preferences and project
requirements, prompting frameworks are typically designed to consider the use of multiple programming
languages by developers. As a result, various prompting frameworks often provide interfaces supporting one or
multiple mainstream programming languages to allow developers to flexibly choose and interact with languages
in different projects and environments, thereby enhancing development efficiency and adaptability. The currently
available prompting framework provides comprehensive coverage of programming languages, including Python,
Java, JavaScript, C#, C++, Go (Golang), Rust, and TypeScript.

Comparative Analysis. Currently, the prompting framework is still in its early stages of rapid development.
Language support tends to begin with an implementation in a specific language and then expand to support
a wider range of programming languages, accommodating more use cases and domains. Overall, LLM-SH is
designed to be more adaptable to a broader range of scenarios and to support a richer set of tools. Consequently,
LLM-SH exhibits stronger compatibility with programming languages compared to LLM-RSTR and LLM-LNG.
For instance, Txtai, within LLM-SH, offers impressive support for five mainstream programming languages:
Python, Java, Rust, Golang, and JavaScript. Meanwhile, LangChain and Semantic Kernel can each support three
programming languages: Python, TypeScript, and JavaScript, as well as C#, Python, and Java, respectively. Most
prompting frameworks tend to focus on supporting one mainstream programming language, with Python and
TypeScript being the primary choices. For instance, in LLM-SH, tools like Haystack, Griptape, PromptFlow,
LLMStack, OpenDAN, AutoChain, TermGPT, and in LLM-LNG, LMQL, as well as in LLM-RSTR, NeMo-Guardrails,
Guardrails, Guidance, Promptify, and ReLLM primarily support Python. On the other hand, Hyv and botpress
belonging to LLM-SH, and TypeChat belonging to LLM-RSTR are specifically designed for TypeScript. LlamaIndex
and embedchain in LLM-SH support both Python and TypeScript. Furthermore, LLM-chain is exclusively focused
on Rust, while LinGoose is tailored for the Golang. As for Pseudocode LLM-LNG, its intent is to create a new
language to simplify interaction with LLMs, so SudoLang, PromptLang, and gpt-jargon support only the syntax
of the language designed within the framework and natural language.

In summary, in terms of compatibility with programming languages, LLM-SH surpasses LLM-RSTR, which in
turn surpasses LLM-LNG.

Compatibility of LLMs. The original intention of the Prompting Framework is to establish a medium for
interaction between external and LLMs. Therefore, one of the key requirements for the Prompting Framework
is its compatibility with LLMs, which means that the Prompting Framework should seamlessly integrate with
various types of LLMs and handle their inputs and outputs correctly. In other words, Prompting Frameworks
with better compatibility generally offer a unified interface, which enables users to use the different Prompting
Frameworks with corresponding instructions to interact with LLMs, without requiring additional handling of
specific details. The current prompting framework supports various LLMs, primarily including the previously
mentioned OpenAI API, Azure OpenAI API, HuggingFace API, as well as other APIs such as Llama API, Anthropic,
ERNIE-Bot, Google PaLM, and so on.

Comparative Analysis. Currently, support for LLMs within prompting frameworks is in a phase of rapid
evolution due to the continuous emergence of new LLMs. Developers need to swiftly integrate these models into
prompting frameworks once they are familiar with their functionalities and usage. It’s worth noting that when
we refer to LLMs compatibility, we mean the ability to seamlessly integrate models into prompting frameworks
without the need for complex additional operations or coding, which implies direct utilization of models in
prompting frameworks through modifications to certain configurations, using the LLMs in their native supported
form, rather than relying on additional plugins or frameworks. Models that are natively supported by prompting
frameworks tend to integrate better with the framework, fully leveraging the model’s capabilities and minimizing

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

18

• Xiaoxia Liu, Jingyi Wang, Jun Sun, Xiaohan Yuan, Guoliang Dong, Peng Di, Wenhai Wang, and Dongxia Wang*

Table 2. The maximum tokens supported and pricing of mainstream LLMs.

Model

gpt-4

gpt-4-32k

gpt-3.5-turbo

gpt-3.5-turbo-16k

text-davinci-003

text-davinci-002

text-embedding-ada-002
Claude Instant
Claude 2
Llama 2
Cohere
PaLM 2

Developer

Max Token

Cost / 1K tokens
Output
Input

OpenAI
Azure OpenAI
OpenAI
Azure OpenAI
OpenAI
Azure OpenAI
OpenAI
Azure OpenAI
OpenAI
Azure OpenAI
OpenAI
Azure OpenAI
OpenAI
Anthropic
Anthropic
MetaAI
Cohere
Google

8,192

$0.03

$0.06

32,768

$0.06

$0.12

4,097

$0.0015

$0.002

16,385

$0.003

$0.004

4,097

$0.012

$0.016

4,097

$0.012

$0.012

8,191
100,000
100,000
4,096
4,096
8,000

$0.0001
$0.00163
$0.01102
free
$0.015
$0.0005

$0.0001
$0.00551
$0.03268
free
$0.015
$0.0005

unexpected bugs during programming. At present, all prompting frameworks offer good support for prominent
APIs released by OpenAI, namely text-davinci-003, gpt-3.5-turbo, chatgpt, and gpt-4. In other words, prompting
frameworks were originally introduced to facilitate user interactions with these mainstream APIs. Pseudocode
LLM-LNG is a special case where this mutation-free pseudocode language can work well with any interactive
interface-based LLMs. Consequently, SudoLang, PromptLang, and gpt-jargon can be compatible with almost
all interactive LLMs. Only a few prompting frameworks currently offer support for Hugging Face APIs. For
instance, within LLM-SH, LangChain, Semantic Kernel, Haystack, Griptape, PromptFlow, LinGoose, LlamaIndex,
embedchain, Txtai, AutoChain, and within LLM-RSTR, TypeChat and Promptify, provide such support. The
mentioned prompting frameworks can also be compatible with Google’s Azure OpenAI API. Furthermore, for
other popular APIs like Claude from Anthropic, Llama API, Google PaLM, etc., only LLM-SH’s LangChain,
Semantic Kernel, Haystack, Griptape, Txtai, LlmaIndex, and embedchain can offer good support.

In summary, all prompting frameworks offer good support for OpenAI’s APIs. In general, LLM-SH exhibits the
strongest compatibility with LLMs, while Pseudocode LLM-LNG demonstrates exceptional compatibility when
dealing with interactive interface-based LLMs without requiring compilation.

6.1.2 Capabilities and Features. Capabilities and features are a crucial dimension when comparing different
Prompting Frameworks, as they directly determine the framework’s ability and flexibility in addressing problems
and meeting user requirements. We elaborate on various crucial stages of the interaction between LLMs and
the Prompting Framework, including data preprocessing, reasoning process, output control, cost considerations,
tool learning, and information maintenance. The comparison dimensions of capabilities and features we have
enumerated can be employed not only for analyzing the strengths and limitations of diverse prompting frameworks
but also as evaluation metrics for forthcoming tasks in assessing the prompting frameworks.

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

Prompting Frameworks for Large Language Models: A Survey •

19

Capability of Handling Unconventional Contents. The ability of prompting frameworks to assist LLMs in
handling unconventional content primarily manifests in two aspects. Firstly, the prompting framework helps
LLMs deal with content that exceeds the token limit, and secondly, the prompting framework empowers LLMs to
process non-textual content formats that go beyond their inherent capabilities. Usually, LLMs have a token limit
determined by the model’s architecture and memory constraints. For example, GPT-3.5-turbo and text-davinci-003
have a maximum input length of 4,097 tokens, while gpt-3.5-turbo-16k allows for 16,385 tokens, and GPT-4-32k
allows for 32,768 tokens, which results in LLMs being unable to capture the global context of a text when dealing
with extremely long documents without external support because only a portion of the text can be included.
The maximum tokens supported and pricing of mainstream LLMs are shown in Tab. 2. Moreover, processing
such long text can lead to performance issues, especially in resource-constrained environments. LLMs need to
maintain a lot of information within a single input, which may require more computational resources and time.
Therefore, prompting frameworks have emerged to assist LLMs in handling complex tasks involving extremely
long texts, such as machine translation, legal document analysis, sentiment analysis of lengthy novels or articles,
long-context dialogue systems, knowledge graph construction, etc. LLMs are primarily designed for processing
pure textual data, making them less suitable for unconventional formats like images, audio, or videos, whose
main inputs and outputs are text data. Prompting frameworks effectively mitigate this limitation, enabling LLMs
to handle a variety of data types, which broadens the application of LLMs to a wide range of multimedia tasks.
Comparative Analysis. In terms of the capability to handle content exceeding token limits and non-textual
content, only LLM-SH can achieve these functionalities without the need for additional plugins or program calls.
LLM-LNG and LLM-RSTR achieve these capabilities by making calls to LLM-SH within their framework design.
However, it’s important to note that such compatibility can potentially lead to unexpected bugs.

For handling content that exceeds token limits, LLM-SH empowers LLMs through methods like splitting,
filtering, concatenation, or summarization. For instance, a classic approach is the “Retrieval" module in LangChain,
where “Document transformers" offer pre-packaged functional functions for document splitting, composition, and
filtering. In the “Chains" module, there is a package called “chains.summarize" that provides various methods for
summarizing documents (PDFs, Notion pages, customer questions, etc.), including Map-Reduce, Stuff, and Refine
approaches to organizing documents. By configuring parameters to design a "chain" structure differently and
introducing vector databases and text embedding models, LLMs can effectively manage extremely long documents.
Similarly, modules like "Summarizer" in Haystack and "Summary Engines" in GripTape can summarize long texts,
and components like "PreProcessor" in Haystack and "Chunkers" in GripTape can perform text splitting and
filtering for long texts.

When it comes to handling non-textual content, LLM-SH can process text extracted from non-text formats
like YouTube videos or HTML files or generate multi-modal content such as images, videos, and audio, based
on pure text content. However, it doesn’t provide full-fledged processing of multimedia files throughout the
input-output process. For instance, the "Tool Memory" module in GripTape can generate images, videos, PDFs,
and other non-textual content. Similarly, the "Document loaders" module in LangChain exposes a "load" method
for loading data as documents from a configured source.

In summary, only LLM-SH can assist LLMs in handling unconventional input contents, while LLM-LNG and
LLM-RSTR need to rely on LLM-SH to achieve this functionality. LLM-SH deals with content exceeding token
limits by splitting, filtering, reassembling, or summarizing long documents. Regarding non-textual content,
LLM-SH processes the text portions extracted from multimedia files or generates multi-modal multimedia
files based on pure text content.

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

20

• Xiaoxia Liu, Jingyi Wang, Jun Sun, Xiaohan Yuan, Guoliang Dong, Peng Di, Wenhai Wang, and Dongxia Wang*

Beneficial Effects of the Reasoning Process. The benefits of prompting frameworks for LLMs in the
reasoning process are primarily evident in two capabilities: accelerating reasoning and ensuring that reasoning
results meet preset requirements. In the current scenario with a surge in data volume and user usage, the speed
of LLMs’ reasoning is crucial for completing tasks efficiently. Additionally, improved reasoning results enable
LLMs to accomplish more work in a given unit of time, greatly facilitating the application of these powerful
natural language processing models in tasks requiring rapid responses and high throughput. For example, it’s
useful in online customer support (providing instant responses to customer queries for better user experiences),
real-time financial analysis (for timely financial decision-making by analyzing news events and market data), and
real-time sentiment analysis (for tracking product or brand feedback on social media in real-time).

Comparative Analysis. Regarding the crucial functionality of accelerating reasoning, most prompting frame-
works do not provide support. Among the prompting frameworks surveyed, only LMQL within LLM-LNG offers
this relevant service. LMQL accelerates inference by providing eager validation during LLM runtime. The principle
behind eager validation is that LLMs typically generate text sequentially, similar to how humans write. When
users make requests to LLMs with conditions like "the output must satisfy A and B," LMQL monitors the output
as it’s being generated. If LMQL detects that the currently outputted portion no longer satisfies condition A, it
forcibly stops the LLM’s execution and triggers it to re-infer, which eliminates the need to wait until the LLM
completes the entire response to determine if the output complies with the conditions. For example, if a user
instructs Chatgpt with the input "Write a poem about the sky, excluding clouds and birds," conditions A and B are
"excluding clouds" and "excluding birds." If Chatgpt generates a description of "clouds" during the writing process,
it no longer meets the user’s request. Therefore, LMQL performs a forced termination of Chatgpt and resumes
from the error-free portion to continue the task. This "validate-as-you-go" approach significantly accelerates
LLM inference.

To ensure that inference results meet preset requirements, LLM-LNG, LLM-RSTR, and LLM-SH all utilize
validate templates or allow for user-defined templates to ensure more standardized and accurate prompts (inputs).
For instance, features like "Prompts" in LangChain’s Model I/O module and "PromptTemplate" in Haystack
enable predefined templates as well as user-defined templates within the framework. Additionally, the previously
mentioned eager validation not only accelerates inference but also enforces stricter compliance with output
requirements, making it easier to obtain outputs consistent with expectations and standards.

In summary, to enhance the inference process of LLMs, LLM-LNG, LLM-RSTR, and LLM-SH all use methods
such as predefined templates or compatibility with user-defined templates to ensure that inference results
better meet requirements. Only LMQL within LLM-LNG supports the acceleration of the reasoning process
during LLM runtime.

Control of LLMs Outputs. Prompting framework’s role in achieving controllable generation with LLMs
primarily addresses two issues: imposing fine-grained structural constraints on generated output and ensuring
that LLMs do not produce sensitive, non-compliant, or unsafe content. The significance of structured output
from LLMs lies in its ability to transform natural language text into a structured format, making information
easier to process, analyze, and apply. The structured output aids in tasks such as extracting key information
from text, building knowledge graphs, and performing data analysis. Structured data plays a crucial role in
information management and data analysis, supporting decision-making, process optimization, insight discovery,
and the development of intelligent applications. Structured data is essential in various industries and domains,
helping organizations better understand and leverage their data assets. The safety and relevance of LLMs’ output
content are crucial because these factors directly impact whether the text generated by the model is appropriate,
accurate, and useful. For example, content filtering on social media platforms ensures that content posted on

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

Prompting Frameworks for Large Language Models: A Survey •

21

these platforms does not contain inappropriate or rule-violating material, maintaining the platform’s reputation
and user experience. In online customer support, automated response systems generate information only related
to product support or common issues, ensuring that responses generated by automated systems are both on-topic
and free from inappropriate content. Maintaining the online platform’s brand reputation, protecting user rights,
providing accurate information, and enhancing the availability of automated systems are all essential. Using
prompting frameworks to assist in the automated and intelligent handling of LLMs’ output content, ensuring that
generated text meets specific requirements, has practical applications in social media, news media, e-commerce,
online education, and many other fields.

Comparative Analysis. When it comes to constraining the output structure of LLMs, LLM-SH, LLM-LNG, and
Content LLM-RSTR typically provide interfaces or pre-packaged functions that, when given custom structured
templates provided by users, transform LLMs’ output into the corresponding structured format. For example,
LangChain’s Model I/O module offers "Output parsers," which are classes designed to help structure language
model responses. By invoking LangChain’s built-in functions and combining them with user-configured structural
templates, LLM-SH’s LangChain directly supports various commonly used structured output forms, such as
lists, time formats, enumerations, JSON, and more. In Semantic Kernel within LLM-SH, LMQL within LLM-LNG,
and SudoLang, which are designed with frameworks and syntax that allow the mixing of natural language with
code, support for structured data is achieved through user-configured custom structural templates. This means
that users need to design, describe, and write their own templates in the corresponding framework’s custom
template locations. However, in the case of Structure LLM-RSTR, a category of prompting frameworks specifically
designed for structured output, they offer built-in features for structured data generation and validation and
excel at supporting formats like JSON and dialogue-based data. For instance, in Guidance, you can use the "gen"
command to interleave generation, prompting, and logic control in a continuous sequential flow that aligns with
how the language model processes text. In TypeChat, there’s the provision of Schema, a data structure used to
describe the expected format and fields of a prompt. By defining a Schema, you can validate and correct user
input to ensure it adheres to the expected format and requirements.

Securing and ensuring compliance with the output content of LLMs is crucial. However, except for Content LLM-
RSTR within LLM-RSTR, no other prompting frameworks address this issue. In Content LLM-RSTR, Guardrails is
a Python package that adds type and quality assurance to LLMs’ output, including semantic validation, such as
checking for biases in generated text and errors in generated code and takes corrective measures when validation
fails. Guardrails provides a file format (.rail) for executing "specifications" (user-specified structural and type
information, validators, and corrective actions) on LLMs’ output and offers a lightweight API call wrapper to
implement these specifications on the output. NVIDIA’s NeMo-Guardrails follows a similar design philosophy,
ensuring control, safety, and security of large model language generation by limiting templates and themes in
conversations. NeMo-Guardrails employs a custom language to implement a three-layer protection mechanism,
including Topical GuardRail for topic-related questions, Safety GuardRail for ensuring controlled responses, and
Security GuardRail to protect against malicious or abusive questions. However, this approach, while practical, also
introduces potential challenges such as configuration redundancy, inflexibility, operational risks, and limitations
on the original conversational capabilities of LLMs.

In summary, LLM-SH, LLM-LNG, and LLM-RSTR all offer different ways to support control over the structure
of LLMs’ output, but only Content LLM-RSTR within LLM-RSTR provides constraints and validation for the
safety and compliance of LLMs’ output content, albeit with certain potential issues in its functionality.

Impact of Invocation Costs. Reducing the cost of LLMs invocation primarily involves two approaches: firstly,
reducing the frequency of invoking LLMs, and secondly, decreasing the number of tokens processed during LLMs

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

22

• Xiaoxia Liu, Jingyi Wang, Jun Sun, Xiaohan Yuan, Guoliang Dong, Peng Di, Wenhai Wang, and Dongxia Wang*

invocation. Utilizing LLMs services on cloud computing platforms such as AWS, Azure, and Google Cloud incurs
charges for each model invocation. These costs escalate with the frequency of invocations and the extent of
computational resources used. One of the significant challenges in implementing LLMs for practical production
scenarios is the high cost associated with invoking LLMs, which can be burdensome for individuals and even
enterprises with limited financial resources. LLMs are typically billed based on the number of tokens generated
or processed, with the number of tokens subject to charges determined by the prompt and the corresponding
response length. The billing unit is the "token," which can represent a word, character, or punctuation symbol. In
English, one token typically corresponds to one word, but for other languages, token forms may vary due to
differences in language structures. Different models have varying token pricing standards; for example, GPT-3.5
is priced at $0.002 per 1000 tokens, while GPT-4’s token price is nearly six times higher than that of GPT-3.5. The
maximum tokens supported and pricing of mainstream LLMs are shown in Tab. 2. While the cost per individual
token may appear acceptable from a computational perspective, it becomes substantial for long-term usage and
complex tasks. For instance, translating large documents, especially complex technical documents across multiple
languages, may require extended processing time and additional computational resources. Similarly, employing
LLMs for large-scale data analysis, text mining, or information extraction tasks, such as processing tens of
thousands of news articles to extract key information, might necessitate distributed computing environments
and substantial storage, resulting in high invocation costs.

Comparative Analysis. In terms of reducing the frequency of LLMs invocation, LLM-SH introduces the "Memory"
module that stores historical query information. Leveraging vector databases, enables a form of "learning from
the past," so that when encountering the same or similar questions, LLMs do not need to be invoked again, thus
saving unnecessary computational expenses. For instance, LLM-SH’s LangChain implements a "Memory" module
for storing past interactions, Haystack includes a "Module memory" module with the InMemoryDocumentStore
class for recording and retrieving interaction content, and Griptape offers a "Conversation Memory" module
with BufferConversationMemory functionality for constructing prompts with sliding window tasks. In contrast,
LLM-LNG primarily reduces the frequency of invoking LLMs by embedding preprocessing programs and modules
within the framework. Simple questions are first handled by smaller or free models, and then LLMs are utilized for
more detailed processing, thus reducing the number of LLMs invocations. However, this method has limitations
in broader tasks. Additionally, LLM-RSTR frameworks typically do not consider this functionality. Regarding
the prompting framework’s role in reducing the number of tokens that LLMs need to process, LLM-SH employs
techniques like splitting, filtering, concatenating, or summarizing text segments to abbreviate and simplify the
content to be processed. This aligns with the earlier-discussed approach of handling extremely long documents.

In summary, the current state of prompting frameworks does not fully address the crucial challenge of reducing
the cost of LLMs invocation. LLM-SH employs "Memory" functionality and text manipulation techniques to
reduce the frequency of invocations and the number of tokens to be processed. LLM-LNG relies on embedded
preprocessing modules, which have limited applicability, while LLM-RSTR frameworks generally do not
implement this capability. Therefore, in the future, reducing the cost of LLMs invocation should be an essential
area of development for prompting frameworks.

Capability of Utilizing External Tools. The ability to use tools is one of the most significant distinctions
between humans and other species. Currently, a crucial limitation of LLMs in practical applications is their
inability to use external tools like humans. However, the advent of prompting frameworks effectively mitigates
this deficiency. Typically, LLMs are generalized models, so the capability for LLMs to utilize external tools holds
significant importance for enhancing their functionality, adapting to specific tasks and domain requirements,
providing access to more data and resource support, and meeting compliance and security demands. For example,

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

Prompting Frameworks for Large Language Models: A Survey •

23

in custom text generation tasks, combining external plugins with LLMs allows the generation of industry-specific
news reports, creative writing, or legal documents. In complex data query tasks, integrating LLMs with database
query plugins enables them to respond to intricate business queries such as sales reports, inventory management,
or medical record retrieval. Furthermore, multimodal processing plugins can be integrated with LLMs to analyze
and generate content with text, images, and audio elements, such as social media posts or advertisements.

Comparative Analysis. In terms of enabling LLMs to use external tools, LLM-SH outperforms LLM-RSTR and
LLM-LNG due to its design focus. LLM-SH can support the integration of LLMs with a wide range of tools spanning
various domains, such as web browsers, databases, email clients, image processing tools, speech recognition
engines, code processors, and more. For instance, LangChain’s Agents module offers a Toolkit function in which
a collection of tools designed for specific tasks and conveniently loaded methods are available. These tools
encompass Gmail, GitHub, SQL Databases, Vectorstore, and various Natural Language APIs. GripTape utilizes
the Tools module’s TextToolMemory to enhance the output of all tools, while also allowing users to perform
different degrees of customization at the structural, task, or tool activity levels. TextToolMemory empowers LLMs
to interact with the external world, generating non-textual content such as images, videos, PDFs, and others. In
contrast, LLM-LNG and LLM-RSTR provide limited support for only the most commonly used external tools. For
instance, LMQL in LLM-LNG offers services restricted to calculators and Wikipedia tools, while Guidance in
LLM-RSTR offers integration with the Bing search engine.

In summary, the current state of prompting frameworks for enabling LLMs to integrate with external tools
is in its initial and somewhat immature stage. LLM-SH provides LLMs with the capability to use tools in
relatively diverse scenarios to some degree, while LLM-LNG and LLM-RSTR offer very limited support in this
regard.

Maintenance of Historical Information. Maintenance of historical interaction information is crucial for
LLMs as it provides them with the ability to store, retrieve, and reference information. This capability aids in
better understanding context, maintaining coherence in complex tasks and long texts, and benefiting from past
computations. However, apart from chat models like ChatGPT, which can record some history within the same
conversation interface (with no sharing of information across different interfaces), LLMs typically process only
the current context information provided in the prompt during service. This limitation is inconvenient for users
as historical interaction information not only enhances interactions with LLMs, reducing the need for repetitive
work but also stimulates non-dialogue LLMs like GPT-3.5 in chat tasks. Prompting frameworks address this need
by offering "Memory" systems, supporting two fundamental operations: reading and writing. This enables the
storage of historical interaction information and its utilization through queries, searches, and retrieval. Prompting
frameworks empower LLMs with the ability to maintain historical interaction information, aiding in context
understanding, information retrieval, multi-turn question-answering, document reading, error detection and
correction using memory, caching intermediate computation results, and storing user preferences, historical
behavior, or personalized information.

Comparative Analysis. Regarding the maintenance of historical interaction information, LLM-SH excels due to
its comprehensive Memory system, which allows integration with various tools across different domains. Taking
LangChain as an example, the "Memory" can store past chat messages, queries, and results, effectively adding
memory to the system. This storage function can be used independently or seamlessly integrated into various
chains. Moreover, LangChain supports the use of embedded models and vector databases to store, query, and
maintain historical information. During a single run, the system interacts with "Memory" twice, once when
providing a query. The prompt includes two parts, one directly from user input, and the other possibly extracted
from information stored in memory. The second interaction records the current interaction in memory for

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

24

• Xiaoxia Liu, Jingyi Wang, Jun Sun, Xiaohan Yuan, Guoliang Dong, Peng Di, Wenhai Wang, and Dongxia Wang*

future queries and retrieval. LLM-SH’s Memory system usually offers multiple ways to manage short-term
memory, such as ConversionMemory and VectorStore-backed Memory. ConversionMemory summarizes ongoing
conversations and stores the current summary in memory, passing it as short-term memory to LLMs in new
rounds of conversation. This compression of historical conversation information is particularly useful for lengthy
conversations. On the other hand, VectorStore-backed Memory stores all past conversations in vector form in
a vector database. In each new conversation round, it matches the user’s input against the vector database to
find the most similar K sets of conversations. LLM-LNG and LLM-RSTR typically achieve historical information
maintenance by invoking the corresponding functional modules in LLM-SH. An interesting feature in LLM-LNG is
LMQL’s "Caching Layer," implemented as a tree-like data structure. This layer caches all model outputs, including
logs and historical information, to enable more efficient exploration of the LLM’s token space during runtime,
even in the presence of multiple variables, constraints, and tool enhancements. The cache can be seen as a tree
with only appendices, explored during query execution and expanded based on query code, constraint conditions,
and inferred execution scenarios.

In summary, LLM-SH provides a relatively complete and comprehensive memory system for maintaining
historical interaction information, while LLM-LNG and LLM-RSTR typically achieve this by invoking corre-
sponding functional modules within LLM-SH.

6.2 Documentation and Support.
Document quality and community support are crucial for a prompting framework. Document integrity refers to
the accuracy, readability, and completeness of technical documentation, which assesses whether the development
team provides detailed, clear, and comprehensive documentation to facilitate user learning and usage. Community
support involves the presence of an active developer community around the framework, allowing users to receive
timely assistance and feedback.

Document Completeness. The investigated prompting frameworks offer three primary deployment methods.
The first method is command-line installation, where Python-based frameworks use commands like "pip install"
or "conda install," and JavaScript-based frameworks use "npm install" for deployment. This method is available
for almost all prompting frameworks. The second method is a custom interactive user interface, providing a
playground that allows users to interact with the framework directly through a user-friendly interface without the
need for installation, for example, LMQL in LLM-LNG. The third method is the "open-and-use" approach, where
deployment and execution are done directly on the interface provided by LLMs, offering the most straightforward
and simple operation. SudoLang in LLM-LNG is an example. Overall, the prompting frameworks studied provide
comprehensive technical documentation that covers almost all features and use cases. They also offer detailed
example code, tutorials, and operation guides, making it easy for users to get started, understand, and use these
frameworks. These technical documents are readily accessible on GitHub. Additionally, some frameworks have
created well-designed web pages with high readability and attractiveness, such as LangChain in LLM-SH.

Document Readability. At present, the technical documentation of existing prompting frameworks is
comprehensive and detailed but may lack readability. The rapid proliferation of LLMs and their derivatives has led
to a need for frequent updates to the technical documentation. These updates may occur daily to accommodate
more products and features. The introduction of new features can sometimes render old ones unusable or
introduce bugs, causing significant challenges for users and developers. Furthermore, the continuous addition of
features and product introductions can make the documentation structure complex and the content increasingly
lengthy. This can lead to a situation where the documentation becomes overwhelming and resembles a "code
mountain" rather than maintaining the clarity and simplicity of its initial state, which can be frustrating for users.

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

Prompting Frameworks for Large Language Models: A Survey •

25

In summary, the dynamic nature of LLMs and their associated frameworks necessitates frequent documentation
updates, but these updates must be managed carefully to maintain clarity and usability for users and developers.
Community Support. Regarding community support and user feedback channels, the development teams
behind these prompting frameworks typically offer Discord online community services. Users can ask questions,
share experiences, and engage with other users in these communities. Furthermore, they maintain official support
teams on Twitter and have dedicated communication topics (tags) for users to provide feedback, suggestions,
and opinions, thus facilitating framework improvements. Additionally, they provide communication spaces on
GitHub for users and developers.

6.3 Challenges Confronting the Prompting Framework
The existing prompting frameworks currently alleviate many limitations of LLMs in practical applications,
significantly enhancing the capabilities of LLMs themselves and further elevating their performance. However,
burgeoning development still encounters numerous challenges. In this section, we will analyze the challenges
and opportunities that the prompting framework currently faces in terms of functionality implementation and
issues related to safety and ethics.

6.3.1 Security Mechanisms of Prompting Framework. For a developed tool, both functionality and security
mechanisms are equally crucial. Software that cannot guarantee the security of user information and is not
harmless to society, regardless of its robust functionality, is unlikely to gain user support. Existing evidence
suggests that LLMs and relatively mature prompting frameworks like LangChain have certain security issues
[6, 62, 66, 87, 118]. However, the existing prompting frameworks have paid minimal attention to the significance
of security ethics and privacy protection. Due to LLMs possessing an "Achilles’ heel" – being uncontrollable
generative AI, we cannot predict the outputs, which can be fatal in certain scenarios. Therefore, we argue that the
security mechanisms that prompting frameworks urgently need to enhance should consist of two parts: defense
against prompt-based attacks and safeguarding the behavior of LLMs.

Defense Against Prompt-based Attacks. We begin by introducing the concept of Prompt-based Attacks
and then provide some suggestions to mitigate this issue within future prompting frameworks. Prompt-based
Attacks share essential similarities with Prompt Engineering in that they both aim to obtain desired outputs
through expertly crafted, rational, and optimized instructions. However, Prompt Engineering is user-oriented,
while Prompt-based Attacks adopt a hacker-attack perspective. Malicious inputs from external sources can
contaminate the model’s outputs through Prompt-based Attacks, thereby exerting influence on external systems,
resulting in adversarial actions. The impact of such attacks depends on the capabilities granted to the model by
the system. Prompt-based Attacks refer to attempts to generate content that contradicts the developer’s intent
using LLMs [31, 43, 62, 89, 125]. Typically, there are two forms of attacks: Prompt-based Deception (bypassing
scrutiny through linguistic techniques) and Prompt-based Injection (tampering with instructions). In scenarios
limited to content generation, the harm caused by these attacks may be relatively insignificant. However, with the
proliferation of various prompting frameworks and projects like AutoGPT, more individuals are granted execution
authority over LLMs, expanding the potential danger. These scenarios encompass not only the creation of email
worms utilizing automated email processing functions but also poisoning email extraction systems through
web-based attacks, code poisoning through code completion mechanisms, and more ominous possibilities, such
as manipulating or accessing local files or diverting funds if a private prompting framework assistant were to be
compromised or granted execution authority.

As for defense mechanisms against Prompt-based Attacks, we offer several suggestions from the perspective
of instruction design. Firstly, when constructing prompts for interaction with LLMs, it is advisable to employ
delimiters to rigorously differentiate instructions from content, which involves encapsulating user-generated

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

26

• Xiaoxia Liu, Jingyi Wang, Jun Sun, Xiaohan Yuan, Guoliang Dong, Peng Di, Wenhai Wang, and Dongxia Wang*

content within delimiters and imposing specific authority constraints, a practice endorsed by OpenAI and machine
learning expert Andrew Ng as a best practice. Secondly, place crucial instructions at the end of the prompt.
Given that most malicious instructions currently tend to disregard preceding instructions, positioning developer
instructions at the end of the entire prompt is indeed a straightforward and convenient method in practice.
Lastly, consider incorporating a pre-filtering layer, such as establishing whitelists and blacklists for prompt
content. Whitelists define permissible inputs, for instance, in the case of designing a machine translation model
from Chinese to English, pre-detect and allow only Chinese characters in the prompt for synthesis with the
model. Conversely, blacklists prohibit specific inputs, for instance, detecting common jailbreak-related phrases or
instructions like "ignore" and refrain from inputting them into the model or checking for the presence of phrases
prohibited by other legal regulations.

Safeguards of LLMs’ Behavior. As is widely acknowledged, LLMs while gaining favor from millions of users,
occasionally exhibit undesirable behaviors such as escaping, hallucinating, and deception. Therefore, it is crucial
to "muzzle" LLMs by adding an additional safeguard layer to their output. Starting from the design principles
and implementations of the prompting framework, augmenting LLMs with an additional protective mechanism
within the prompting framework is both reasonable and aligned with software development principles. This
augmentation allows for the early interception and modification of objectionable or non-compliant content in
the output of LLMs before obtaining the final results.

The Nemo Guardrails developed by Microsoft, as mentioned earlier, still has several issues when it comes
to protecting LLMs’ behavior. Firstly, it uses its proprietary definition language, which may appear more user-
friendly but limits its extensibility. Moreover, it transforms a model’s security and control problem into a manual
policy configuration problem. This approach brings various potential issues such as redundant configurations,
lack of flexibility, operational risks, and potential curtailment of the original capabilities of large language models.
It seems to be more like a compromise solution in today’s commercial scenarios where there is a desire to
effectively utilize the generation capabilities of large models but no effective solution for controllability and
security.

Therefore, we believe that future prompting frameworks should be designed based on mainstream programming
languages, employing advanced technologies to establish flexible and automated mechanisms for extracting and
configuring protection rules, which focus on three main aspects: topic relevance, content safety, and application
security, ultimately standardizing the behavior of LLMs. Thematic integrity safeguards aim to prevent LLMs from
going off-topic. LLMs possess a richer imagination and are more capable of creative code and text generation
compared to other AIs. However, for specific applications such as coding or customer service, users do not
want them to "stray from the intended scope" while addressing issues, and generating irrelevant content. In
such cases, topic-constrained safeguards are required. When a large model generates text or code that goes
beyond the predefined topic, these safeguards guide it back to the designated functionality and topic. Content
safety safeguards are intended to prevent incoherent output from large models. Incoherent output includes two
scenarios: factual inaccuracies in the answers generated by LLMs, which are things that "sound reasonable but
are entirely incorrect," and the generation of biased or malicious output, such as using offensive language when
prompted by users or generating unethical content. Application security refers to restricting the application’s
connections to known secure third-party applications. The prompting framework should avoid exposing LLMs to
malicious attacks from external sources during task execution. This includes preventing the induction of LLMs to
call external virus plugins and defending against hackers who may attempt to attack LLMs through methods like
network intrusion or malicious software.

6.3.2 Capability Limitations of Prompting Framework. In comparing and analyzing the capabilities and
features of prompting frameworks, we delineate 6 dimensions. Prompting frameworks exhibit commendable

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

Prompting Frameworks for Large Language Models: A Survey •

27

performance across these capability dimensions, but they still exhibit shortcomings in the degree of implementa-
tion within each capability dimension. For instance, concerning the handling of unconventional inputs, current
prompting frameworks can significantly assist LLMs in text processing leaps but remain somewhat constrained
in multi-modal scenarios (e.g., video and images). Similarly, limitations exist in invoking external expert models.
Furthermore, as the landscape of large models continuously evolves with the emergence of numerous LLMs and
external plugins, many prompting frameworks adapt by continually adding encapsulated invocation functions to
support relevant services. However, this rapid evolution introduces several challenges. The updated functionalities
are often haphazardly aggregated and do not offer the same level of support as native capabilities provided by
the framework. Additionally, more intricate functionalities may lead to contradictions or duplications when
not properly planned, resulting in a steep learning curve for users. Consequently, we analyze the limitations
of current prompting frameworks from these perspectives: an increasingly steep learning curve, constraints in
invoking external interfaces and handling multi-modal I/O.

Increasingly Steep Learning Curve. With the explosive growth in the field of large models, numerous related
tools and plugins have emerged, which has posed significant challenges to the development and maintenance
of prompting frameworks, requiring software engineers to quickly familiarize themselves with these emerging
external tools and integrate their interfaces into the existing prompting framework. This has resulted in some
functionality stacking and redundancy. For example, native functionalities within the prompting framework
typically allow for straightforward invocation with uniform interfaces, achieved by simply modifying parameters.
Conversely, newly added functionalities often necessitate users to invoke other packages and employ relatively
complex and non-uniform calling procedures. Consequently, users must acquire additional knowledge before
usage, resulting in steeper learning curves. The relatively complex processes and methods also lead to suboptimal
user experiences or program bugs. Furthermore, the introduction of new functionalities may disrupt the proper
functioning of previously implemented native features, which is a recurring issue within existing prompting
frameworks. As previously indicated, it has been observed that the technical documentation of the existing
prompting framework exhibits deficiencies in terms of readability. The emergence of this problem is logical,
and an effective mitigation strategy involves developers considering future developments and changes in the
framework’s structural design, which entails enhancing the modularity, scalability, and standardization of the
prompting framework.

Constraints in Invoking External Interfaces. Currently, prompting frameworks can support relatively basic
external tool usage, such as browsing the web or querying databases. However, we argue that the accessibility of
external expert models remains rudimentary within most prompting frameworks. For instance, current prompting
frameworks cannot fully assist LLMs in utilizing the widely-used "Microsoft Suite" in commercial and office
environments, including Microsoft Word, Microsoft Excel, and Microsoft PowerPoint. Additionally, prompting
frameworks lack secure protocols for accessing and handling users’ private or commercial data that meet security
and privacy requirements. Furthermore, because current prompting frameworks can only handle text-based
tasks, there are limitations in handling multi-modal inputs such as videos, Word documents, emails, etc. This
makes it challenging to provide support for widely-used functional tools like YouTube (one of the world’s largest
video-sharing platforms with billions of users), arXiv (a significant open-access academic preprint platform),
Twitter (a prominent social media platform in the realm of social media and news dissemination), Outlook (one of
Microsoft’s widely-used email and calendar management tools), and others. In the future, prompting frameworks
should aim to not only assist LLMs in supporting these widely-used mainstream software but also allow for the
integration of more emerging or niche tools or platforms to foster a more vibrant AI community ecosystem.

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

28

• Xiaoxia Liu, Jingyi Wang, Jun Sun, Xiaohan Yuan, Guoliang Dong, Peng Di, Wenhai Wang, and Dongxia Wang*

7 FUTURE DIRECTIONS AND CONCLUSION
7.1 Conclusion of Existing Prompting Frameworks
In this paper, we elucidate the genesis of the prompting framework and its underpinning technological foundations.
Subsequently, we proffer a conceptual definition of the prompting framework, along with its requisite character-
istics of modularity, abstraction, extensibility, and standardization. We then classify the prompting framework
based on usage scenarios and technical attributes into three categories: the shell of LLMs (LLM-SH), language for
interaction with LLMs (LLM-LNG), output restrictors of LLMs (LLM-RSTR). Following this categorization, we
conduct a comprehensive comparative analysis of the compatibility, capabilities and features, documentation,
and community support of these prompting frameworks across various dimensions. Finally, we delineate the
challenges currently confronting the development of prompting frameworks. Additionally, we introduce several
practical relevant prompt-based tools that fall outside the purview of the prompting framework domain and
tools that play a significant role in assisting LLMs in accomplishing tasks. In this section, we summarize the
applicability and limitations of existing prompting frameworks.

Despite the various attempts made by current prompting frameworks to alleviate the limitations of LLMs in
real-world applications, there are still challenges and limitations that need to be addressed. These frameworks
have emerged with different focuses and features, addressing various dimensions of user concerns, including
documentation and community support, compatibility, capabilities (such as the ability to use external tools,
cost reduction, etc.), which have indeed made strides in solving some of the issues. However, it is important
to note that current prompting frameworks can be considered as compromise solutions to meet user needs in
today’s commercial scenarios, rather than fully future-proof methods. The limitations of existing prompting
frameworks primarily revolve around the lack of support for security mechanisms and inherent limitations in
their capabilities.

Security Mechanisms. Regarding the security mechanisms within prompting frameworks, including resis-
tance to prompt-related attacks and constraints on LLMs’ behavior, there are currently significant limitations.
Firstly, most prompting frameworks do not adequately address resistance against prompt-related attacks, such
as injection and deception. These vulnerabilities pose a severe threat to system security. Additionally, in terms
of constraining LLMs’ behavior, current prompting frameworks rely primarily on manually configured safety
policies similar to Reinforcement Learning from Human Feedback (RLHF). They have not fully leveraged advanced
technologies and methods, which can result in issues like redundant configurations, inflexibility, operational
risks, and even limitations on the original functionality of LLMs.

Capability Limitations. The limitations in the capabilities of prompting frameworks themselves are evident,
especially when it comes to developing applications with large language models (LLMs). One of the primary
reasons for this limitation is that many of the issues in LLM applications are rooted in the deficiencies of the
underlying technology of large models, emphasizing the importance of prompt engineering. For instance, when
manipulating LLMs to perform highly complex tasks using prompting frameworks, developers often rely on
highly customized, handcrafted prompts. However, many existing prompting frameworks are designed with
a "simplification to complexity" principle in mind. They assume that more complex structures lead to more
comprehensive functionality. In other words, these frameworks tend to be overly complex and do not provide
sufficient openness in terms of prompt design. As a result, users often find themselves needing to configure
many aspects of the system themselves, but prompting frameworks do not provide appropriate support for this
requirement. Therefore, simplifying and streamlining the configuration process and providing more open and
flexible prompt design options could enhance the usability and effectiveness of these frameworks in developing
complex LLM applications. Simultaneously, the current prompting framework still faces notable shortcomings

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

Prompting Frameworks for Large Language Models: A Survey •

29

in its accessibility to the broader external world, such as the limited support for third-party tools, including
multimodal tools, and mainstream platforms like arXiv and Twitter.

7.2 Future Directions
We believe that the next-generation of prompting frameworks should overcome the limitations mentioned above
while integrating the strengths of the three prompting frameworks in this paper, which can provide users with
more concise and compact interaction channels, facilitate LLMs interactions with powerful third-party interfaces,
and enable interactions with higher-quality and more tailored. The next-generation prompting framework should
be a comprehensive platform that is more streamlined, more secure, more versatile, and more standardized, which
seamlessly integrates development, testing, evaluation, maintenance, expansion, and communication with LLMs,
constituting an organic LLM ecosystem.

More streamlined. The next-generation prompting framework should embody a higher degree of streamlining,
primarily manifested in the simplification of user interactions with LLMs and the interactions between LLMs and
environments. Furthermore, the technical architecture and documentation should exhibit enhanced compatibility
with new products and technologies, coupled with a more user-friendly learning curve and instructional materials.
In essence, it should adhere to the principle of "simplify without oversimplifying, embracing the concept of
simplicity as the ultimate sophistication."

More secure. The next-generation prompting framework ensures the secure and compliant generation of
content by Large Language Models (LLMs) while safeguarding user privacy and security, serving as a bidirectional
security barrier between users and LLMs and between LLMs and applications.

More versatile. The next-generation prompting framework seamlessly integrates with more diverse, feature-
rich external applications, enabling LLMs to excel in various domains such as healthcare, research, education,
transportation, and more.

More standardized The next-generation prompting framework adheres to established domain standards,
which are widely accepted sets of rules, guidelines, specifications, or best practices within specific domains
to ensure the quality, consistency, and reliability of products, services, or processes. Examples include ISO
27001 for information security management systems (ISMS) in the field of information technology and GMP
standards for quality management in pharmaceutical and medical device manufacturing in the healthcare domain.
These standards facilitate compliance across different prompting frameworks, eliminating the need for users to
acquire additional knowledge and promoting mutual support and complementarity between different prompting
frameworks.

Organic LLMs ecosystem. The next-generation prompting framework seamlessly integrates with LLMs,
serving as a comprehensive platform for LLM development, testing, comparison, evaluation, user interaction,
and developer communication. This integration fosters an ecosystem that evolves through continuous feedback,
ultimately delivering enhanced services and enabling leaps in technology and application development.

REFERENCES

[1] Fatih Kadir Akın. 2022. Awesome ChatGPT Prompts. https://github.com/f/awesome-chatgpt-prompts
[2] Mostafa M Amin, Erik Cambria, and Björn W Schuller. 2023. Will Affective Computing Emerge From Foundation Models and General

Artificial Intelligence? A First Evaluation of ChatGPT. IEEE Intelligent Systems 38, 2 (2023), 15–23.

[3] apache. 2022. CAMEL. https://github.com/apache/camel
[4] Stephen H. Bach, Victor Sanh, Zheng-Xin Yong, Albert Webson, Colin Raffel, Nihal V. Nayak, Abheesht Sharma, Taewoon Kim, M Saiful
Bari, Thibault Fevry, Zaid Alyafeaiu, Manan Dey, Andrea Santilli, Zhiqing Sun, Srulik Ben-David, Canwen Xu, Gunjan Chhablani, Han
Wang, Jason Alan Fries, Maged S. Al-shaibani, Shanya Sharma, Urmish Thakker, Khalid Almubarak, Xiangru Tang, Mike Tian-Jian, and
Alexander M. Rush. 2022. PromptSource: An Integrated Development Environment and Repository for Natural Language Prompts.
(2022). https://arxiv.org/abs/2202.01279

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

30

• Xiaoxia Liu, Jingyi Wang, Jun Sun, Xiaohan Yuan, Guoliang Dong, Peng Di, Wenhai Wang, and Dongxia Wang*

[5] Yejin Bang, Samuel Cahyawijaya, Nayeon Lee, Wenliang Dai, Dan Su, Bryan Wilie, Holy Lovenia, Ziwei Ji, Tiezheng Yu, Willy Chung,
et al. 2023. A multitask, multilingual, multimodal evaluation of chatgpt on reasoning, hallucination, and interactivity. arXiv preprint
arXiv:2302.04023 (2023).

[6] Clark Barrett, Brad Boyd, Ellie Burzstein, Nicholas Carlini, Brad Chen, Jihye Choi, Amrita Roy Chowdhury, Mihai Christodorescu,
Anupam Datta, Soheil Feizi, et al. 2023. Identifying and Mitigating the Security Risks of Generative AI. arXiv preprint arXiv:2308.14840
(2023).

[7] Yoshua Bengio, Aaron Courville, and Pascal Vincent. 2013. Representation learning: A review and new perspectives. IEEE transactions

on pattern analysis and machine intelligence 35, 8 (2013), 1798–1828.

[8] Yoshua Bengio, Réjean Ducharme, and Pascal Vincent. 2000. A neural probabilistic language model. Advances in neural information

processing systems 13 (2000).

[9] Amanda Bertsch, Uri Alon, Graham Neubig, and Matthew R Gormley. 2023. Unlimiformer: Long-range transformers with unlimited

length input. arXiv preprint arXiv:2305.01625 (2023).

[10] Luca Beurer-Kellner, Marc Fischer, and Martin Vechev. 2023. Prompting is programming: A query language for large language models.

Proceedings of the ACM on Programming Languages 7, PLDI (2023), 1946–1969.

[11] Rishi Bommasani, Percy Liang, and Tony Lee. 2023. Holistic Evaluation of Language Models. Annals of the New York Academy of

Sciences (2023).

[12] botpress. 2023. Botpress. https://github.com/botpress/botpress
[13] Tom Brown, Benjamin Mann, Nick Ryder, Melanie Subbiah, Jared D Kaplan, Prafulla Dhariwal, Arvind Neelakantan, Pranav Shyam,
Girish Sastry, Amanda Askell, et al. 2020. Language models are few-shot learners. Advances in neural information processing systems 33
(2020), 1877–1901.

[14] Jake Brukhman. 2023. gpt-jargon. https://github.com/jbrukh/gpt-jargon
[15] Aydar Bulatov, Yuri Kuratov, and Mikhail S Burtsev. 2023. Scaling Transformer to 1M tokens and beyond with RMT. arXiv preprint

arXiv:2304.11062 (2023).

[16] Yihan Cao, Siyu Li, Yixin Liu, Zhiling Yan, Yutong Dai, Philip S Yu, and Lichao Sun. 2023. A comprehensive survey of ai-generated

content (aigc): A history of generative ai from gan to chatgpt. arXiv preprint arXiv:2303.04226 (2023).

[17] Yong Cao, Li Zhou, Seolhwa Lee, Laura Cabello, Min Chen, and Daniel Hershcovich. 2023. Assessing cross-cultural alignment between

chatgpt and human societies: An empirical study. arXiv preprint arXiv:2303.17466 (2023).

[18] Marco Cascella, Jonathan Montomoli, Valentina Bellini, and Elena Bignami. 2023. Evaluating the feasibility of ChatGPT in healthcare:

an analysis of multiple clinical and research scenarios. Journal of Medical Systems 47, 1 (2023), 33.

[19] Yupeng Chang, Xu Wang, Jindong Wang, Yuan Wu, Kaijie Zhu, Hao Chen, Linyi Yang, Xiaoyuan Yi, Cunxiang Wang, Yidong Wang,

et al. 2023. A survey on evaluation of large language models. arXiv preprint arXiv:2307.03109 (2023).

[20] Harrison Chase. 2022. LangChain. https://github.com/hwchase17/langchain
[21] Lichang Chen, Jiuhai Chen, Tom Goldstein, Heng Huang, and Tianyi Zhou. 2023. InstructZero: Efficient Instruction Optimization for

Black-Box Large Language Models. arXiv preprint arXiv:2306.03082 (2023).

[22] Le Chen, Pei-Hung Lin, Tristan Vanderbruggen, Chunhua Liao, Murali Emani, and Bronis de Supinski. 2023. LM4HPC: Towards

Effective Language Model Application in High-Performance Computing. arXiv preprint arXiv:2306.14979 (2023).

[23] Lingjiao Chen, Matei Zaharia, and James Zou. 2023. FrugalGPT: How to Use Large Language Models While Reducing Cost and

Improving Performance. arXiv preprint arXiv:2305.05176 (2023).

[24] Weize Chen, Yusheng Su, Jingwei Zuo, Cheng Yang, Chenfei Yuan, Chen Qian, Chi-Min Chan, Yujia Qin, Yaxi Lu, Ruobing Xie, Zhiyuan
Liu, Maosong Sun, and Jie Zhou. 2023. AgentVerse: Facilitating Multi-Agent Collaboration and Exploring Emergent Behaviors in
Agents. arXiv:2308.10848 [cs.CL]

[25] Xuanting Chen, Junjie Ye, Can Zu, Nuo Xu, Rui Zheng, Minlong Peng, Jie Zhou, Tao Gui, Qi Zhang, and Xuanjing Huang. 2023. How
Robust is GPT-3.5 to Predecessors? A Comprehensive Study on Language Understanding Tasks. arXiv preprint arXiv:2303.00293 (2023).
[26] Ajay Kumar Chintala and Vignesh Aigal. [n. d.]. LLMStack: A platform to build and deploy LLM applications. https://github.com/

trypromptly/llmstack

[27] Aakanksha Chowdhery, Sharan Narang, Jacob Devlin, Maarten Bosma, Gaurav Mishra, Adam Roberts, Paul Barham, Hyung Won
Chung, Charles Sutton, Sebastian Gehrmann, Parker Schuh, Kensen Shi, Sasha Tsvyashchenko, Joshua Maynez, Abhishek Rao, Parker
Barnes, Yi Tay, Noam Shazeer, Vinodkumar Prabhakaran, Emily Reif, Nan Du, Ben Hutchinson, Reiner Pope, James Bradbury, Jacob
Austin, Michael Isard, Guy Gur-Ari, Pengcheng Yin, Toju Duke, Anselm Levskaya, Sanjay Ghemawat, Sunipa Dev, Henryk Michalewski,
Xavier Garcia, Vedant Misra, Kevin Robinson, Liam Fedus, Denny Zhou, Daphne Ippolito, David Luan, Hyeontaek Lim, Barret Zoph,
Alexander Spiridonov, Ryan Sepassi, David Dohan, Shivani Agrawal, Mark Omernick, Andrew M. Dai, Thanumalayan Sankaranarayana
Pillai, Marie Pellat, Aitor Lewkowycz, Erica Moreira, Rewon Child, Oleksandr Polozov, Katherine Lee, Zongwei Zhou, Xuezhi Wang,
Brennan Saeta, Mark Diaz, Orhan Firat, Michele Catasta, Jason Wei, Kathy Meier-Hellstern, Douglas Eck, Jeff Dean, Slav Petrov, and
Noah Fiedel. 2022. PaLM: Scaling Language Modeling with Pathways. arXiv:2204.02311 [cs.CL]

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

Prompting Frameworks for Large Language Models: A Survey •

31

[28] Hyung Won Chung, Le Hou, Shayne Longpre, Barret Zoph, Yi Tay, William Fedus, Eric Li, Xuezhi Wang, Mostafa Dehghani, Siddhartha

Brahma, et al. 2022. Scaling instruction-finetuned language models. arXiv preprint arXiv:2210.11416 (2022).

[29] Ronan Collobert, Jason Weston, Léon Bottou, Michael Karlen, Koray Kavukcuoglu, and Pavel Kuksa. 2011. Natural language processing

(almost) from scratch. Journal of machine learning research 12, ARTICLE (2011), 2493–2537.

[30] Wei Dai, Jionghao Lin, Flora Jin, Tongguang Li, Yi-Shan Tsai, Dragan Gasevic, and Guanliang Chen. 2023. Can large language models

provide feedback to students? A case study on ChatGPT. (2023).

[31] Gelei Deng, Yi Liu, Yuekang Li, Kailong Wang, Ying Zhang, Zefeng Li, Haoyu Wang, Tianwei Zhang, and Yang Liu. 2023. Jailbreaker:

Automated Jailbreak Across Multiple Large Language Model Chatbots. arXiv preprint arXiv:2307.08715 (2023).

[32] Ameet Deshpande, Vishvak Murahari, Tanmay Rajpurohit, Ashwin Kalyan, and Karthik Narasimhan. 2023. Toxicity in chatgpt:

Analyzing persona-assigned language models. arXiv preprint arXiv:2304.05335 (2023).

[33] Jacob Devlin, Ming-Wei Chang, Kenton Lee, and Kristina Toutanova. 2018. Bert: Pre-training of deep bidirectional transformers for

language understanding. arXiv preprint arXiv:1810.04805 (2018).

[34] Etienne Dilocker, Bob van Luijt, Byron Voorbach, Mohd Shukri Hasan, Abdel Rodriguez, Dirk Alexander Kulawiak, Marcin Antas, and

Parker Duckworth. [n. d.]. Weaviate. https://github.com/weaviate/weaviate

[35] Ning Ding, Shengding Hu, Weilin Zhao, Yulin Chen, Zhiyuan Liu, Hai-Tao Zheng, and Maosong Sun. 2021. OpenPrompt: An

Open-source Framework for Prompt-learning. arXiv preprint arXiv:2111.01998 (2021).

[36] Qingxiu Dong, Lei Li, Damai Dai, Ce Zheng, Zhiyong Wu, Baobao Chang, Xu Sun, Jingjing Xu, and Zhifang Sui. 2022. A survey for

in-context learning. arXiv preprint arXiv:2301.00234 (2022).

[37] Hongyang Du, Zonghang Li, Dusit Niyato, Jiawen Kang, Zehui Xiong, Dong In Kim, et al. 2023. Enabling AI-generated content (AIGC)

services in wireless edge networks. arXiv preprint arXiv:2301.03220 (2023).

[38] Yogesh K Dwivedi, Nir Kshetri, Laurie Hughes, Emma Louise Slade, Anand Jeyaraj, Arpan Kumar Kar, Abdullah M Baabdullah,
Alex Koohang, Vishnupriya Raghavan, Manju Ahuja, et al. 2023. “So what if ChatGPT wrote it?” Multidisciplinary perspectives on
opportunities, challenges and implications of generative conversational AI for research, practice and policy. International Journal of
Information Management 71 (2023), 102642.

[39] Chris Dzoba. 2023. GPTRPG. https://github.com/dzoba/gptrpg
[40] Eric Elliott. 2023. SudoLang. https://github.com/paralleldrive/sudolang-llm-support
[41] Emilio Ferrara. 2023. Should chatgpt be biased? challenges and risks of bias in large language models. arXiv preprint arXiv:2304.03738

(2023).

[42] Forethought-Technologies. [n. d.]. AutoChain. https://github.com/Forethought-Technologies/AutoChain
[43] Kai Greshake, Sahar Abdelnabi, Shailesh Mishra, Christoph Endres, Thorsten Holz, and Mario Fritz. 2023. More than you’ve asked
for: A Comprehensive Analysis of Novel Prompt Injection Threats to Application-Integrated Large Language Models. arXiv preprint
arXiv:2302.12173 (2023).

[44] griptape ai. 2023. Griptape. https://github.com/griptape-ai/griptape
[45] henomis. 2023. LinGoose. https://github.com/henomis/lingoose
[46] Sirui Hong, Xiawu Zheng, Jonathan Chen, Yuheng Cheng, Jinlin Wang, Ceyao Zhang, Zili Wang, Steven Ka Shing Yau, Zijuan Lin,
Liyang Zhou, Chenyu Ran, Lingfeng Xiao, and Chenglin Wu. 2023. MetaGPT: Meta Programming for Multi-Agent Collaborative
Framework. arXiv:2308.00352 [cs.AI]

[47] Edward J Hu, Yelong Shen, Phillip Wallis, Zeyuan Allen-Zhu, Yuanzhi Li, Shean Wang, Lu Wang, and Weizhu Chen. 2021. Lora:

Low-rank adaptation of large language models. arXiv preprint arXiv:2106.09685 (2021).

[48] InsuranceToolkits. 2023. PromptFlow. https://github.com/InsuranceToolkits/promptflow
[49] Neel Jain, Khalid Saifullah, Yuxin Wen, John Kirchenbauer, Manli Shu, Aniruddha Saha, Micah Goldblum, Jonas Geiping, and Tom
Goldstein. 2023. Bring Your Own Data! Self-Supervised Evaluation for Large Language Models. arXiv preprint arXiv:2306.13651 (2023).

[50] Frederick Jelinek. 1998. Statistical methods for speech recognition. MIT press.
[51] Takeshi Kojima, Shixiang Shane Gu, Machel Reid, Yutaka Matsuo, and Yusuke Iwasawa. 2022. Large language models are zero-shot

reasoners. Advances in neural information processing systems 35 (2022), 22199–22213.

[52] Sotiris B Kotsiantis, Ioannis Zaharakis, P Pintelas, et al. 2007. Supervised machine learning: A review of classification techniques.

Emerging artificial intelligence applications in computer engineering 160, 1 (2007), 3–24.

[53] John Lafferty, Andrew McCallum, and Fernando CN Pereira. 2001. Conditional random fields: Probabilistic models for segmenting and

labeling sequence data. (2001).

[54] Md Tahmid Rahman Laskar, M Saiful Bari, Mizanur Rahman, Md Amran Hossen Bhuiyan, Shafiq Joty, and Jimmy Xiangji Huang. 2023.
A Systematic Study and Comprehensive Evaluation of ChatGPT on Benchmark Datasets. arXiv preprint arXiv:2305.18486 (2023).
[55] Mike Lewis, Yinhan Liu, Naman Goyal, Marjan Ghazvininejad, Abdelrahman Mohamed, Omer Levy, Ves Stoyanov, and Luke Zettlemoyer.
2019. Bart: Denoising sequence-to-sequence pre-training for natural language generation, translation, and comprehension. arXiv
preprint arXiv:1910.13461 (2019).

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

32

• Xiaoxia Liu, Jingyi Wang, Jun Sun, Xiaohan Yuan, Guoliang Dong, Peng Di, Wenhai Wang, and Dongxia Wang*

[56] Aitor Lewkowycz, Anders Andreassen, David Dohan, Ethan Dyer, Henryk Michalewski, Vinay Ramasesh, Ambrose Slone, Cem Anil,
Imanol Schlag, Theo Gutman-Solo, et al. 2022. Solving quantitative reasoning problems with language models. Advances in Neural
Information Processing Systems 35 (2022), 3843–3857.

[57] Xinzhe Li, Ming Liu, Shang Gao, and Wray Buntine. 2023. A survey on out-of-distribution evaluation of neural nlp models. arXiv

preprint arXiv:2306.15261 (2023).

[58] Yen-Ting Lin and Yun-Nung Chen. 2023. LLM-Eval: Unified Multi-Dimensional Automatic Evaluation for Open-Domain Conversations

with Large Language Models. arXiv preprint arXiv:2305.13711 (2023).

[59] Jerry Liu. 2022. LlamaIndex. https://doi.org/10.5281/zenodo.1234
[60] Pengfei Liu, Weizhe Yuan, Jinlan Fu, Zhengbao Jiang, Hiroaki Hayashi, and Graham Neubig. 2023. Pre-train, prompt, and predict: A

systematic survey of prompting methods in natural language processing. Comput. Surveys 55, 9 (2023), 1–35.

[61] Siru Liu, Aileen P Wright, Barron L Patterson, Jonathan P Wanderer, Robert W Turer, Scott D Nelson, Allison B McCoy, Dean F Sittig,
and Adam Wright. 2023. Using AI-generated suggestions from ChatGPT to optimize clinical decision support. Journal of the American
Medical Informatics Association 30, 7 (2023), 1237–1245.

[62] Yi Liu, Gelei Deng, Yuekang Li, Kailong Wang, Tianwei Zhang, Yepang Liu, Haoyu Wang, Yan Zheng, and Yang Liu. 2023. Prompt

Injection attack against LLM-integrated Applications. arXiv preprint arXiv:2306.05499 (2023).

[63] Yinhan Liu, Myle Ott, Naman Goyal, Jingfei Du, Mandar Joshi, Danqi Chen, Omer Levy, Mike Lewis, Luke Zettlemoyer, and Veselin

Stoyanov. 2019. Roberta: A robustly optimized bert pretraining approach. arXiv preprint arXiv:1907.11692 (2019).

[64] Pan Lu, Baolin Peng, Hao Cheng, Michel Galley, Kai-Wei Chang, Ying Nian Wu, Song-Chun Zhu, and Jianfeng Gao. 2023. Chameleon:

Plug-and-play compositional reasoning with large language models. arXiv preprint arXiv:2304.09842 (2023).

[65] Brady D Lund, Ting Wang, Nishith Reddy Mannuru, Bing Nie, Somipam Shimray, and Ziang Wang. 2023. ChatGPT and a new academic
reality: Artificial Intelligence-written research papers and the ethics of the large language models in scholarly publishing. Journal of
the Association for Information Science and Technology 74, 5 (2023), 570–581.

[66] Kai Mei, Zheng Li, Zhenting Wang, Yang Zhang, and Shiqing Ma. 2023. NOTABLE: Transferable Backdoor Attacks Against Prompt-based

NLP Models. arXiv preprint arXiv:2305.17826 (2023).

[67] David Mezzetti. 2020. txtai: the all-in-one embeddings database. https://github.com/neuml/txtai
[68] Grégoire Mialon, Roberto Dessì, Maria Lomeli, Christoforos Nalmpantis, Ram Pasunuru, Roberta Raileanu, Baptiste Rozière, Timo
Schick, Jane Dwivedi-Yu, Asli Celikyilmaz, et al. 2023. Augmented language models: a survey. arXiv preprint arXiv:2302.07842 (2023).

[69] microsoft. 2023. Guidance. https://github.com/guidance-ai/guidance
[70] microsoft. 2023. TypeChat. https://github.com/microsoft/TypeChat
[71] Tomas Mikolov, Kai Chen, Greg Corrado, and Jeffrey Dean. 2013. Efficient estimation of word representations in vector space. arXiv

preprint arXiv:1301.3781 (2013).

[72] Tomas Mikolov, Martin Karafiát, Lukas Burget, Jan Cernock`y, and Sanjeev Khudanpur. 2010. Recurrent neural network based language

model.. In Interspeech, Vol. 2. Makuhari, 1045–1048.

[73] Tomas Mikolov, Ilya Sutskever, Kai Chen, Greg S Corrado, and Jeff Dean. 2013. Distributed representations of words and phrases and

their compositionality. Advances in neural information processing systems 26 (2013).

[74] Bonan Min, Hayley Ross, Elior Sulem, Amir Pouran Ben Veyseh, Thien Huu Nguyen, Oscar Sainz, Eneko Agirre, Ilana Heintz, and Dan
Roth. 2023. Recent Advances in Natural Language Processing via Large Pre-Trained Language Models: A Survey. ACM Comput. Surv.
56, 2, Article 30 (sep 2023), 40 pages. https://doi.org/10.1145/3605943

[75] Sewon Min, Xinxi Lyu, Ari Holtzman, Mikel Artetxe, Mike Lewis, Hannaneh Hajishirzi, and Luke Zettlemoyer. 2022. Rethinking the

role of demonstrations: What makes in-context learning work? arXiv preprint arXiv:2202.12837 (2022).

[76] Marta Montenegro-Rueda, José Fernández-Cerero, José María Fernández-Batanero, and Eloy López-Meneses. 2023. Impact of the

Implementation of ChatGPT in Education: A Systematic Review. Computers 12, 8 (2023), 153.

[77] Yohei Nakajima. 2023. BabyAGI. https://github.com/yoheinakajima/babyagi
[78] Reiichiro Nakano, Jacob Hilton, Suchir Balaji, Jeff Wu, Long Ouyang, Christina Kim, Christopher Hesse, Shantanu Jain, Vineet Kosaraju,
William Saunders, et al. 2021. Webgpt: Browser-assisted question-answering with human feedback. arXiv preprint arXiv:2112.09332
(2021).

[79] NVIDIA. 2023. NeMo-Guardrails. https://github.com/NVIDIA/NeMo-Guardrails
[80] Franz Josef Och, Daniel Gildea, Sanjeev Khudanpur, Anoop Sarkar, Kenji Yamada, Alexander Fraser, Shankar Kumar, Libin Shen,
David A Smith, Katherine Eng, et al. 2004. A smorgasbord of features for statistical machine translation. In Proceedings of the Human
Language Technology Conference of the North American Chapter of the Association for Computational Linguistics: HLT-NAACL 2004.
161–168.

[81] OpenAI. 2023. Evals. https://github.com/openai/evals
[82] OpenAI. 2023. GPT-4 Technical Report. arXiv:2303.08774 [cs.CL]
[83] OpenDAN.ai. 2023. OpenDAN. https://www.opendan.ai/

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

Prompting Frameworks for Large Language Models: A Survey •

33

[84] Jonas Oppenlaender and Joonas Hämäläinen. 2023. Mapping the Challenges of HCI: An Application and Evaluation of ChatGPT and

GPT-4 for Cost-Efficient Question Answering. arXiv preprint arXiv:2306.05036 (2023).

[85] Long Ouyang, Jeffrey Wu, Xu Jiang, Diogo Almeida, Carroll Wainwright, Pamela Mishkin, Chong Zhang, Sandhini Agarwal, Katarina
Slama, Alex Ray, et al. 2022. Training language models to follow instructions with human feedback. Advances in Neural Information
Processing Systems 35 (2022), 27730–27744.

[86] Ankit Pal. 2022. Promptify: Structured Output from LLMs. https://github.com/promptslab/Promptify. Prompt-Engineering components

for NLP tasks in Python.

[87] Rodrigo Pedro, Daniel Castro, Paulo Carreira, and Nuno Santos. 2023. From Prompt Injections to SQL Injection Attacks: How Protected

is Your LLM-Integrated Web Application? arXiv preprint arXiv:2308.01990 (2023).

[88] Baolin Peng, Chunyuan Li, Pengcheng He, Michel Galley, and Jianfeng Gao. 2023. Instruction tuning with gpt-4. arXiv preprint

arXiv:2304.03277 (2023).

[89] Fábio Perez and Ian Ribeiro. 2022. Ignore Previous Prompt: Attack Techniques For Language Models. https://doi.org/10.48550/ARXIV.

2211.09527

[90] Malte Pietsch, Timo Möller, Bogdan Kostic, Julian Risch, Massimiliano Pippi, Mayank Jobanputra, Sara Zanzottera, Silvano Cerza,
Vladimir Blagojevic, Thomas Stadelmann, Tanay Soni, and Sebastian Lee. 2019. Haystack: the end-to-end NLP framework for pragmatic
builders. https://github.com/deepset-ai/haystack

[91] Pinecone. 2023. Pinecone. https://github.com/pinecone-io
[92] Chengwei Qin, Aston Zhang, Zhuosheng Zhang, Jiaao Chen, Michihiro Yasunaga, and Diyi Yang. 2023. Is ChatGPT a general-purpose

natural language processing task solver? arXiv preprint arXiv:2302.06476 (2023).

[93] Yujia Qin, Shengding Hu, Yankai Lin, Weize Chen, Ning Ding, Ganqu Cui, Zheni Zeng, Yufei Huang, Chaojun Xiao, Chi Han, et al.

2023. Tool learning with foundation models. arXiv preprint arXiv:2304.08354 (2023).

[94] Alec Radford, Jeff Wu, Rewon Child, David Luan, Dario Amodei, and Ilya Sutskever. 2019. Language Models are Unsupervised Multitask

Learners. (2019).

[95] Colin Raffel, Noam Shazeer, Adam Roberts, Katherine Lee, Sharan Narang, Michael Matena, Yanqi Zhou, Wei Li, and Peter J Liu. 2020.
Exploring the limits of transfer learning with a unified text-to-text transformer. The Journal of Machine Learning Research 21, 1 (2020),
5485–5551.

[96] reworkd. 2023. AgentGPT. https://github.com/reworkd/AgentGPT
[97] Matt Rickard. 2023. ReLLM. https://github.com/r2d4/rellm
[98] Ronald Rosenfeld. 2000. Two decades of statistical language modeling: Where do we go from here? Proc. IEEE 88, 8 (2000), 1270–1278.
[99] ruvnet. 2023. PromptLang. https://github.com/ruvnet/promptlang
[100] Justyna Sarzynska-Wawer, Aleksander Wawer, Aleksandra Pawlak, Julia Szymanowska, Izabela Stefaniak, Michal Jarkiewicz, and
Lukasz Okruszek. 2021. Detecting formal thought disorder by deep contextualized word representations. Psychiatry Research 304
(2021), 114135.

[101] Sentdex. 2023. TermGPT. https://github.com/Sentdex/TermGPT
[102] ShreyaR. 2023. Guardrails. https://github.com/ShreyaR/guardrails
[103] Significant Gravitas. [n. d.]. Auto-GPT. https://github.com/Significant-Gravitas/Auto-GPT
[104] Taranjeet Singh. 2023. Embedchain. https://github.com/embedchain/embedchain
[105] sobelio. 2023. llm-chain. https://github.com/sobelio/llm-chain
[106] Scott M Thede and Mary Harper. 1999. A second-order hidden Markov model for part-of-speech tagging. In Proceedings of the 37th

annual meeting of the Association for Computational Linguistics. 175–182.

[107] TimPietrusky. [n. d.]. Hyv. https://github.com/failfa-st/hyv
[108] Hugo Touvron, Thibaut Lavril, Gautier Izacard, Xavier Martinet, Marie-Anne Lachaux, Timothée Lacroix, Baptiste Rozière, Naman
Goyal, Eric Hambro, Faisal Azhar, et al. 2023. Llama: Open and efficient foundation language models. arXiv preprint arXiv:2302.13971
(2023).

[109] Hugo Touvron, Louis Martin, Kevin Stone, Peter Albert, Amjad Almahairi, Yasmine Babaei, Nikolay Bashlykov, Soumya Batra, Prajjwal
Bhargava, Shruti Bhosale, et al. 2023. Llama 2: Open foundation and fine-tuned chat models. arXiv preprint arXiv:2307.09288 (2023).

[110] TransformerOptimus. 2023. SuperAGI. https://github.com/TransformerOptimus/SuperAGI
[111] Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N Gomez, Łukasz Kaiser, and Illia Polosukhin. 2017.

Attention is all you need. Advances in neural information processing systems 30 (2017).
[112] Gil LaHaye Vic Perdana. 2023. Semantic-kernel. https://github.com/microsoft/semantic-kernel
[113] Jindong Wang, Xixu Hu, Wenxin Hou, Hao Chen, Runkai Zheng, Yidong Wang, Linyi Yang, Haojun Huang, Wei Ye, Xiubo Geng, et al.
2023. On the robustness of chatgpt: An adversarial and out-of-distribution perspective. arXiv preprint arXiv:2302.12095 (2023).
[114] Jianguo Wang, Xiaomeng Yi, Rentong Guo, Hai Jin, Peng Xu, Shengjun Li, Xiangyu Wang, Xiangzhou Guo, Chengming Li, Xiaohai
Xu, et al. 2021. Milvus: A Purpose-Built Vector Data Management System. In Proceedings of the 2021 International Conference on
Management of Data. 2614–2627.

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

34

• Xiaoxia Liu, Jingyi Wang, Jun Sun, Xiaohan Yuan, Guoliang Dong, Peng Di, Wenhai Wang, and Dongxia Wang*

[115] Xinlong Wang, Wen Wang, Yue Cao, Chunhua Shen, and Tiejun Huang. 2023. Images speak in images: A generalist painter for
in-context visual learning. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition. 6830–6839.
[116] Yizhong Wang, Yeganeh Kordi, Swaroop Mishra, Alisa Liu, Noah A Smith, Daniel Khashabi, and Hannaneh Hajishirzi. 2022. Self-instruct:

Aligning language model with self generated instructions. arXiv preprint arXiv:2212.10560 (2022).

[117] Taylor Webb, Keith J Holyoak, and Hongjing Lu. 2023. Emergent analogical reasoning in large language models. Nature Human

Behaviour (2023), 1–16.

[118] Alexander Wei, Nika Haghtalab, and Jacob Steinhardt. 2023. Jailbroken: How does llm safety training fail? arXiv preprint arXiv:2307.02483

(2023).

[119] Jason Wei, Yi Tay, Rishi Bommasani, Colin Raffel, Barret Zoph, Sebastian Borgeaud, Dani Yogatama, Maarten Bosma, Denny Zhou,

Donald Metzler, et al. 2022. Emergent abilities of large language models. arXiv preprint arXiv:2206.07682 (2022).

[120] Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Fei Xia, Ed Chi, Quoc V Le, Denny Zhou, et al. 2022. Chain-of-thought
prompting elicits reasoning in large language models. Advances in Neural Information Processing Systems 35 (2022), 24824–24837.
[121] Jerry Wei, Jason Wei, Yi Tay, Dustin Tran, Albert Webson, Yifeng Lu, Xinyun Chen, Hanxiao Liu, Da Huang, Denny Zhou, et al. 2023.

Larger language models do in-context learning differently. arXiv preprint arXiv:2303.03846 (2023).

[122] Thomas Wolf, Lysandre Debut, Victor Sanh, Julien Chaumond, Clement Delangue, Anthony Moi, Perric Cistac, Clara Ma, Yacine Jernite,
Julien Plu, Canwen Xu, Teven Le Scao, Sylvain Gugger, Mariama Drame, Quentin Lhoest, and Alexander M. Rush. 2020. Transformers:
State-of-the-Art Natural Language Processing. Association for Computational Linguistics, 38–45. https://www.aclweb.org/anthology/
2020.emnlp-demos.6

[123] Changrong Xiao, Sean Xin Xu, Kunpeng Zhang, Yufang Wang, and Lei Xia. 2023. Evaluating Reading Comprehension Exercises
Generated by LLMs: A Showcase of ChatGPT in Education Applications. In Proceedings of the 18th Workshop on Innovative Use of NLP
for Building Educational Applications (BEA 2023). 610–625.

[124] Tianbao Xie, Zhoujun Cheng, Yiheng Xu, Peng Shi, and Tao Yu. 2022. A framework for human-readable prompt-based method with large

language models.

[125] Jun Yan, Vikas Yadav, Shiyang Li, Lichang Chen, Zheng Tang, Hai Wang, Vijay Srinivasan, Xiang Ren, and Hongxia Jin. 2023. Virtual

Prompt Injection for Instruction-Tuned Large Language Models. arXiv preprint arXiv:2307.16888 (2023).

[126] Jingfeng Yang, Hongye Jin, Ruixiang Tang, Xiaotian Han, Qizhang Feng, Haoming Jiang, Bing Yin, and Xia Hu. 2023. Harnessing the

power of llms in practice: A survey on chatgpt and beyond. arXiv preprint arXiv:2304.13712 (2023).

[127] Xianjun Yang, Yan Li, Xinlu Zhang, Haifeng Chen, and Wei Cheng. 2023. Exploring the limits of chatgpt for query or aspect-based text

summarization. arXiv preprint arXiv:2302.08081 (2023).

[128] Zhilin Yang, Zihang Dai, Yiming Yang, Jaime Carbonell, Russ R Salakhutdinov, and Quoc V Le. 2019. Xlnet: Generalized autoregressive

pretraining for language understanding. Advances in neural information processing systems 32 (2019).

[129] Shunyu Yao, Dian Yu, Jeffrey Zhao, Izhak Shafran, Thomas L Griffiths, Yuan Cao, and Karthik Narasimhan. 2023. Tree of thoughts:

Deliberate problem solving with large language models. arXiv preprint arXiv:2305.10601 (2023).

[130] yzfly. 2023. LangGPT. https://github.com/yzfly/LangGPT
[131] Zhanpeng Zeng, Cole Hawkins, Mingyi Hong, Aston Zhang, Nikolaos Pappas, Vikas Singh, and Shuai Zheng. 2023. Vcc: Scaling

Transformers to 128K Tokens or More by Prioritizing Important Tokens. arXiv preprint arXiv:2305.04241 (2023).

[132] Zetaphor. 2023. Zep. https://github.com/getzep/zep
[133] Chaoning Zhang, Chenshuang Zhang, Chenghao Li, Yu Qiao, Sheng Zheng, Sumit Kumar Dam, Mengchun Zhang, Jung Uk Kim,
Seong Tae Kim, Jinwoo Choi, et al. 2023. One small step for generative ai, one giant leap for agi: A complete survey on chatgpt in aigc
era. arXiv preprint arXiv:2304.06488 (2023).

[134] Chaoning Zhang, Chenshuang Zhang, Sheng Zheng, Yu Qiao, Chenghao Li, Mengchun Zhang, Sumit Kumar Dam, Chu Myaet Thwal,
Ye Lin Tun, Le Luang Huy, et al. 2023. A complete survey on generative ai (aigc): Is chatgpt from gpt-4 to gpt-5 all you need? arXiv
preprint arXiv:2303.11717 (2023).

[135] Wayne Xin Zhao, Kun Zhou, Junyi Li, Tianyi Tang, Xiaolei Wang, Yupeng Hou, Yingqian Min, Beichen Zhang, Junjie Zhang, Zican

Dong, et al. 2023. A survey of large language models. arXiv preprint arXiv:2303.18223 (2023).

[136] Denny Zhou, Nathanael Schärli, Le Hou, Jason Wei, Nathan Scales, Xuezhi Wang, Dale Schuurmans, Claire Cui, Olivier Bousquet, Quoc
Le, et al. 2022. Least-to-most prompting enables complex reasoning in large language models. arXiv preprint arXiv:2205.10625 (2022).
[137] Jiaming Zhou, Tengyue Li, Simon James Fong, Nilanjan Dey, and Rubén González Crespo. 2023. Exploring chatGPT’S potential for
consultation, recommendations and report diagnosis: Gastric cancer and gastroscopy reports’ case. IJIMAI 8, 2 (2023), 7–13.
[138] Kaijie Zhu, Jindong Wang, Jiaheng Zhou, Zichen Wang, Hao Chen, Yidong Wang, Linyi Yang, Wei Ye, Neil Zhenqiang Gong, Yue Zhang,
et al. 2023. PromptBench: Towards Evaluating the Robustness of Large Language Models on Adversarial Prompts. arXiv preprint
arXiv:2306.04528 (2023).

[139] zilliztech. 2023. GPTCache. https://github.com/zilliztech/GPTCache

ACM Comput. Surv., Vol. 1, No. 1, Article . Publication date: November 2023.

