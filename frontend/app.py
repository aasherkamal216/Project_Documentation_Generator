import streamlit as st
import requests
import json
from io import BytesIO

# Set the page configuration for the Streamlit app
st.set_page_config(page_title="Angular Project Analyzer", layout="wide")

# Set the title of the app
st.title("Angular Project Analyzer")

# Create a sidebar for user options
st.sidebar.header("Options")
# Dropdown to select the format for the help document
output_format = st.sidebar.selectbox(
    "Help Document Format",
    ["txt", "pdf"]
)

# File uploader for the user to upload their Angular project as a ZIP file
uploaded_file = st.file_uploader("Upload your Angular project (ZIP file)", type="zip")

# Check if a file has been uploaded
if uploaded_file:
    # Create two columns for UI graph generation and help documentation
    col1, col2 = st.columns(2)
    
    with col1:
        # Subheader for generating the UI graph
        st.subheader("Generate UI Graph")
        # Button to trigger graph generation
        if st.button("Generate Graph"):
            files = {"file": uploaded_file}  # Prepare the file for upload
            try:
                # Send a POST request to process the uploaded file
                response = requests.post("http://web:8000/process", files=files)
                if response.status_code == 200:
                    # Display the generated graph image
                    st.image(response.content)
                else:
                    # Show an error message if the response is not successful
                    st.error(f"Error: {response.status_code}")
            except Exception as e:
                # Handle any exceptions that occur during the request
                st.error(f"Error: {str(e)}")
    
    with col2:
        # Subheader for generating help documentation
        st.subheader("Generate Help Documentation")
        # Button to trigger documentation generation
        if st.button("Generate Documentation"):
            try:
                # First get the UI elements and navigation data
                files = {"file": uploaded_file}  # Prepare the file for upload
                
                # Get the extracted UI data from the backend
                response = requests.post("http://web:8000/extract_ui_data", files=files)
                
                if response.status_code == 200:
                    # Parse the UI data from the response
                    ui_data = response.json()
                    
                    # Create JSON payload with actual extracted data
                    help_doc_data = {
                        "UI_Elements": ui_data.get("elements", []),
                        "Navigation_Actions": ui_data.get("actions", []),
                        "Page_Names": ui_data.get("page_names", {})
                    }
                    
                    # Prepare the JSON data for the help document
                    files = {"file": ("data.json", json.dumps(help_doc_data))}
                    # Send a request to generate the help document
                    response = requests.post(
                        f"http://web:8000/generate_help_doc?file_type={output_format}",
                        files=files
                    )
                    
                    if response.status_code == 200:
                        # Check the output format and display or download the documentation
                        if output_format == "txt":
                            st.text_area("Generated Documentation", response.text, height=400)
                        else:
                            st.download_button(
                                "Download PDF",
                                response.content,
                                file_name="help_document.pdf",
                                mime="application/pdf"
                            )
                    else:
                        # Show an error message if documentation generation fails
                        st.error(f"Error generating documentation: {response.status_code}")
                else:
                    # Show an error message if file processing fails
                    st.error(f"Error extracting UI data: {response.status_code}")
            except Exception as e:
                # Handle any exceptions that occur during the request
                st.error(f"Error: {str(e)}")