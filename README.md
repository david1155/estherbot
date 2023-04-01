# Flask Chatbot with GPT-4

This is a Flask-based chatbot application that uses OpenAI's GPT-4 model for generating responses. The application uses Flask-SocketIO for real-time communication between the server and the client.

## Environment Variables

- `SYSTEM_CONTENT`: Configuration of the chat bot, e.g. "Act as a sales bot. Try to collect name, company and phone number. My company Acme Inc. info: " (Optional)
- `TEMPERATURE`: Controls the randomness of the model's output. Higher values (e.g., 2) make the output more random, while lower values (e.g., 0) make it more deterministic. Default is 0.75.
- `MODEL`: The name of the OpenAI model to use. Default is "gpt-4".
- `OPENAI_API_KEY`: Your OpenAI API key, which can be obtained from the OpenAI website.

## Docker Images

Docker images for this application are available on the [releases page](https://github.com/david1155/estherbot/releases).

## Running the Application with Docker

1. Pull the Docker image:

   ```
   docker pull david1155/estherbot:latest
   ```

2. Run the Docker container:

   ```
   docker run -d -p 5000:5000 -e OPENAI_API_KEY=your_api_key -e SYSTEM_CONTENT="Act as a helpful chatbot" -e TEMPERATURE=0 -e MODEL="gpt-3.5-turbo" david1155/estherbot:latest
   ```

   Replace `your_api_key` with your OpenAI API key, and adjust other environment variables as needed.

3. Access the application in your browser at `http://localhost:5000`.

## Obtaining an OpenAI API Key

To obtain an API key for GPT-4, visit the [OpenAI website](https://platform.openai.com/) and sign up for an account. Once you have an account, you can access your API key from the dashboard.
