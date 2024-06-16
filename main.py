import re
import os
import time
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
import streamlit as st

load_dotenv("key.env")


def init_database(user, password, host, port, database) -> SQLDatabase:
    db_uri = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
    return SQLDatabase.from_uri(db_uri)


def get_sql_chain(db):
    # Definir la cadena SQL y el modelo de lenguaje una vez
    template = """
    You are a specialist in international basketball player scouting you are fast and efficient.  
    Based on the table schema below, write an SQL query that would answer the user's question. 
    Take into account the conversation history.

    Additionally, knowing that you work in collaboration with the website sportiw, you will provide the link to each profile so that whenever you request information about any player, you will also save the information about their ProfileID, which you will use to generate a link for each player as follows:

    https://sportiw.com/athletes/Lastname.Firstname/ProfileID

    If spaces appear in the link, the syntax will be:

    https://sportiw.com/en/athletes/Dossou%20Yovo.Mathis/45937

    <SCHEMA>{schema}</SCHEMA>

    Conversation history: {chat_history}

    Write only SQL and nothing else. Do not wrap the SQL query in any other text, not even in backticks. Do not write anything that is not an SQL command.

    Example:
    Question: Can you propose a list 15 players with a free throw statistic greater than 50?
    SQL Query: SELECT DISTINCT u.Firstname, u.Lastname, pe.GameFreeThrowsStatistic, CONCAT('https://sportiw.com/en/athletes/', REPLACE(CONCAT(u.Lastname, '.', u.Firstname), ' ', '%20'), '/', p.ProfileID) AS link FROM users u JOIN profile p ON u.ID = p.userID JOIN profile_experiences pe ON p.ProfileID = pe.ProfileID WHERE pe.GameFreeThrowsStatistic > 50 ORDER BY pe.GameFreeThrowsStatistic DESC LIMIT 15;
    Question: Give me 10 athletes who have played in NCAA
    SQL Query: SELECT DISTINCT u.Firstname, u.Lastname, u.Height, CONCAT('https://sportiw.com/en/athletes/', REPLACE(CONCAT(u.Lastname, '.', u.Firstname), ' ', '%20'), '/', p.ProfileID) AS link FROM users u JOIN profile p ON u.ID = p.userID JOIN profile_experiences pe ON p.ProfileID = pe.ProfileID WHERE pe.League LIKE '%NCAA%' ORDER BY u.Height ASC LIMIT 10; 
    Question: Who has played in national 3?
    SQL Query: SELECT DISTINCT u.Firstname, u.Lastname, CONCAT('https://sportiw.com/en/athletes/', REPLACE(CONCAT(u.Lastname, '.', u.Firstname), ' ', '%20'), '/', p.ProfileID) AS link FROM users u JOIN profile p ON u.ID = p.userID JOIN profile_experiences pe ON p.ProfileID = pe.ProfileID WHERE pe.League = 'National 3';

    
    Your turn:

    Question: {question}
    SQL Query:
    """
    prompt = ChatPromptTemplate.from_template(template)

    llm = ChatGroq(model="llama3-70b-8192", temperature=0)

    def get_schema(_):
        return db.get_table_info()

    return (
        RunnablePassthrough.assign(schema=get_schema) | prompt | llm | StrOutputParser()
    )


def get_response(user_query, db: SQLDatabase, chat_history: list):
    sql_chain = get_sql_chain(db)

    template = """
    Write the SQl Query response in human way. Do not give information about the SQL Query, just answer.
    Do not generate information, just put whatever the SQL Query comes out in human way.
    
    SQL Query: <SQL>{query}</SQL>
    User question: {question}
    SQL response: {response}
    """

    prompt = ChatPromptTemplate.from_template(template)

    llm = ChatGroq(model="mixtral-8x7b-32768", temperature=0)

    chain = (
        RunnablePassthrough.assign(query=sql_chain).assign(
            schema=lambda _: db.get_table_info(),
            response=lambda vars: db.run(vars["query"]),
        )
        | prompt
        | llm
        | StrOutputParser()
    )
    start_time = time.time()
    response = chain.invoke(
        {
            "question": user_query,
            "chat_history": chat_history,
        }
    )

    elapsed_time = time.time() - start_time

    if "No results found" in response:
        response = "Theres no result found for that question."
    elif not response:
        response = "Response not found."
    else:
        response += f"\n\nTime taken: {elapsed_time:.2f} seconds."

    return response


if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(
            content="Hi! I'm the Sportiw Database Chat! What can I help you with?"
        )
    ]

# Configuración de la página
st.set_page_config(page_title="SDC", page_icon=":speech_balloon:")

st.title("SDC")

with st.sidebar:
    st.subheader("Database connection")
    st.write(
        "This is an user-friendly application that allows you to ask question about a database!"
    )

    st.text_input("Host", value="localhost", key="Host")
    st.text_input("Port", value="3306", key="Port")
    st.text_input("Username", value="root", key="User")
    st.text_input("Password", type="password", value="asir", key="Password")
    st.text_input("Database", value="terminado", key="Database")

    if st.button("Connect"):
        with st.spinner("Joining database..."):
            db = init_database(
                st.session_state["User"],
                st.session_state["Password"],
                st.session_state["Host"],
                st.session_state["Port"],
                st.session_state["Database"],
            )
            st.session_state.db = db
            st.success("Connection succeded!")

# Mostrar el historial de chat
for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI"):
            st.markdown(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.markdown(message.content)

# Captura de la entrada del usuario
user_query = st.chat_input("Ask...")
if user_query is not None and user_query.strip() != "":
    st.session_state.chat_history.append(HumanMessage(content=user_query))

    with st.chat_message("Human"):
        st.markdown(user_query)

    with st.chat_message("AI"):
        with st.spinner("Thinking..."):
            response = get_response(
                user_query, st.session_state.db, st.session_state.chat_history
            )
        st.markdown(response)
        # Agregar la respuesta del bot al historial de chat
        st.session_state.chat_history.append(AIMessage(content=response))
