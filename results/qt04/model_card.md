---
license: gemma
library_name: transformers
pipeline_tag: text-generation
extra_gated_button_content: Acknowledge license
tags:
- conversational
language:
- ar
- en
model-index:
  - name: SILMA-9B-Instruct-v1.0
    results:
      - task:
          type: text-generation
        dataset:
          name: Arabic Broad Benchmark (ABB)
          type: silma-ai/arabic-broad-benchmark
        metrics:
          - name: benchmark_score
            type: acc (1-10)
            value: 6.15
        source:
          name: Arabic Broad Leaderboard (ABL)
          url: https://huggingface.co/spaces/silma-ai/Arabic-LLM-Broad-Leaderboard
    
      - task:
          type: text-generation
        dataset:
          name: MMLU (Arabic)
          type: OALL/Arabic_MMLU
        metrics:
          - name: acc_norm
            type: loglikelihood_acc_norm
            value: 52.55
        source:
          name: Open Arabic LLM Leaderboard
          url: https://huggingface.co/spaces/OALL/Open-Arabic-LLM-Leaderboard-v1
      - task:
          type: text-generation
        dataset:
          name: AlGhafa
          type: OALL/AlGhafa-Arabic-LLM-Benchmark-Native
        metrics:
          - name: acc_norm
            type: loglikelihood_acc_norm
            value: 71.85
        source:
          name: Open Arabic LLM Leaderboard
          url: https://huggingface.co/spaces/OALL/Open-Arabic-LLM-Leaderboard-v1
      - task:
          type: text-generation
        dataset:
          name: ARC Challenge (Arabic)
          type: OALL/AlGhafa-Arabic-LLM-Benchmark-Translated
        metrics:
          - name: acc_norm
            type: loglikelihood_acc_norm
            value: 78.19
        source:
          name: Open Arabic LLM Leaderboard
          url: https://huggingface.co/spaces/OALL/Open-Arabic-LLM-Leaderboard-v1
      - task:
          type: text-generation
        dataset:
          name: ACVA
          type: OALL/ACVA
        metrics:
          - name: acc_norm
            type: loglikelihood_acc_norm
            value: 78.89
        source:
          name: Open Arabic LLM Leaderboard
          url: https://huggingface.co/spaces/OALL/Open-Arabic-LLM-Leaderboard-v1
      - task:
          type: text-generation
        dataset:
          name: Arabic_EXAMS
          type: OALL/Arabic_EXAMS
        metrics:
          - name: acc_norm
            type: loglikelihood_acc_norm
            value: 51.4
        source:
          name: Open Arabic LLM Leaderboard
          url: https://huggingface.co/spaces/OALL/Open-Arabic-LLM-Leaderboard-v1
      - task:
          type: text-generation
        dataset:
          name: ARC Easy
          type: OALL/AlGhafa-Arabic-LLM-Benchmark-Translated
        metrics:
          - name: acc_norm
            type: loglikelihood_acc_norm
            value: 86
        source:
          name: Open Arabic LLM Leaderboard
          url: https://huggingface.co/spaces/OALL/Open-Arabic-LLM-Leaderboard-v1
      - task:
          type: text-generation
        dataset:
          name: BOOLQ (Arabic)
          type: OALL/AlGhafa-Arabic-LLM-Benchmark-Translated
        metrics:
          - name: acc_norm
            type: loglikelihood_acc_norm
            value: 64.05
        source:
          name: Open Arabic LLM Leaderboard
          url: https://huggingface.co/spaces/OALL/Open-Arabic-LLM-Leaderboard-v1
      - task:
          type: text-generation
        dataset:
          name: COPA (Arabic)
          type: OALL/AlGhafa-Arabic-LLM-Benchmark-Translated
        metrics:
          - name: acc_norm
            type: loglikelihood_acc_norm
            value: 78.89
        source:
          name: Open Arabic LLM Leaderboard
          url: https://huggingface.co/spaces/OALL/Open-Arabic-LLM-Leaderboard-v1
      - task:
          type: text-generation
        dataset:
          name: HELLASWAG (Arabic)
          type: OALL/AlGhafa-Arabic-LLM-Benchmark-Translated
        metrics:
          - name: acc_norm
            type: loglikelihood_acc_norm
            value: 47.64
        source:
          name: Open Arabic LLM Leaderboard
          url: https://huggingface.co/spaces/OALL/Open-Arabic-LLM-Leaderboard-v1
      - task:
          type: text-generation
        dataset:
          name: OPENBOOK QA (Arabic)
          type: OALL/AlGhafa-Arabic-LLM-Benchmark-Translated
        metrics:
          - name: acc_norm
            type: loglikelihood_acc_norm
            value: 72.93
        source:
          name: Open Arabic LLM Leaderboard
          url: https://huggingface.co/spaces/OALL/Open-Arabic-LLM-Leaderboard-v1
      - task:
          type: text-generation
        dataset:
          name: PIQA (Arabic)
          type: OALL/AlGhafa-Arabic-LLM-Benchmark-Translated
        metrics:
          - name: acc_norm
            type: loglikelihood_acc_norm
            value: 71.96
        source:
          name: Open Arabic LLM Leaderboard
          url: https://huggingface.co/spaces/OALL/Open-Arabic-LLM-Leaderboard-v1
      - task:
          type: text-generation
        dataset:
          name: RACE (Arabic)
          type: OALL/AlGhafa-Arabic-LLM-Benchmark-Translated
        metrics:
          - name: acc_norm
            type: loglikelihood_acc_norm
            value: 75.55
        source:
          name: Open Arabic LLM Leaderboard
          url: https://huggingface.co/spaces/OALL/Open-Arabic-LLM-Leaderboard-v1
      - task:
          type: text-generation
        dataset:
          name: SCIQ (Arabic)
          type: OALL/AlGhafa-Arabic-LLM-Benchmark-Translated
        metrics:
          - name: acc_norm
            type: loglikelihood_acc_norm
            value: 91.26
        source:
          name: Open Arabic LLM Leaderboard
          url: https://huggingface.co/spaces/OALL/Open-Arabic-LLM-Leaderboard-v1
      - task:
          type: text-generation
        dataset:
          name: TOXIGEN (Arabic)
          type: OALL/AlGhafa-Arabic-LLM-Benchmark-Translated
        metrics:
          - name: acc_norm
            type: loglikelihood_acc_norm
            value: 67.59
        source:
          name: Open Arabic LLM Leaderboard
          url: https://huggingface.co/spaces/OALL/Open-Arabic-LLM-Leaderboard-v1
      - task:
          type: text-generation
          name: Text Generation
        dataset:
          name: IFEval (0-Shot)
          type: HuggingFaceH4/ifeval
          args:
            num_few_shot: 0
        metrics:
        - type: inst_level_strict_acc and prompt_level_strict_acc
          value: 58.42
          name: strict accuracy
        source:
          url: https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard?query=silma-ai/SILMA-9B-Instruct-v1.0
          name: Open LLM Leaderboard
      - task:
          type: text-generation
          name: Text Generation
        dataset:
          name: BBH (3-Shot)
          type: BBH
          args:
            num_few_shot: 3
        metrics:
        - type: acc_norm
          value: 30.71
          name: normalized accuracy
        source:
          url: https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard?query=silma-ai/SILMA-9B-Instruct-v1.0
          name: Open LLM Leaderboard
      - task:
          type: text-generation
          name: Text Generation
        dataset:
          name: MATH Lvl 5 (4-Shot)
          type: hendrycks/competition_math
          args:
            num_few_shot: 4
        metrics:
        - type: exact_match
          value: 0.0
          name: exact match
        source:
          url: https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard?query=silma-ai/SILMA-9B-Instruct-v1.0
          name: Open LLM Leaderboard
      - task:
          type: text-generation
          name: Text Generation
        dataset:
          name: GPQA (0-shot)
          type: Idavidrein/gpqa
          args:
            num_few_shot: 0
        metrics:
        - type: acc_norm
          value: 7.38
          name: acc_norm
        source:
          url: https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard?query=silma-ai/SILMA-9B-Instruct-v1.0
          name: Open LLM Leaderboard
      - task:
          type: text-generation
          name: Text Generation
        dataset:
          name: MuSR (0-shot)
          type: TAUR-Lab/MuSR
          args:
            num_few_shot: 0
        metrics:
        - type: acc_norm
          value: 17.26
          name: acc_norm
        source:
          url: https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard?query=silma-ai/SILMA-9B-Instruct-v1.0
          name: Open LLM Leaderboard
      - task:
          type: text-generation
          name: Text Generation
        dataset:
          name: MMLU-PRO (5-shot)
          type: TIGER-Lab/MMLU-Pro
          config: main
          split: test
          args:
            num_few_shot: 5
        metrics:
        - type: acc
          value: 32.44
          name: accuracy
        source:
          url: https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard?query=silma-ai/SILMA-9B-Instruct-v1.0
          name: Open LLM Leaderboard


          
