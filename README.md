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
   - Deploy a PostgreSQL database to store feed data.
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

## 📐 System Design

![System Design Diagram](https://github.com/user-attachments/assets/3da390f1-7a18-4dd8-ae98-02ba1c9aee71)

---

## 📏 Code Guidelines

- **Separate Codebases**: Clearly distinguish research code from production code.
- **Lint Before Committing**: Run linters using:
  ```bash
  make lint
