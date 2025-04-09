import asyncio
import shutil
import streamlit as st
from agents import Agent, Runner, trace
from agents.mcp import MCPServer, MCPServerStdio

async def query_git_repo(mcp_server: MCPServer, directory_path: str, query: str):
    agent = Agent(
        name="Assistant",
        instructions=f"Answer questions about the localgit repository at {directory_path}, use that for repo_path",
        mcp_servers=[mcp_server],
    )

    with st.spinner(f"Running query: {query}"):
        result = await Runner.run(starting_agent=agent, input=query)
        return result.final_output

async def run_streamlit_app():
    st.title("Local Git Repo Explorer")
    st.write("This app allows you to query information about a local git repository.")

    directory_path = st.text_input("Enter the path to the git repository:")

    if directory_path:
        # Common queries as buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Most frequent contributor"):
                query = "Who's the most frequent contributor?"
                run_query(directory_path, query)

        with col2:
            if st.button("Last change summary"):
                query = "Summarize the last change in the repository."
                run_query(directory_path, query)

        # Custom query
        custom_query = st.text_input("Or enter your own query:")
        if st.button("Run Custom Query") and custom_query:
            run_query(directory_path, custom_query)

def run_query(directory_path, query):
    if not shutil.which("uvx"):
        st.error("uvx is not installed. Please install it with `pip install uvx`.")
        return

    async def execute_query():
        async with MCPServerStdio(
            cache_tools_list=True,
            params={
                "command": "python", 
                "args": [
                    "-m", 
                    "mcp_server_git", 
                    "--repository", 
                    directory_path
                ]
            },
        ) as server:
            with trace(workflow_name="MCP Git Query"):
                result = await query_git_repo(server, directory_path, query)
                st.markdown("### Result")
                st.write(result)

    asyncio.run(execute_query())

if __name__ == "__main__":
    st.set_page_config(
        page_title="Local Git Repo Explorer",
        page_icon="📊",
        layout="centered"
    )
    # Change from async to synchronous implementation
    # Since Streamlit doesn't work well with asyncio in the main thread

    # Define a synchronous version of our app
    def main_streamlit_app():
        st.title("Local Git Repo Explorer")
        st.write("This app allows you to query information about a Git repository.")

        directory_path = st.text_input("Enter the path to the git repository:")

        if directory_path:
            # Common queries as buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Most frequent contributor"):
                    query = "Who's the most frequent contributor?"
                    run_query(directory_path, query)

            with col2:
                if st.button("Last change summary"):
                    query = "Summarize the last change in the repository."
                    run_query(directory_path, query)

            # Custom query
            custom_query = st.text_input("Or enter your own query:")
            if st.button("Run Custom Query") and custom_query:
                run_query(directory_path, custom_query)

    # Run the synchronous app
    main_streamlit_app()