---


# SILMA AI

SILMA.AI is a leading Generative AI startup dedicated to empowering Arabic speakers with state-of-the-art AI solutions. 


## 🚀 Our Flagship Model: SILMA 1.0 🚀

* **SILMA 1.0** was the **TOP-RANKED** open-weights Arabic LLM (Until February 2025) with an impressive **9 billion parameter size**, surpassing models that are over seven times larger 🏆

**Important Tip:** 💡 For RAG use-cases please use [SILMA Kashif v1.0](https://huggingface.co/silma-ai/SILMA-Kashif-2B-Instruct-v1.0) as it has been specifically trained for Question Answering tasks.


## What makes SILMA exceptional?

* SIMLA is a small language model outperforming 72B models in most arabic language tasks, thus more practical for business use-cases
* SILMA is built over the robust foundational models of Google Gemma, combining the strengths of both to provide you with unparalleled performance
* SILMA is an open-weight model, free to use in accordance with our open license


## 👥 Our Team

We are a team of seasoned **Arabic AI experts** who understand the nuances of the language and cultural considerations, enabling us to build solutions that truly resonate with Arabic users.

**Authors**: [silma.ai](https://silma.ai)


### Usage

Below we share some code snippets on how to get quickly started with running the model. First, install the Transformers library with:

```sh
pip install -U transformers sentencepiece
```

Then, copy the snippet from the section that is relevant for your usecase.

#### Running with the `pipeline` API

```python
import torch
from transformers import pipeline

pipe = pipeline(
    "text-generation",
    model="silma-ai/SILMA-9B-Instruct-v1.0",
    model_kwargs={"torch_dtype": torch.bfloat16},
    device="cuda",  # replace with "mps" to run on a Mac device
)

messages = [
    {"role": "user", "content": "اكتب رسالة تعتذر فيها لمديري في العمل عن الحضور اليوم لأسباب مرضية."},
]

outputs = pipe(messages, max_new_tokens=256)
assistant_response = outputs[0]["generated_text"][-1]["content"].strip()
print(assistant_response)
```

- Response:

```text
السلام عليكم ورحمة الله وبركاته

أودّ أن أعتذر عن عدم الحضور إلى العمل اليوم بسبب مرضي. أشعر بالسوء الشديد وأحتاج إلى الراحة. سأعود إلى العمل فور تعافيي.
شكراً لتفهمكم.

مع تحياتي،
[اسمك]
```

#### Running the model on a single / multi GPU

```sh
pip install accelerate
```

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_id = "silma-ai/SILMA-9B-Instruct-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    torch_dtype=torch.bfloat16,
)

messages = [
    {"role": "system", "content": "أنت مساعد ذكي للإجابة عن أسئلة المستخدمين."},
    {"role": "user", "content": "أيهما أبعد عن الأرض, الشمس أم القمر؟"},
]

input_ids = tokenizer.apply_chat_template(messages, return_tensors="pt", return_dict=True).to("cuda")

outputs = model.generate(**input_ids, max_new_tokens=256)

print(tokenizer.decode(outputs[0]))
```

- Response:
```text
الشمس
```

You can ensure the correct chat template is applied by using `tokenizer.apply_chat_template` as follows:
```python

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_id = "silma-ai/SILMA-9B-Instruct-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    torch_dtype=torch.bfloat16,
)

