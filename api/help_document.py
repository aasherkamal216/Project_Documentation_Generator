import os
from fastapi import HTTPException

import requests
import json
from fpdf import FPDF


MODEL_NAME = "llama3.1"  # Can be changed
BASE_URL = "http://ollama:11434/api/generate"

def generate_help_doc_with_llama(elements, actions, page_names):

    """Generate a human-readable help document using Llama 2 locally."""
    summary = {
        "UI_Elements": elements,
        "Navigation_Actions": actions,
        "Page_Names": page_names
    }

    prompt = f"""
You are an expert in Angular applications and your task is to generate a comprehensive and user-friendly help document based on the following project structure. The document should be clear and easy for end-users (non-technical users) to understand. The data includes:

1-UI Elements: These include components like forms, buttons, inputs, links, and navigation menus. For each UI element, provide a description of its purpose in the app, what it does, and how users interact with it.
2-Navigation Actions: These describe how users move between different parts of the app. Highlight important user flows, such as buttons or links that navigate to different pages, and explain how users can perform actions like clicking or submitting forms.
3-Page Names and Routes: These are the pages of the application and the routes associated with them. Include a short description of each page, its role in the app, and any major features or actions available on those pages.

Please ensure the help document covers the following:
-Descriptions for each UI element: {summary['UI_Elements']} and its functionality.
-Clear explanations of the actions users can take within the app.
-A guide to navigating the app: {summary['Navigation_Actions']}, focusing on the main user flows.
-A list of pages and routes: {summary['Page_Names']}, with simple explanations about their purpose and how to use them.

The document should be written in a way that is easily understandable for someone with no technical background and should provide all the necessary information for end-users to effectively navigate and use the application.
"""

    try:
        response = requests.post(
            BASE_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            }
        )
        answer = json.loads(response.text)['response']
        return answer

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating help document: {str(e)}")
