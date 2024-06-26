This project is a simple program that allow chatting with a database of your choice instaled in your computer by MySQL.

Here are the dependencies:

To run the provided Python code, you'll need to install several libraries. Here is the list of required libraries:

time: A standard Python library for handling time-related operations.

dotenv: Used to load environment variables from a .env file.

langchain_core.messages: Manages AI and human messages.

langchain_core.prompts: Used to create prompt templates for the conversation flow.

langchain_core.runnables: Provides functionalities to execute data processing flows.

langchain_community.utilities: Includes utilities to interact with SQL databases.

langchain_core.output_parsers: Used to parse text outputs.

langchain_groq: Provides specific functionalities to interact with the ChatGroq model.

streamlit: Used to build the interactive web interface.

After installing these libraries, you should be able to run the code without issues, as long as all other components (such as models and the database) are correctly set up and accessible.


Add your keys in the .env file and install the libraries 

pip install python-dotenv langchain-core langchain-community langchain-groq streamlit