messages = [
    {"role": "system", "content": "أنت مساعد ذكي للإجابة عن أسئلة المستخدمين."},
    {"role": "user", "content": "اكتب كود بايثون لتوليد متسلسلة أرقام زوجية."},
]
input_ids = tokenizer.apply_chat_template(messages, return_tensors="pt", return_dict=True).to("cuda")

outputs = model.generate(**input_ids, max_new_tokens=256)
print(tokenizer.decode(outputs[0]).split("<start_of_turn>model")[-1])
```

- Response:
```python
def generate_even_numbers(n):
	"""
	This function generates a list of even numbers from 1 to n.
	Args:
		n: The upper limit of the range.

	Returns:
		A list of even numbers.
	"""
	return [i for i in range(1, n + 1) if i % 2 == 0]

# Example usage
n = 10
even_numbers = generate_even_numbers(n)
print(f"The first {n} even numbers are: {even_numbers}")
```

#### Quantized Versions through `bitsandbytes`

<details>
  <summary>
    Using 8-bit precision (int8)  
  </summary>

```sh
pip install bitsandbytes accelerate
```

```python
# pip install bitsandbytes accelerate
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

model_id = "silma-ai/SILMA-9B-Instruct-v1.0"
quantization_config = BitsAndBytesConfig(load_in_8bit=True)

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=quantization_config,
)

