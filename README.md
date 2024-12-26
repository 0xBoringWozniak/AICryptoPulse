# AICryptoPulse

**AICryptoPulse** is an advanced Retrieval-Augmented Generation (RAG) system designed to curate and analyze daily crypto news. It powers the Telegram bot **[@agent_cryptopulse_bot](https://t.me/agent_cryptopulse_bot)**, providing insightful updates directly to your chat.

---

## 🚀 Project Structure

- **`/bot`**: Telegram Bot User Interface (UI).
- **`/data`**: Airflow infrastructure for collecting and processing news feeds.
- **`/notebooks`**: Jupyter notebooks for research and experiments.
- **`/service`**: Core logic implementing the RAG pipeline and API application.

---

## 🛠 How to Run?

1. **Set up the Airflow module** (located in `/data`):
   - Refer to the [official Airflow documentation](https://airflow.apache.org/docs/apache-airflow/stable/start.html) for installation.
   - Run a PostgreSQL database to store feed data.
   - Set up S3-like bucket to store FAISS indexes.
   - Configure settings in `/data/configs/`.
   - Enable all DAGs in the Airflow interface.

2. **Configure environment variables**:
   - Use `.env.example` as a template to create your `.env` file.

3. **Run the Service**:
   - Use Docker Compose to deploy the system:
     ```bash
     docker-compose up -d
     ```
   - Alternatively, use the Makefile:
     ```bash
     make all
     ```

---

## 🌐 Data Pipeline
- Data is collecting from the open APIs (feeds, Twitter APIs, Telegram API)
- ETLs are running on Airflow and store all data in PostgreSQL
- FAISS index (both short-term and long-term) are updated each day on Airflow

Done:
 - [x] Coindesk
 - [x] DLNews
 - [x] Twitter big crypto accounts
 - [x] [DeFillamaFeed](https://feed.defillama.com/)

In progress:
- [ ] [Tree Feed](https://news.treeofalpha.com/)
- [ ] Custom Twitter accounts

To Do:
- [ ] Bloomberg
- [ ] Cointelegraph
- [ ] Classic Financial news portals

---

## Benchmarks and metrics
- CryptoQA (HemaChandrao/crypto_QA) - synthetic QnA dataset with GPT answers (215 rows);
- Filtered crypto-2024 (sites.google.com/view/cryptoqa-2024/datasets) – dataset with answers to crypto questions from reddit and twitter from the Indian Institute of Technology (239 rows). Filtering was performed by filtering relevant items using the Qwen2.5-14b model.

### `HemaChandrao/crypto_QA`

** MTEB models **

| model_id                                          |      mAP |      MRR |
|:--------------------------------------------------|---------:|---------:|
| HIT-TMG/KaLM-embedding-multilingual-mini-instr... | 0.818385 | 0.817797 |
| jinaai/jina-embeddings-v3                         | 0.807477 | 0.805951 |
| Alibaba-NLP/gte-large-en-v1.5                     | 0.779034 | 0.777258 |
| WherelsAl/UAE-Large-V1                            | 0.7547   | 0.752776 |
| jxm/cde-small-v1                                  | 0.240464 | 0.224688 |

** Base models **
| model_id                              |      mAP |      MRR |
|:--------------------------------------|---------:|---------:|
| all-mpnet-base-v2                     | 0.798267 | 0.796895 |
| multi-qa-mpnet-base-dot-v1            | 0.778915 | 0.777039 |
| all-distilroberta-v1                  | 0.733526 | 0.730228 |
| all-MiniLM-L12-v2                     | 0.725623 | 0.722476 |
| multi-qa-MiniLM-L6-cos-v1             | 0.716872 | 0.714196 |
| multi-qa-distilbert-cos-v1            | 0.713394 | 0.710679 |
| all-MiniLM-L6-v2                      | 0.712731 | 0.709069 |
| paraphrase-multilingual-mpnet-base-v2 | 0.610216 | 0.601813 |
| paraphrase-albert-small-v2            | 0.607011 | 0.601449 |
| paraphrase-multilingual-MiniLM-L12-v2 | 0.594264 | 0.585709 |
| distiluse-base-multilingual-cased-v2  | 0.582778 | 0.575996 |
| distiluse-base-multilingual-cased-v1  | 0.571691 | 0.563731 |
| paraphrase-MiniLM-L3-v2               | 0.551712 | 0.543413 |

### `Filtered Cryptoqa-2024`

** MTEB models **

| model_id                                          |      mAP |      MRR |
|:--------------------------------------------------|---------:|---------:|
| Alibaba-NLP/gte-large-en-v1.5                     | 0.631214 | 0.623856 |
| HIT-TMG/KaLM-embedding-multilingual-mini-instr... | 0.608928 | 0.602966 |
| jinaai/jina-embeddings-v3                         | 0.608519 | 0.601709 |
| WherelsAl/UAE-Large-V1                            | 0.554994 | 0.547885 |
| jxm/cde-small-v1                                  | 0.155341 | 0.136702 |

** Base models **

| model_id                              |      mAP |      MRR |
|:--------------------------------------|---------:|---------:|
| all-mpnet-base-v2                     | 0.575693 | 0.566497 |
| all-distilroberta-v1                  | 0.523694 | 0.512484 |
| multi-qa-mpnet-base-dot-v1            | 0.515863 | 0.505068 |
| all-MiniLM-L12-v2                     | 0.509307 | 0.499188 |
| all-MiniLM-L6-v2                      | 0.469071 | 0.458595 |
| multi-qa-distilbert-cos-v1            | 0.466012 | 0.453911 |
| multi-qa-MiniLM-L6-cos-v1             | 0.434840 | 0.420884 |
| distiluse-base-multilingual-cased-v1  | 0.305668 | 0.291416 |
| paraphrase-multilingual-mpnet-base-v2 | 0.303580 | 0.287447 |
| distiluse-base-multilingual-cased-v2  | 0.300423 | 0.283640 |
| paraphrase-multilingual-MiniLM-L12-v2 | 0.274722 | 0.258638 |

---

## RAG

Retriever - all-MiniLM-L6-v2.
Decoder - gpt-3.5-turbo.

Also our solution contains caching of model responses, for more reasonable spending of financial resources, chat history for the user.

---

## 📐 System Design

![System Design Diagram](https://github.com/user-attachments/assets/3da390f1-7a18-4dd8-ae98-02ba1c9aee71)

---

## 📏 Code Guidelines

- **Separate Codebases**: Clearly distinguish research code from production code.
- **Lint Before Committing**: Run linters using:
  ```bash
  make lint
