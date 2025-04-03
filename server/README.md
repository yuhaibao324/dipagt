# Multi-Agent System Server

This is the server component of a multi-agent system built with Python, using PostgreSQL as the database and Peewee as the ORM.

## Project Structure

```
server/
├── app/
│   ├── chat/           # Chat-related functionality
│   ├── db/             # Database models and configuration
│   │   ├── database.py # Database connection setup
│   │   └── models.py   # Database models
│   ├── intention/      # Intention processing
│   ├── llm/            # Large Language Model integration
│   ├── memory/         # Conversational memory management (using mem0)
│   │   └── mem0_memory.py # Wrapper for mem0 client
│   ├── plan/           # Planning and task management
│   ├── tools/          # Agent tools and capabilities
│   ├── utils/          # Utility functions
│   ├── config.py       # Configuration management
│   └── health_check.py # Health check endpoint
├── data/
│   ├── agents.json          # Predefined agents, will be imported to database
│   ├── tools.json           # Predefined tools, will be imported to database
│   ├── agent_tools.json     # Agents and tools relationship
│   └── import_data.py       # Database import script
```

## Core Components

The system utilizes a PostgreSQL database managed via the Peewee ORM to store agents, tools, conversations, and tasks. Key components include:

### Database Models (`app/db/models.py`)

- `Agent`: Represents an AI agent with properties like name, description, type (e.g., Copilot, Product Manager, Designer, Engineer), and configuration.
- `Tool`: Defines available tools with name, description, and parameters.
- `AgentTool`: Manages the many-to-many relationship between agents and tools, allowing flexible assignment of toolsets to different agents.
- `Chat`: Represents a conversation session.
- `Message`: Stores individual messages within a chat.
- `Task`: Represents tasks assignable to agents, supporting execution via a Directed Acyclic Graph (DAG).

### Memory Management (`app/memory/`)

- The system uses `mem0` to manage conversational memory.
- `Mem0Memory` (`app/memory/mem0_memory.py`) provides an abstraction layer over `mem0`.
- In chat processing, relevant history is retrieved from `mem0` instead of the full database history to provide better context to the LLM and planner.
- User and assistant messages are added to `mem0` during the conversation.

### run qdrant

`docker pull qdrant/qdrant`

```powershell
docker run -p 6333:6333 -p 6334:6334 `
-v ${PWD}/qdrant_storage:/qdrant/storage:z `
qdrant/qdrant
```

### Tools (`app/tools/`)

The system provides a variety of tools agents can leverage:

- `browser_use.py`: Web browsing capabilities.
- `command_line_tool.py`: Command line execution.
- `code_writer.py`: Code generation and editing.
- `design_generator.py`: Design generation.
- `tavily_search.py`: Web search functionality.
- `web_content_fetcher.py`: Web content retrieval.
- `mcp_tool.py`: Multi-agent coordination.
- `answer.py`: Answer generation.

**Tool Management:**

- A `ToolManager` (`app/tools/tool_manager.py`) is provided to manage agent-accessible tools. It handles:
  - Fetching the list of tools available to a specific agent.
  - Retrieving tool instances.
  - Configuring tools based on parameters.
  - Executing tools on behalf of an agent.
- All tools inherit from a `BaseTool` base class. Each tool implements an asynchronous `_run` method and a `get_schema` method.

## Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure environment variables (copy `.env.example` to `.env` and fill in the details).
4.  Install PostgreSQL and create a database.
5.  **(Optional)** Configure `mem0`: By default, `mem0` uses in-memory storage. If you plan to use cloud features or persistent storage with `mem0`, refer to the `mem0` documentation for configuration (e.g., setting API keys via environment variables like `MEM0_API_KEY`).

## Database Configuration

Configure the PostgreSQL connection details in your `.env` file:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=dipagt
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
```

## Predefined Agents (`data/agents.json`)

The system comes with several predefined agent types:

- **Copilot**: Responsible for managing and dispatching tasks to other agents.
- **Bob**: A highly skilled Product Manager, proficient in product design and analysis.
- **Alice**: A Designer capable of creating clean and effective designs.
- **Pliman**: A technology-focused Engineer adept at handling various technical challenges.

## Agent-Tool Association (`data/agent_tools.json`)

Each agent can be associated with multiple tools. These associations are defined in the `agent_tools.json` file and include:

- **Configuration**: Agent-specific tool configurations, allowing customization of tool behavior per agent.

For example, the Alice agent might use the `DesignGenerator` tool and the `TavilySearch` tool, while the Pliman agent might use the `CodeWriter` tool and the `CommandLineTool` tool.

## Usage

### Initialize Database

```bash
python -c "from app.db.models import init_db; init_db()"
```

### Import Predefined Agents and Tools

```bash
python data/import_data.py
```

_(Note: Add specific test script if available)_

### Run Database Tests (Example)

```bash
pytest app/db/test_database.py
```

_(Note: Update path/command based on actual test setup)_

## Extensibility

### Adding New Agents

1.  Add the new agent definition to `data/agents.json`.
2.  Run `python data/import_data.py` to import.

### Adding New Tools

1.  Create the new tool class in the `app/tools/` directory, inheriting from `BaseTool`.
2.  Import the new tool in `app/tools/__init__.py`.
3.  Add the new tool definition to `data/tools.json`.
4.  Run `python data/import_data.py` to import.

### Adding New Agent-Tool Associations

1.  Add the new association(s) to `data/agent_tools.json`.
2.  Run `python data/import_data.py` to import.