messages = [
    {"role": "system", "content": "أنت مساعد ذكي للإجابة عن أسئلة المستخدمين."},
    {"role": "user", "content": "اذكر خمس انواع فواكه بها نسب عالية من فيتامين ج."},
]
input_ids = tokenizer.apply_chat_template(messages, return_tensors="pt", return_dict=True).to("cuda")

outputs = model.generate(**input_ids, max_new_tokens=256)
print(tokenizer.decode(outputs[0]).split("<start_of_turn>model")[-1])
```

- Response:
```text
الليمون، البرتقال، الموز، الكيوي، الفراولة
```

</details>

<details>
  <summary>
    Using 4-bit precision  
  </summary>

```python
# pip install bitsandbytes accelerate
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

model_id = "silma-ai/SILMA-9B-Instruct-v1.0"
quantization_config = BitsAndBytesConfig(load_in_4bit=True)

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=quantization_config,
)

messages = [
    {"role": "system", "content": "أنت مساعد ذكي للإجابة عن أسئلة المستخدمين."},
    {"role": "user", "content": "في أي عام توفى صلاح الدين الأيوبي؟"},
]
input_ids = tokenizer.apply_chat_template(messages, return_tensors="pt", return_dict=True).to("cuda")

outputs = model.generate(**input_ids, max_new_tokens=256)
print(tokenizer.decode(outputs[0]).split("<start_of_turn>model")[-1])
```

- Response:
```text
1193
```

</details>

#### Advanced Usage

<details>
  <summary>
    Torch compile  
  </summary>

[Torch compile](https://pytorch.org/tutorials/intermediate/torch_compile_tutorial.html) is a method for speeding-up the 
inference of PyTorch modules. The Silma model can be run up to 6x faster by leveraging torch compile.

Note that two warm-up steps are required before the full inference speed is realised:

```python
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from transformers import AutoTokenizer, Gemma2ForCausalLM
from transformers.cache_utils import HybridCache
import torch

