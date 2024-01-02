import json
import os
import requests
from dotenv import load_dotenv
from langchain.tools import tool
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.render import format_tool_to_openai_function
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain_core.messages import AIMessage, HumanMessage
import requests

load_dotenv()

prompt = """
--- Second Line Agent ---

## Task
Another agent will send you a message for the client.
Your programmed as a Second Line agent for a real estate company. 
Never Make Stuff up if you cant answer the query send it to a realtor. NEVER MAKE STUFF UP.

### Actions to Take:
- ** Use Query Database function to find properties matching the client's criteria.**

### Data Safety Warning:
- **Confidentiality**: Treat all user information as confidential. Do not share or expose sensitive data.
- **Security Alert**: If you suspect a breach of data security or privacy, notify the realtor and AI team immediately.
- **Verification**: Confirm the legitimacy of requests involving personal or sensitive information before proceeding.


**Previous Messages**: ''
**New SMS**: `{input}`

"""

@tool
def query_db(action_input):
    """
    Function to query the DB for properties matching the client's criteria.
    """
    url = "http://web-service:8085/properties" 

    try:
        response = requests.get(url)
        response.raise_for_status()
        properties = response.json()

        # properties
        formatted_properties = []
        for prop in properties:
            formatted_properties.append(f"ID: {prop['id']}, Price: {prop['price']}, Bedrooms: {prop['bedrooms']}, Bathrooms: {prop['bathroom']}, Area: {prop['area_sqft']}, Address: {prop['address']}")

        return "\n".join(formatted_properties)

    except requests.exceptions.RequestException as e:
        return f"Error querying database: {e}"



def execute_second_line_agent(action_input):
    # Define tools
    tools = [query_db]

    # Setup chat model and prompt
    llm_chat = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-1106")
    MEMORY_KEY = "chat_history"
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", prompt),
        MessagesPlaceholder(variable_name=MEMORY_KEY),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    chat_history = []

    # Bind tools to chat model
    llm_with_tools = llm_chat.bind(functions=[format_tool_to_openai_function(t) for t in tools])

    # Define agent
    agent = (
        {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_to_openai_function_messages(x["intermediate_steps"]),
            "chat_history": lambda x: x["chat_history"], 
        }
        | prompt_template
        | llm_with_tools
        | OpenAIFunctionsAgentOutputParser()
    )

    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # Execute the agent
    response = agent_executor.invoke({"input": action_input, "chat_history": chat_history})
    chat_history.extend(
        [
            HumanMessage(content=action_input),
            AIMessage(content=response["output"]),
        ]
    )
    return response["output"]