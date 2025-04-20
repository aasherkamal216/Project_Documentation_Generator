# Documentation Generator

This project provides a streamlined solution for analyzing Angular projects, visualizing their UI structure, and automatically generating documentation. It leverages a combination of tools, including Streamlit for the frontend, FastAPI for the backend API, and Ollama for running the models locally.

# Setup

Ensure Docker and Docker Compose are installed and running on your system.

## Running the Project

1.  Start the services using Docker Compose:

    ```bash
    docker compose up --build
    ```

    This command builds the necessary Docker images and starts the services defined in `compose.yaml`.

2.  Access the frontend in your web browser at `http://localhost:8501`.

## Using the Application

1.  Upload your Angular project as a ZIP file through the Streamlit frontend.
2.  Click the "Generate Graph" button to visualize the UI graph.
3.  Click the "Generate Documentation" button to create help documentation.  You can select the format (txt or pdf) in the sidebar.
4.  The generated graph will be displayed, and the documentation will be shown or offered for download, depending on the selected format.

## Changing the Model Name

To change the Ollama model used for generating help documentation:

1.  **Modify `ollama/pull-llama3.sh`**:

    *   Edit the line `ollama pull llama3.1` to pull your desired model. For example, to use the `llama3.3` model, change the line to:

        ```bash
        ollama pull llama3.3
        ```

    *   Also, modify the model name in `grep` command:

        ```bash
        if ! ollama list | grep -q "llama3.3"; then
        ```

2.  **Modify `api/help_document.py`**:

    *   Update the `MODEL_NAME` variable to match the model you specified in the script:

        ```python
        MODEL_NAME = "llama3.3"
        ```

3.  Rebuild and restart the Docker containers:

    ```bash
    docker-compose up --build --force-recreate
    ```

    The `--force-recreate` option ensures that the containers are recreated with the updated configurations.

## Configuration

The application uses the following ports:

-   Frontend: `8501`
-   API: `8000`
-   Ollama: `11434`

These ports are defined in the `compose.yaml` file and can be adjusted as needed.

## Volumes

The following volumes are used:

-   `ollama_data`:  Persists Ollama model data.
-   `uploads`: Stores uploaded Angular projects and generated outputs.