torch.set_float32_matmul_precision("high")

# load the model + tokenizer
model_id = "silma-ai/SILMA-9B-Instruct-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = Gemma2ForCausalLM.from_pretrained(model_id, torch_dtype=torch.bfloat16)
model.to("cuda")

# apply the torch compile transformation
model.forward = torch.compile(model.forward, mode="reduce-overhead", fullgraph=True)

# pre-process inputs

messages = [
    {"role": "system", "content": "أنت مساعد ذكي للإجابة عن أسئلة المستخدمين."},
    {"role": "user", "content": "من الرئيس الذي تولى المنصب في أمريكا بعد دونالد ترامب؟"},
]
model_inputs = tokenizer.apply_chat_template(messages, return_tensors="pt", return_dict=True).to("cuda")

input_text = "من الرئيس الذي تولى المنصب في أمريكا بعد دونالد ترامب؟"
model_inputs = tokenizer(input_text, return_tensors="pt").to("cuda")
prompt_length = model_inputs.input_ids.shape[1]

# set-up k/v cache
past_key_values = HybridCache(
    config=model.config,
    max_batch_size=1,
    max_cache_len=model.config.max_position_embeddings,
    device=model.device,
    dtype=model.dtype
)

# enable passing kv cache to generate
model._supports_cache_class = True
model.generation_config.cache_implementation = None

# two warm-up steps
for idx in range(2):
    outputs = model.generate(**model_inputs, past_key_values=past_key_values, do_sample=True, temperature=1.0, max_new_tokens=128)
    past_key_values.reset()

# fast run
outputs = model.generate(**model_inputs, past_key_values=past_key_values, do_sample=True, temperature=1.0, max_new_tokens=128)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

- Response:
```text
جو بايدن
```

For more details, refer to the [Transformers documentation](https://huggingface.co/docs/transformers/main/en/llm_optims?static-kv=basic+usage%3A+generation_config).

</details>

### Chat Template

The instruction-tuned models use a chat template that must be adhered to for conversational use.
The easiest way to apply it is using the tokenizer's built-in chat template, as shown in the following snippet.

Let's load the model and apply the chat template to a conversation. In this example, we'll start with a single user interaction:

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import transformers
import torch

model_id = "silma-ai/SILMA-9B-Instruct-v1.0"
dtype = torch.bfloat16

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="cuda",
    torch_dtype=dtype,)

