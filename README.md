<div id="top"></div>

<div align="center">

<picture>
  <source srcset="assets/logo.svg" media="(prefers-color-scheme: light)">
  <source srcset="assets/logo-darkmode.svg" media="(prefers-color-scheme: dark)">
  <img src="assets/logo.svg" alt="Logo" width="50%">
</picture>

[📃 Paper](https://arxiv.org/abs/2407.20183) | [💻 Demo](https://internlm-chat.intern-ai.org.cn/)

<https://github.com/user-attachments/assets/44ffe4b9-be26-4b93-a77b-02fed16e33fe>

</div>
</p>

## ✨ MindSearch: Mimicking Human Minds Elicits Deep AI Searcher

MindSearch is a powerful AI search engine that mimics human thinking patterns to perform comprehensive web searches. This streamlined version focuses on the core backend functionality, providing:

- **FastAPI Backend**: RESTful API for integration into your applications
- **Terminal Interface**: Direct command-line interaction for development and testing
- **Backend Example**: Sample code showing how to interact with the API
- **Multi-Model Support**: Works with GPT-4, InternLM, Qwen, and other LLMs
- **Multiple Search Engines**: DuckDuckGo, Bing, Google, Brave, and Tencent Search
- **Intelligent Query Processing**: Breaks down complex questions and searches in parallel

## 📅 Changelog

- 2024/11/05: 🥳 MindSearch is now deployed on Puyu! 👉 [Try it](https://internlm-chat.intern-ai.org.cn/) 👈
  -  Refactored the agent module based on [Lagent v0.5](https://github.com/InternLM/lagent) for better performance in concurrency.
  -  Improved the UI to embody the simultaneous multi-query search.


## ⚽️ Build Your Own MindSearch

### Step1: Dependencies Installation

```bash
git clone https://github.com/InternLM/MindSearch
cd MindSearch
pip install -r requirements.txt
```

### Step2: Setup Environment Variables

Before setting up the API, you need to configure environment variables. Create a `.env` file and add your API keys:

```bash
# For OpenAI GPT models
OPENAI_API_KEY=your_openai_api_key
OPENAI_API_BASE=https://api.openai.com/v1/chat/completions

# For web search (not needed for DuckDuckGo)
WEB_SEARCH_API_KEY=your_search_api_key

# For Tencent Search (if using TencentSearch)
TENCENT_SEARCH_SECRET_ID=your_secret_id
TENCENT_SEARCH_SECRET_KEY=your_secret_key
```

### Step3: Start MindSearch API Server

```bash
python -m mindsearch.app --lang en --model_format internlm_server --search_engine DuckDuckGoSearch --asy
```

**Parameters:**
- `--lang`: Language (`en` for English, `cn` for Chinese)
- `--model_format`: Model format
  - `internlm_server` for InternLM2.5-7b-chat with local server
  - `gpt4` for GPT-4
  - `qwen` for Qwen models
  - `internlm_silicon` for InternLM via SiliconFlow API
  - See [models.py](./mindsearch/agent/models.py) for all supported models
- `--search_engine`: Search engine
  - `DuckDuckGoSearch` (no API key required)
  - `BingSearch`
  - `BraveSearch`
  - `GoogleSearch` (via Serper API)
  - `TencentSearch`
- `--asy`: Enable asynchronous agents for better performance



## 🔧 Using MindSearch

### Option 1: API Server + Backend Example

1. **Start the API server:**
```bash
python -m mindsearch.app --lang en --model_format gpt4 --search_engine DuckDuckGoSearch
```

2. **Use the backend example script:**
```bash
python backend_example.py
```

The backend example demonstrates how to:
- Send queries to the MindSearch API
- Process streaming responses
- Handle the structured output with search results and references

### Option 2: Terminal Interface (Direct Usage)

For direct interaction without the API server:

```bash
python -m mindsearch.terminal
```

This runs MindSearch directly in your terminal, perfect for:
- Quick testing and debugging
- Development and experimentation
- Understanding the search process step-by-step

## 📝 License

This project is released under the [Apache 2.0 license](LICENSE).

## Citation

If you find this project useful in your research, please consider cite:

```
@article{chen2024mindsearch,
  title={MindSearch: Mimicking Human Minds Elicits Deep AI Searcher},
  author={Chen, Zehui and Liu, Kuikun and Wang, Qiuchen and Liu, Jiangning and Zhang, Wenwei and Chen, Kai and Zhao, Feng},
  journal={arXiv preprint arXiv:2407.20183},
  year={2024}
}
```

## Our Projects

Explore our additional research on large language models, focusing on LLM agents.

- [Lagent](https://github.com/InternLM/lagent): A lightweight framework for building LLM-based agents
- [AgentFLAN](https://github.com/InternLM/Agent-FLAN): An innovative approach for constructing and training with high-quality agent datasets (ACL 2024 Findings)
- [T-Eval](https://github.com/open-compass/T-Eval): A Fine-grained tool utilization evaluation benchmark (ACL 2024)
