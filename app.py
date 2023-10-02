import streamlit as st
from google.cloud import aiplatform
from sqlalchemy import *
from sqlalchemy.engine import create_engine


from langchain import SQLDatabase, SQLDatabaseChain
from langchain.llms import VertexAI

from langchain.prompts.prompt import PromptTemplate

PROJECT_ID = "<KEY-YOUR-PROJECT-ID>"
LOCATION = 'us-central1'
DATASET_ID = '<KEY-YOUR-DATASET-ID>'


#Intialise
aiplatform.init(
    project=PROJECT_ID,
    location=LOCATION,
)

project_id = PROJECT_ID
dataset_id = DATASET_ID
table_uri = f"bigquery://{project_id}/{dataset_id}"
engine = create_engine(f"bigquery://{project_id}/{dataset_id}") 


#intialise LLM
llm = VertexAI(
    model_name='text-bison@001',
    max_output_tokens=1024,
    temperature=0,
    top_p=1,
    top_k=1,
    verbose=True,
)

#Connection to DB with tables
db = SQLDatabase(engine=engine,metadata=MetaData(bind=engine),include_tables=['BusArrival4', 'WEATHER_DERIVED_PASSENGER_VOLUME_BY_BUSSTOP_202306', 'weather-data'])

db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True)#, return_direct=True)
db_chain_debug = SQLDatabaseChain.from_llm(llm, db, verbose=True, return_intermediate_steps=True)


_googlesql_prompt = """For given question, create a syntactically correct bigquery sql query.
Use table definitions to get the columns names and use only those column names.
You must query only the columns that are needed to answer the question. Wrap each column name in backticks (`) to denote them as delimited identifiers.
Use a limit given in the question and if not given then use a limit of {top_n}  in the query using bigquery LIMIT clause.

Only use the following tables:
{table_info}

Question: {input}"""

GOOGLESQL_PROMPT = PromptTemplate(
    input_variables=["input", "table_info", "top_n"],
    template=_googlesql_prompt,
)


# App title
st.set_page_config(page_title="💬 Chat with you Bigquery Data", page_icon="💬")
with st.sidebar:
    st.title('💬 Chat with you Bigquery Data')
    st.caption("Select a table and chat with your bigquery table. Alternatively you can also try out some of the pre-written prompts below!")


#Clear chat history
def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

#Your list of table to configure in Dataset
my_list = ['BusArrival4', 'WEATHER_DERIVED_PASSENGER_VOLUME_BY_BUSSTOP_202306', 'weather-data']
user_table = st.sidebar.selectbox("Select an option:", my_list)


#Pre-built prompt input for testing based on table
if user_table == 'WEATHER_DERIVED_PASSENGER_VOLUME_BY_BUSSTOP_202306':
    questions = ["Which day has the highest total volume?", 
             "Which bus stop has the highest total volume?", 
             "On the day with the highest rainfall, what is the total volume?"] 
    
elif user_table == 'weather-data':    
    questions = ["Which day is the hottest?", 
             "Which day has the highest rainfall?", 
             "Which day is the coldest?"]
    
else:
    questions = ["How many number of bus data are there?", 
             "What are the distinct bus numbers?", 
             "Which bus has the highest passenger count?"]

#Suggestion title
suggested_question= st.sidebar.selectbox("Try a few pre-written prompts:", questions)

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]


# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


# # Add execute button
if st.sidebar.button('Execute'):
    # If button pressed, use the selected dropdown option as input
    prompt2 = suggested_question
    st.session_state.messages.append({"role": "user", "content": prompt2})
    with st.chat_message("user"):
        st.write(prompt2)

# User-provided prompt
if  prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)


# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # response = db_chain(GOOGLESQL_PROMPT.format(input=prompt, table_info=user_table, top_n=5))
            if not prompt:
                response = db_chain_debug((GOOGLESQL_PROMPT.format(input=prompt2, table_info=user_table, top_n=5)))
            else:
                response = db_chain_debug((GOOGLESQL_PROMPT.format(input=prompt, table_info=user_table, top_n=5)))
            instructions = response['query']

            # Split the query into instructions and question
            instructions, question = response['query'].split("Question: ")

            # The result is directly accessed from the response dictionary
            result = response['result']
            to_write = response["intermediate_steps"]

            # Display result in the expandable box
            with st.expander("See explanation"):                
                placeholder_sql = st.empty()
                placeholder_sql_res = st.empty()
                placeholder_sql.markdown(f"**SQL Query:**\n{to_write[1]}")
                placeholder_sql_res.markdown(f"**SQL Result:**\n{to_write[3]}")

                # placeholder_query = st.empty()
                # placeholder_question = st.empty()
                # placeholder_query.markdown(f"**Query:**\n{instructions.strip()}")
                # placeholder_question.markdown(f"**Question:**\n{question.strip()}")


            # Display result in the required format and handle if result column is empty
            placeholder_result = st.empty()
            if not result.strip():
                result = to_write[3]
                
            placeholder_result.markdown(f"**Result:**\n{result.strip()}")
            

    message = {"role": "assistant", "content": f"{result.strip()}"}
    st.session_state.messages.append(message)