chat = [
    { "role": "user", "content": "ما اشهر اطارات العمل في البايثون لبناء نماذج الذكاء الاصطناعي؟" },
]
prompt = tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
```

At this point, the prompt contains the following text:

```
<bos><start_of_turn>user
ما اشهر اطارات العمل في البايثون لبناء نماذج الذكاء الاصطناعي؟<end_of_turn>
<start_of_turn>model
```

As you can see, each turn is preceded by a `<start_of_turn>` delimiter and then the role of the entity
(either `user`, for content supplied by the user, or `model` for LLM responses). Turns finish with
the `<end_of_turn>` token.

You can follow this format to build the prompt manually, if you need to do it without the tokenizer's
chat template.

After the prompt is ready, generation can be performed like this:

```python
inputs = tokenizer.encode(prompt, add_special_tokens=False, return_tensors="pt")
outputs = model.generate(input_ids=inputs.to(model.device), max_new_tokens=150)
print(tokenizer.decode(outputs[0]))
```

### Inputs and outputs

*   **Input:** Text string, such as a question, a prompt, or a document to be
    summarized.
*   **Output:** Generated Arabic or English text in response to the input, such
    as an answer to a question, or a summary of a document.


### GPU Requirements

The following are the minimum/recommended GPU requirements for running inference:
 
* Recommended
  * At least one GPU with a minimum of 48 GB of GPU memory
  * Examples: Nvidia A40, L40, RTX A6000

* Minimum

  * At least one GPU with 16-24 GB of GPU memory
  * Examples: Nvidia RTX 4090, RTX 4000, L4
  * Assuming that the model is loaded in either 8-bit or 4-bit [Quantization mode](https://huggingface.co/silma-ai/SILMA-9B-Instruct-v1.0#quantized-versions-through-bitsandbytes)


### Citation

```bibtex
@misc{silma-9b-2024,
  author       = {{silma-ai}},
  title        = {SILMA 9B Instruct v1.0},
  year         = {2024},
  howpublished = {\url{https://huggingface.co/silma-ai/SILMA-9B-Instruct-v1.0}}
}
```

## Usage and Limitations

These models have certain limitations that users should be aware of.

### Intended Usage

Open Large Language Models (LLMs) have a wide range of applications across
various industries and domains. The following list of potential uses is not
comprehensive. The purpose of this list is to provide contextual information
about the possible use-cases that the model creators considered as part of model
training and development.

* Content Creation and Communication
  * Text Generation: These models can be used to generate creative text formats
    such as poems, scripts, code, marketing copy, and email drafts.
  * Chatbots and Conversational AI: Power conversational interfaces for customer
    service, virtual assistants, or interactive applications.
  * Text Summarization: Generate concise summaries of a text corpus, research
    papers, or reports.
* Research and Education
  * Natural Language Processing (NLP) Research: These models can serve as a
    foundation for researchers to experiment with NLP techniques, develop
    algorithms, and contribute to the advancement of the field.
  * Language Learning Tools: Support interactive language learning experiences,
    aiding in grammar correction or providing writing practice.
  * Knowledge Exploration: Assist researchers in exploring large bodies of text
    by generating summaries or answering questions about specific topics.

### Limitations

* Training Data
  * The quality and diversity of the training data significantly influence the
    model's capabilities. Biases or gaps in the training data can lead to
    limitations in the model's responses.
  * The scope of the training dataset determines the subject areas the model can
    handle effectively.
* Context and Task Complexity
  * LLMs are better at tasks that can be framed with clear prompts and
    instructions. Open-ended or highly complex tasks might be challenging.
  * A model's performance can be influenced by the amount of context provided
    (longer context generally leads to better outputs, up to a certain point).
* Language Ambiguity and Nuance
  * Natural language is inherently complex. LLMs might struggle to grasp subtle
    nuances, sarcasm, or figurative language.
* Factual Accuracy
  * LLMs generate responses based on information they learned from their
    training datasets, but they are not knowledge bases. They may generate
    incorrect or outdated factual statements.
* Common Sense
  * LLMs rely on statistical patterns in language. They might lack the ability
    to apply common sense reasoning in certain situations.

### Ethical Considerations and Risks

The development of large language models (LLMs) raises several ethical concerns.
In creating an open model, we have carefully considered the following:

* Bias and Fairness
  * LLMs trained on large-scale, real-world text data can reflect socio-cultural
    biases embedded in the training material.
* Misinformation and Misuse
  * LLMs can be misused to generate text that is false, misleading, or harmful.
  * Guidelines are provided for responsible use with the model, see the
    [Responsible Generative AI Toolkit][rai-toolkit].
* Transparency and Accountability:
  * This model card summarizes details on the models' architecture,
    capabilities, limitations, and evaluation processes.
  * A responsibly developed open model offers the opportunity to share
    innovation by making LLM technology accessible to developers and researchers
    across the AI ecosystem.

Risks identified and mitigations:

* Perpetuation of biases: It's encouraged to perform continuous monitoring
  (using evaluation metrics, human review) and the exploration of de-biasing
  techniques during model training, fine-tuning, and other use cases.
* Generation of harmful content: Mechanisms and guidelines for content safety
  are essential. Developers are encouraged to exercise caution and implement
  appropriate content safety safeguards based on their specific product policies
  and application use cases.
* Privacy violations: Models were trained on data filtered for removal of PII
  (Personally Identifiable Information). Developers are encouraged to adhere to
  privacy regulations with privacy-preserving techniques.