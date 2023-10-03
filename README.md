# nl2sql

## Getting Started

1. Clone this repository to your local machine.
1. Install the required dependencies using the following command:

    ```bash
    pip install -r requirements.txt
    ```

1. Fill in your project_id, location, datset_id, table names and list of pre selected questions template in app.py based on requirements

1. Run app.py to start the Streamlit application:

    ```bash
    streamlit run app.py
    ```

1. Open the Streamlit application in your web browser using the provided URL.

## Usage

### Chat
1. Input your question in the text box, either in English or any other natural language.
1. Press "Send" to send the question to the application or select pre-selected question
1. The application will process the question using Palm2 and LangChain, converting it SQL and retrieve result from Bigquery.
1. Data from Bigquery will be displayed on the chat box with history appended.
