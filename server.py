import json
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI
from mcp.server.fastmcp import FastMCP
from sqlalchemy import MetaData, Table, create_engine, inspect, select
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from .env")

# pool_pre_ping helps detect stale database connections.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=2,
    max_overflow=0,
)

mcp = FastMCP("ChatGPT + PostgreSQL MCP Server")


@mcp.tool()
def ask_chatgpt(prompt: str) -> str:
    """Ask ChatGPT a question."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content


@mcp.tool()
def summarize(text: str) -> str:
    """Summarize text."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": f"Summarize the following:\n\n{text}"}],
    )

    return response.choices[0].message.content


@mcp.tool()
def explain_python(code: str) -> str:
    """Explain Python code."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": f"Explain this Python code:\n\n{code}"}],
    )

    return response.choices[0].message.content


def json_result(data) -> str:
    """Convert results into JSON text."""
    return json.dumps(data, indent=2, default=str)


def get_table(table_name: str, schema: str = "public") -> Table:
    """Reflect a table after validating that it exists."""
    inspector = inspect(engine)

    if schema not in inspector.get_schema_names():
        raise ValueError(f"Schema not found: {schema}")

    if table_name not in inspector.get_table_names(schema=schema):
        raise ValueError(f"Table not found: {schema}.{table_name}")

    return Table(
        table_name,
        MetaData(),
        schema=schema,
        autoload_with=engine,
    )


@mcp.tool()
def list_tables(schema: str = "public") -> str:
    """List tables available in a PostgreSQL schema."""
    try:
        inspector = inspect(engine)

        if schema not in inspector.get_schema_names():
            return json_result({"error": "Schema not found"})

        tables = inspector.get_table_names(schema=schema)

        return json_result({
            "schema": schema,
            "count": len(tables),
            "tables": tables,
        })

    except SQLAlchemyError:
        return json_result({
            "error": "Unable to list tables. Check database access."
        })


@mcp.tool()
def describe_table(table_name: str, schema: str = "public") -> str:
    """Show column names, data types, and nullable status."""
    try:
        table = get_table(table_name, schema)

        columns = [
            {
                "name": column.name,
                "type": str(column.type),
                "nullable": column.nullable,
                "primary_key": column.primary_key,
            }
            for column in table.columns
        ]

        return json_result({
            "schema": schema,
            "table": table_name,
            "columns": columns,
        })

    except ValueError as exc:
        return json_result({"error": str(exc)})
    except SQLAlchemyError:
        return json_result({
            "error": "Unable to inspect table. Check database access."
        })


@mcp.tool()
def query_table(
    table_name: str,
    schema: str = "public",
    limit: int = 10,
    offset: int = 0,
) -> str:
    """Read rows from an existing table with pagination.

    Only SELECT is performed. Limit must be between 1 and 100.
    Offset must be zero or greater.
    """
    if not 1 <= limit <= 100:
        return json_result({"error": "limit must be between 1 and 100"})

    if offset < 0:
        return json_result({"error": "offset must be zero or greater"})

    try:
        table = get_table(table_name, schema)

        statement = select(table).limit(limit).offset(offset)

        with engine.connect() as connection:
            result = connection.execute(statement)
            rows = [dict(row) for row in result.mappings().all()]

        return json_result({
            "schema": schema,
            "table": table_name,
            "limit": limit,
            "offset": offset,
            "returned_rows": len(rows),
            "rows": rows,
        })

    except ValueError as exc:
        return json_result({"error": str(exc)})
    except SQLAlchemyError:
        return json_result({
            "error": "Query failed. Check database access and schema."
        })


if __name__ == "__main__":    
    print("Starting PostgreSQL MCP server...", file=sys.stderr, flush=True)
    mcp.run(transport="stdio")