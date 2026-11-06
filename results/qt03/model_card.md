---
license: apache-2.0
language:
- ar
- en
pipeline_tag: text-generation
tags:
- pytorch
library_name: transformers
base_model: google/gemma-3-27b-pt
---

<p align="center">
  <img src="./assets/fanar_logo.jpg" width="200"/>
</p>

# Fanar-2-27B-Instruct

**Fanar-2-27B-Instruct** is an advanced Arabic-English LLM developed by [Qatar Computing Research Institute (QCRI)](https://www.hbku.edu.qa/en/qcri) at [Hamad Bin Khalifa University (HBKU)](https://www.hbku.edu.qa/), a member of Qatar Foundation for Education, Science, and Community Development. It is part of the **Fanar 2.0 release**, a comprehensive Arabic-centric multimodal generative AI platform that includes specialized models for [image generation](https://huggingface.co/QCRI/Fanar-2-Oryx-IG), [image understanding](https://huggingface.co/QCRI/Fanar-2-Oryx-IVU), and [poetry generation](https://huggingface.co/QCRI/Fanar-2-Diwan).


Building on the success of [Fanar 1.0](https://arxiv.org/abs/2501.13944), we continually pretrain the `google/gemma-3-27b-pt` model on ~166B Arabic and English tokens using a novel three-recipe training approach with model merging. Highlighting the richness of the Arabic language, we support Modern Standard Arabic (MSA) and a diverse set of Arabic dialects, including Gulf, Levantine, and Egyptian. Fanar models, through meticulous curation of the pretraining and post-training data, are aligned with Islamic values and Arabic culture.

**Fanar-2-27B-Instruct** introduces several breakthrough capabilities including native Arabic reasoning traces, selective thinking mode, tool calling, and advanced hallucination mitigation—making it the most capable Arabic-English language model in the Fanar family.

We have published a [report](https://arxiv.org/abs/2603.16397) with all the details regarding Fanar 2.0 GenAI platform. We also provide a [chat interface](https://chat.fanar.qa), mobile apps for [iOS](https://apps.apple.com/jo/app/fanar-فنار/id6741857943) and [Android](https://play.google.com/store/apps/details?id=com.fanarmobile), and [API access](https://api.fanar.qa/docs) to our models and the GenAI platform (request access [here](https://api.fanar.qa/request/en)).

---

## Model Details

| Attribute                  | Value                              |
|---------------------------|------------------------------------|
| Developed by              | [QCRI](https://www.hbku.edu.qa/en/qcri) at [HBKU](https://www.hbku.edu.qa/)                      |
| Sponsored by              | [Ministry of Communications and Information Technology, State of Qatar](https://www.mcit.gov.qa/en/)
| Model Type                | Autoregressive Transformer         |
| Parameter Count           | 27 Billion                          |
| Context Length            | 32,768 Tokens                        |
| Input                     | Text only                          |
| Output                    | Text only                          |
| Base Model                | Gemma-3-27B-pt                     |
| Training Frameworks        | NVIDIA NeMo + LlamaFactory                        |
| Continual Pretraining     | ~166B tokens (Arabic, English, Code) |
| SFT Instructions          | 4M                               |
| DPO Preference Pairs      | 280K                              |
| Languages                 | Arabic, English                    |
| License                   | Apache 2.0                         |

---

## What's New from Fanar 1.0

Fanar-2-27B-Instruct represents a major evolution from Fanar-1-9B-Instruct with improvements across model capacity, capabilities, and performance.

| Aspect | Fanar 1.0 (9B) | Fanar 2.0 (27B) | Improvement |
|--------|----------------|-----------------|-------------|
| **Model Size** | 9 Billion parameters | 27 Billion parameters | 3× larger |
| **Context Length** | 4,096 tokens | 32,768 tokens | 8× longer |
| **Pretraining Tokens** | 1 Trillion (continual) | 166 Billion (continual) | Quality over quantity |
| **Thinking Mode with Native Arabic Reasoning** | ❌ Not available | ✅ Available with `<think>` tags | New capability |
| **Tool Calling** | ❌ Not available | ✅ Generic & 10 Fanar tools | New capability |
| **Hallucination Mitigation** | Basic | Knowledge probing and verification traces | Enhanced |

### Performance Improvements

| Benchmark | Fanar 1.0 (9B) | Fanar 2.0 (27B) | Delta |
|-----------|----------------|-----------------|-------|
| ArabicMMLU | 67.35% | 74.67% | +7.32% |
| Belebele (Dialectal Arabic) | 83.26% | 86.81% | +3.55% |
| ACVA (Cultural) | 79.66% | 82.70% | +3.04% |
| MMLU (English) | 71.32% | 78.89% | +7.57% |
| GSM8K (Math) | 83.02% | 93.70% | +10.68% |
| MT-Bench | 5.58 | 6.12 | +5.4% |
| IF-Eval | 74.70 | 82.97 | +8.27% |
| Safety | 67.55 | 72.62 | +5.07% |
| Cultural Alignment | 3.86 | 4.32 | +4.6% |

---

## Model Training

### Continual Pretraining

Fanar-2-27B-Instruct was continually pretrained on the Gemma-3-27B-pt base model using a novel **three-recipe approach** with model merging, consuming approximately **166B tokens** over 75,000 GPU hours on NVIDIA H100 GPUs.

**Three-Recipe Training Strategy:**

1. **Recipe 1 (50B tokens)**: Curated high-quality data
   - 45% Arabic (curated HQ sources from Fanar 1.0)
   - 45% English (Dolma subset)
   - 10% Code (The Stack v2)
   - **Focus**: Linguistic correctness and domain breadth

2. **Recipe 2 (70B tokens)**: Curated + Educational web data
   - 45% Arabic (curated + ArabicWeb-EDU)
   - 45% English (curated + FineWeb-EDU)
   - 10% Code
   - **Focus**: Formal Arabic registers and domain-specific terminology

3. **Recipe 3 (30B tokens)**: Translation-centric parallel data
   - 50% Arabic (curated + Arabic translations)
   - 50% English (FineWeb-EDU subset)
   - **Focus**: Cross-lingual alignment and Arabic lexical coverage

**Training Configuration:**

- Learning rate: 1e-6 (warmup 100 steps, cosine decay to 5e-7)
- Annealing phase: 8B tokens after each recipe (learning rate linearly decays to zero)
- Final model: Linear merge of checkpoints
  - 60% Recipe 1 (with annealing)
  - 20% Recipe 2 (with annealing)
  - 20% Recipe 3 (without annealing)

### Post-training

Fanar-2-27B-Instruct underwent a comprehensive five-stage post-training pipeline:

#### 1. Supervised Fine-tuning (SFT) - 4M Instructions
- Short-form instruction-response pairs
- **Long chain-of-thought reasoning traces** (including native Arabic reasoning traces)
- Multi-turn dialogue
- Culturally aligned samples
- Data: Filtered public datasets + synthetic generation with language consistency filtering

#### 2. Long-Context Adaptation - 54K Instructions
- Extended training for 16K context window
- Long-form instruction-response pairs
- Multi-turn dialogue coherence

#### 3. Capability Rebalancing - 1.8M Instructions
- High-quality curated subset to restore balance after long-context adaptation
- Prevents degradation of short-form task performance

#### 4. Direct Preference Optimization (DPO) - 280K Preference Pairs
- Public preference corpora + synthetic pairs
- User-dislike data from production logs
- Cultural alignment preference pairs

#### 5. Checkpoint Merging
- Linear merge: 40% primary DPO + 40% SFT-Reasoning + 20% DPO-mix
- Combines complementary strengths across training stages

---

## Key Capabilities

### Thinking Mode with Native Arabic Reasoning
The model supports optional reasoning trace generation using `<think>...</think>` blocks. Unlike models that use translated English reasoning traces, Fanar-2-27B-Instruct was trained on ~250K Arabic reasoning examples, and as a result generates multi-step reasoning natively in Arabic.

### Tool Calling
Supports generic tool use in addition to 10 internal Fanar tools for enhanced functionality including web search, calculator, and domain-specific utilities.

### Knowledge Probing & Hallucination Mitigation
Trained to explicitly say "I don't know" when uncertain, reducing hallucinations through knowledge probing during training, 5-step structured verification traces, and calibrated abstention responses.

### Quranic Verse Encapsulation
Spontaneous Quranic verse references are wrapped in validation markers, enabling downstream verification of verse correctness.

---

## Getting Started

Fanar-2-27B-Instruct is compatible with the Hugging Face `transformers` library (tested with v4.57.6). Here's how to load and use the model:

### Using Transformers

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

model_name = "QCRI/Fanar-2-27B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")

# Message content may be in Arabic or English
messages = [
    {"role": "user", "content": "ما هي عاصمة قطر؟"},
]

inputs = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
outputs = model.generate(**tokenizer(inputs, return_tensors="pt", return_token_type_ids=False).to(model.device), max_new_tokens=256)

print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

### Using vLLM (Recommended for Production)

Fanar-2-27B-Instruct is also compatible with `vllm` for efficient inference (tested with v0.18.0)

```python
from vllm import LLM, SamplingParams

model_name = "QCRI/Fanar-2-27B-Instruct"

llm = LLM(model=model_name, gpu_memory_utilization=0.95)
sampling_params = SamplingParams(temperature=0.7, max_tokens=256)

# Message content may be in Arabic or English
messages = [
    {"role": "user", "content": "ما هي عاصمة قطر؟"},
]

outputs = llm.chat(messages, sampling_params)
print(outputs[0].outputs[0].text)
```

### Controlling Thinking Mode

```python
# With thinking (default) - shows reasoning process
response = llm.chat(messages, sampling_params, chat_template_kwargs={"no_thinking": False})
# Output: <think>reasoning steps...</think>\nFinal answer

# Without thinking - cleaner output for production
response = llm.chat(messages, sampling_params, chat_template_kwargs={"no_thinking": True})
# Output: Final answer only
```


---

## Evaluation

Evaluation was conducted using customized versions of LM Evaluation Harness and Lighteval. Fanar-2-27B-Instruct demonstrates **best-in-class performance among similarly sized models** on Arabic benchmarks while maintaining competitive English capabilities. The summary below compares Fanar on a number of benchmarks, more results and comparisons to Arabic-centric and multilingual models of various sizes can be found in the technical report (Sec 3.4 Evaluation).

### Performance Summary

| Model | MMMLU (Arabic) | ArabicMMLU | OALL-v2 | Almieyar | Belebele | ACVA | MMLU (English) | GSM8K | Arabic Cultural (/10) | Safety |
|-------|----------------|------------|---------|--------------|----------|------|----------------|-------|-----------------|----------------|
| **Fanar-27B** | 67.40 | **74.67** | 69.40 | **79.46** | **86.81** | **82.70** | 78.89 | 93.70 | **4.32** | **72.62** |
| Gemma-3-27B-it | 67.65 | 72.21 | **70.95** | 70.48 | 85.54 | 80.23 | 77.38 | **95.80** | 3.34 | 70.53 |
| AceGPT-v2-32B-Chat | 61.10 | 69.55 | 67.42  | 55.24 | 83.96 | 79.69 | 75.72 | 71.50 | 3.25 | 71.94 |
| Qwen3-32B | **69.32** | 73.08 | 64.85 | 67.18 | 85.98 | 79.72 | **82.25** | **95.80** | 3.49 | 71.25 |

**Benchmark Details:**

- **MMMLU (Arabic)**: 0-shot Arabic world knowledge across diverse domains
- **ArabicMMLU**: 3-shot Arabic knowledge and capability evaluation
- **OALL-v2**: 0-shot Arabic language understanding suite
- **Almieyar**: 0-shot average score across phonology, morphology, syntax, semantics, and pragmatics subcategories
- **Belebele**: 3-shot dialectal Arabic reading comprehension
- **ACVA**: 5-shot Arabic cultural values and alignment evaluation
- **MMLU (English)**: 5-shot English knowledge
- **GSM8K**: 0-shot mathematical reasoning
- **Arabic Cultural**: Cultural alignment score (out of 10, higher is better)
- **Safety**: Overall safety evaluation score averaged across 9 detailed subcategories.

---

## Intended Use, Ethical Considerations & Limitations

Fanar-2-27B-Instruct is capable of generating fluent and contextually appropriate responses. However, as with any generative model, there are uncertainties. The model may produce **biased, offensive, or incorrect outputs**. The standalone model is **not suitable for high-stakes decision-making** (e.g., legal, medical, or financial advice). It can be deployed as part of a broader AI system. Developers are encouraged to implement proper safeguards to ensure culturally respectful, accurate, and safe deployment. It should not be used to generate or spread **harmful, illegal, or misleading content.** 

Though we have extensively tested Fanar-2-27B-Instruct and implemented multiple mitigation strategies (e.g., knowledge probing, verification traces, and cultural alignment training), we cannot address every possible scenario. Thus, we advise developers to:

- Implement further safety checks and content filtering
- Perform domain-specific fine-tuning for sensitive use cases
- Monitor outputs in production environments
- Provide clear disclaimers to end users

Kindly refer to our [Terms of Service](https://chat.fanar.qa/terms-of-service) and [Privacy Policy](https://chat.fanar.qa/privacy-policy).

The output generated by this model is not considered a statement of QCRI, HBKU, Qatar Foundation, MCIT, or any other organization or individual.

---

## Fanar Platform

While Fanar-2-27B-Instruct is a powerful standalone model, it is part of the broader **Fanar Platform**—an integrated Arabic-centric multimodal AI ecosystem that provides enhanced capabilities and continuous updates. The platform includes:

**Core Capabilities:**

- **Text Generation**: Multiple conversational models optimized for different tasks
- **Speech (Aura)**: Speech-to-text (short-form and long-form) and text-to-speech synthesis with Arabic dialect support and bilingual Arabic-English capabilities
- **Image Understanding (Oryx-IVU)**: Vision-language model for culturally-grounded image and video understanding including Arabic calligraphy recognition
- **Image Generation (Oryx-IG)**: Culturally-aligned text-to-image generation trained on taxonomy-driven data across 23,000+ cultural search terms
- **Machine Translation (FanarShaheen)**: High-quality bilingual Arabic↔English translation across diverse domains (e.g., news, STEM, and medical)
- **Poetry Generation (Diwan)**: Classical Arabic poetry generation respecting prosodic meters (Buhur) and maintaining diacritization accuracy

**Specialized Systems:**

- **Fanar-Sadiq**: Multi-agent Islamic question-answering system with 9 specialized tools (Fiqh reasoning, Quran/Hadith retrieval, zakat/inheritance calculation, prayer times, and Hijri calendar). Deployed in production on [IslamWeb](https://islamweb.net) and [IslamOnline](https://islamonline.net) platforms.
- **Safety & Moderation**: Fanar-Guard and culturally-informed content filtering trained on 468K annotated Arabic-English safety examples

**Access Points:**

- **[Fanar Chat](https://chat.fanar.qa)**: Web conversational interface integrating all modalities
- **[iOS](https://apps.apple.com/jo/app/fanar-فنار/id6741857943) and [Android](https://play.google.com/store/apps/details?id=com.fanarmobile) apps**: Mobile apps for on-the-go access to the Fanar Platform
- **[Fanar API](https://api.fanar.qa)**: Programmatic access to models and specialized capabilities

The Fanar Platform continuously evolves with model updates, new capabilities, and improved safety mechanisms. For production deployments requiring the latest features, multimodal integration, cross-model orchestration, and ongoing support, we recommend using the [Fanar Platform](https://fanar.qa) rather than the standalone models published here.

---

## Citation

If you use Fanar-2-27B-Instruct or the Fanar 2.0 GenAI platform in your research or applications, please cite:

```bibtex
@misc{fanarteam2026fanar20arabicgenerative,
      title={Fanar 2.0: Arabic Generative AI Stack}, 
      author={FANAR TEAM and Ummar Abbas and Mohammad Shahmeer Ahmad and Minhaj Ahmad and Abdulaziz Al-Homaid and Anas Al-Nuaimi and Enes Altinisik and Ehsaneddin Asgari and Sanjay Chawla and Shammur Chowdhury and Fahim Dalvi and Kareem Darwish and Nadir Durrani and Mohamed Elfeky and Ahmed Elmagarmid and Mohamed Eltabakh and Asim Ersoy and Masoomali Fatehkia and Mohammed Qusay Hashim and Majd Hawasly and Mohamed Hefeeda and Mus'ab Husaini and Keivin Isufaj and Soon-Gyo Jung and Houssam Lachemat and Ji Kim Lucas and Abubakr Mohamed and Tasnim Mohiuddin and Basel Mousi and Hamdy Mubarak and Ahmad Musleh and Mourad Ouzzani and Amin Sadeghi and Husrev Taha Sencar and Mohammed Shinoy and Omar Sinan and Yifan Zhang},
      year={2026},
      eprint={2603.16397},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2603.16397}, 
}
```

---

## Acknowledgements

This project is from [Qatar Computing Research Institute (QCRI)](https://www.hbku.edu.qa/en/qcri) at [Hamad Bin Khalifa University (HBKU)](https://hbku.edu.qa), a member of Qatar Foundation. We thank our engineers, researchers, and support team for their efforts in advancing Arabic-centric large language models.

Special thanks to the [Ministry of Communications and Information Technology, State of Qatar](https://www.mcit.gov.qa/en/) for their continued support by providing the compute infrastructure needed to develop and serve the platform through the Google Cloud Platform.

---

## License

This model is licensed under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0).
