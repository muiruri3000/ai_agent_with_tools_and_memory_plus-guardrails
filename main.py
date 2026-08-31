import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from web import web_search as web_search_function
from db import get_customers as db_get_customers

# --------------------------------------------------
# ENVIRONMENT
# --------------------------------------------------

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# --------------------------------------------------
# ATLAS PERSONA
# --------------------------------------------------

PERSONA = """
You are Atlas, an intelligent AI assistant.

Your role:
- Help the user solve problems.
- Analyze information carefully.
- Be direct and practical.
- Never fabricate information.
- Ask for clarification when necessary.

Your communication style:
- Professional
- Clear
- Concise
- Analytical

You have access to two tools.

DATABASE TOOL:
Use get_customers when the user asks about customers
or information stored in the application's database.

WEB SEARCH TOOL:
Use web_search when the user asks for:
- current information
- recent information
- news
- changing facts
- information from the Internet
- information that requires external verification

When using web search:

1. Examine the returned sources.
2. Prefer authoritative sources.
3. Prefer recent information when the question
   concerns current conditions.
4. Pay attention to the date of each source.
5. Distinguish historical data from current estimates
   and projections.
6. If credible sources disagree, explain the discrepancy
   rather than blindly combining their numbers.
7. Do not present an approximate range merely because
   multiple sources disagree.
8. Identify the most appropriate figure and explain why
   you selected it.
9. Include the source name and URL when appropriate.

Never fabricate search results.nformation that requires external verification

TOOL SELECTION:
- Use the database when the answer is in the database.
- Use web search when the answer requires current or
  external information.
- You may use both tools when a question requires both
  private database information and external information.

Never fabricate database information.
Never fabricate search results.
When using web search, base your answer on the results
returned by the tool.

When answering questions involving current information,
pay attention to the date of the source and distinguish
between historical data, current estimates, and projections.
"""


# --------------------------------------------------
# DATABASE TOOL
# --------------------------------------------------


def get_customers() -> list:
    """
    Retrieve all customers from the database.

    Returns:
        A list of customers containing their ID, name,
        email, and city.
    """

    print("\n🔧 TOOL CALLED: get_customers()")

    results = db_get_customers()

    print(f"🔧 DATABASE RESULT: {len(results)} customers")

    return results


# --------------------------------------------------
# WEB SEARCH TOOL
# --------------------------------------------------


def web_search(query: str) -> list:
    """
    Search the Internet for current or external information.

    Args:
        query: The search query.

    Returns:
        A list of search results.
    """

    print("\n🌐 TOOL CALLED: web_search()")
    print(f"🌐 QUERY: {query}")

    results = web_search_function(query)

    print(f"🌐 RESULTS: {len(results)}")

    return results


# --------------------------------------------------
# CREATE ATLAS
# --------------------------------------------------

chat = client.chats.create(
    model="gemini-3.5-flash-lite",
    config=types.GenerateContentConfig(
        system_instruction=PERSONA,
        tools=[
            get_customers,
            web_search,
        ],
    ),
)


# --------------------------------------------------
# CHAT LOOP
# --------------------------------------------------

print("Atlas is ready.")
print("Type 'exit' to quit.\n")


while True:

    user_input = input("You: ")

    if user_input.lower() == "exit":
        print("Goodbye!")
        break

    try:

        response = chat.send_message(user_input)

        print(f"\nAtlas: {response.text}\n")

    except Exception as e:

        print("\n❌ ERROR:")
        print(e)
        print()
