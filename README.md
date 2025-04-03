# Multi-Agent System

A Python-based multi-agent system that enables collaboration between different AI agents to accomplish complex tasks. The system uses PostgreSQL for data storage and Peewee as the ORM.

## Project Structure

```
.
├── server/           # Server component (Python/FastAPI)
│   ├── app/         # Main application code
│   ├── Dockerfile
│   ├── .dockerignore
│   └── README.md
├── ui/               # Client interface (Next.js)
│   ├── src/
│   ├── Dockerfile
│   ├── .dockerignore
│   └── README.md
├── docker-compose.yaml # Docker orchestration
├── .env.example        # Example environment variables for Docker
└── README.md           # This file
```

## Features

- **Multi-Agent Collaboration**: Different AI agents can work together to solve complex problems
- **Extensible Tool System**: Agents can use various tools like web search, code generation, and more
- **Flexible Database**: PostgreSQL with Peewee ORM for robust data storage
- **Multiple LLM Support**: Integration with OpenAI and Anthropic models (Update as applicable)
- **Task Management**: Support for complex task hierarchies and workflows
- **Conversational Memory**: Utilizes Qdrant and potentially mem0 for context management.
- **Web UI**: Next.js frontend for user interaction.
- **Containerized Deployment**: Docker and Docker Compose setup for easy deployment.

## Prerequisites (for Manual Setup)

- Python 3.11+
- Node.js 20+ & npm
- PostgreSQL 12+
- Qdrant (Can be run via Docker, see server README)
- OpenAI API key (if using OpenAI models)
- Anthropic API key (if using Anthropic models)
- Tavily API key (if using Tavily search tool)

## Manual Installation & Usage

Refer to the `README.md` files within the `server/` and `ui/` directories for detailed instructions on setting up and running each component manually.

## Deployment (Docker)

This is the recommended way to run the entire application stack (Backend, Frontend, Database, Vector Store, DB Admin).

**Prerequisites:**

- Docker ([Install Docker](https://docs.docker.com/get-docker/))
- Docker Compose ([Included with Docker Desktop](https://docs.docker.com/compose/install/))

**Steps:**

1.  **Clone the Repository:**

    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2.  **Configure Environment Variables:**

    - Copy the example environment file:
      ```bash
      cp .env.example .env
      ```
    - Edit the `.env` file in the project root directory.
    - **Crucially, fill in:**
      - `POSTGRES_PASSWORD` (Use a strong password!)
      - `PGADMIN_DEFAULT_PASSWORD` (Use a strong password!)
      - `MEM0_API_KEY` (If required)
      - `OPENAI_API_KEY`
      - `TAVILY_API_KEY`
      - Any other required API keys or secrets for the server.
    - You can also adjust the `*_PORT_HOST` variables if the default ports (5432, 5050, 6334, 6333, 8000, 3000) conflict with other services on your machine.

3.  **Build and Start Services:**

    - From the project root directory (where `docker-compose.yaml` is located), run:
      ```bash
      docker compose up --build -d
      ```
      - `--build`: Builds the images for the `server` and `ui` services based on their Dockerfiles. You only need to include this the first time or when you change the Dockerfile or source code.
      - `-d`: Runs the containers in detached mode (in the background).
    - The server will automatically initialize the database schema and import the necessary initial data (agents, tools) on its first startup. Check the server logs (`docker compose logs -f server`) to monitor this process.

4.  **Access Services:** (Renumbered from 5)

    - **Web UI:** Open your browser to `http://localhost:3000` (or the `UI_PORT_HOST` you set in `.env`).
    - **PgAdmin (Database Admin):** `http://localhost:5050` (or `PGADMIN_PORT_HOST`). Log in with the email/password set in your `.env` (`PGADMIN_DEFAULT_EMAIL`, `PGADMIN_DEFAULT_PASSWORD`). You'll need to manually add a connection to the database server within PgAdmin:
      - Host Name/Address: `postgres` (this is the service name defined in `docker-compose.yaml`)
      - Port: `5432`
      - Maintenance database: `postgres` (or the value of `POSTGRES_DB`)
      - Username: The value of `POSTGRES_USER` from `.env`
      - Password: The value of `POSTGRES_PASSWORD` from `.env`
    - **Server API (Direct Access):** `http://localhost:8000` (or `SERVER_PORT_HOST`)
    - **Qdrant UI (Direct Access):** `http://localhost:6334` (or `QDRANT_HTTP_PORT_HOST`)

5.  **View Logs:** (Renumbered from 6)

    ```bash
    # View logs for all services
    docker compose logs -f

    # View logs for a specific service (e.g., server)
    docker compose logs -f server
    ```

6.  **Stop Services:** (Renumbered from 7)

    ```bash
    # Stop and remove containers, networks
    docker compose down

    # Stop and remove containers, networks, AND volumes (DELETES ALL DATA)
    docker compose down -v
    ```

## TODO

[] /chat refresh cannot find the page
[] Test all tools
[] Use complex use cases for testing, such as generating HTML reports
[x] There are still some issues with running server environment variables in docker-compose. You can use docker-compose as a database and vector database. Manually pip install -r requirements for the backend, then run fastapi; manually npm install for the frontend, then npm run dev - fixed recommend using docker-compose for quick start up

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License
