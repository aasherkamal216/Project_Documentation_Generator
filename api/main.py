import os
import glob
import re
import json
import zipfile
import shutil
import networkx as nx
from bs4 import BeautifulSoup

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse

import matplotlib.pyplot as plt
from fpdf import FPDF

from help_document import generate_help_doc_with_llama

app = FastAPI()

UPLOADS_DIR = "/uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

def extract_files(source_path):
    """Extracts all HTML and TS files from the given directory."""
    html_files = glob.glob(os.path.join(source_path, '**/*.html'), recursive=True)
    ts_files = glob.glob(os.path.join(source_path, '**/*.ts'), recursive=True)
    return html_files, ts_files

def generate_unique_id(tag, index, tag_content):
    """Generates a unique ID for an HTML element if it doesn't have one."""
    return f"{tag}_{index}_{tag_content.strip()[:10]}" if tag_content.strip() else f"{tag}_{index}"

def parse_html(file_path):
    """Parses an HTML file and extracts relevant UI elements."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as file:
            content = file.read()

    soup = BeautifulSoup(content, 'html.parser')
    elements = []
    for index, tag in enumerate(soup.find_all(['button', 'input', 'a', 'form'])):
        tag_id = tag.get('id')
        tag_name = tag.get('name')
        tag_content = tag.get_text(strip=True)
        element_id = tag_id or tag_name or generate_unique_id(tag.name, index, tag_content)
        elements.append({'tag': tag.name, 'id': element_id, 'classes': tag.get('class', []), 'text': tag_content})
    return elements

def parse_typescript(ts_files):
    """Parses TypeScript files to extract page names and navigation actions."""
    page_names = {}
    page_names = {}
    actions = []
    for ts_file in ts_files:
        with open(ts_file, 'r', encoding='utf-8') as file:
            content = file.read()
        component_match = re.search(r'@Component\(\s*{([^}]*)}\s*\)', content, re.DOTALL)
        route_match = re.search(r'path:\s*\'(.*?)\'', content)
        component_name = os.path.basename(ts_file).replace('.ts', '')
        if component_match:
            selector_match = re.search(r'selector:\s*\'(.*?)\'', component_match.group(1))
            component_name = selector_match.group(1) if selector_match else component_name
        route = route_match.group(1) if route_match else component_name
        page_names[component_name] = route
        actions.extend(re.findall(r'this\.router\.navigate\(\s*\[([^]]*)\]\s*\)', content))
    return page_names, actions

def generate_graph(elements, actions, page_names):
    """Generates a directed graph representing UI navigation."""
    G = nx.DiGraph()
    for element in elements:
        G.add_node(element['id'], label=element['tag'], text=element['text'])
    for action in actions:
        for page_name, route in page_names.items():
            if route in action:
                source = next((el['id'] for el in elements if el['tag'] == 'button' and el['id'] != 'unknown'), 'source_node')
                G.add_edge(source, page_name, action="navigate")
    return G

def visualize_graph(graph, output_path):
    """Visualizes the graph and saves it to an image file."""
    pos = nx.spring_layout(graph, seed=42)
    plt.figure(figsize=(16, 14))
    nx.draw(graph, pos, with_labels=True, node_size=4000, node_color="lightblue", font_size=8, edge_color="black", arrows=True, arrowsize=20)
    nx.draw_networkx_edge_labels(graph, pos, edge_labels={(u, v): d['action'] for u, v, d in graph.edges(data=True)}, font_size=8)
    plt.title("UI and Navigation Graph")
    plt.savefig(output_path)
    plt.close()

def extract_and_parse_zip(file: UploadFile):
    """Common function to extract and parse a ZIP file"""
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are supported.")
    
    file_path = os.path.join(UPLOADS_DIR, file.filename)
    with open(file_path, "wb") as temp_zip:
        shutil.copyfileobj(file.file, temp_zip)
    
    extracted_path = os.path.join(UPLOADS_DIR, "extracted")
    # Clear previous extraction if exists
    if os.path.exists(extracted_path):
        shutil.rmtree(extracted_path)
    
    os.makedirs(extracted_path, exist_ok=True)
    
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extracted_path)
    
    html_files, ts_files = extract_files(extracted_path)
    all_elements = [parse_html(html_file) for html_file in html_files]
    all_elements = [item for sublist in all_elements for item in sublist]
    page_names, actions = parse_typescript(ts_files)
    
    return all_elements, actions, page_names


@app.post("/extract_ui_data")
async def extract_ui_data(file: UploadFile = File(...)):
    """Endpoint to extract UI elements, actions, and page names without generating a graph"""
    all_elements, actions, page_names = extract_and_parse_zip(file)
    
    return JSONResponse({
        "elements": all_elements,
        "actions": actions,
        "page_names": page_names
    })

@app.post("/process")
async def process_source_code(file: UploadFile = File(...)):
    """Endpoint to process the uploaded file and generate a UI graph"""
    all_elements, actions, page_names = extract_and_parse_zip(file)
    
    graph = generate_graph(all_elements, actions, page_names)
    graph_image_path = os.path.join(UPLOADS_DIR, "ui_graph.png")
    visualize_graph(graph, graph_image_path)
    return FileResponse(graph_image_path, filename="ui_graph.png")

@app.post("/generate_help_doc")
async def generate_help_doc(file: UploadFile = File(...), file_type: str = "txt"):
    """Endpoint to generate a help document based on the extracted UI data."""
    try:
        content = await file.read()
        data = json.loads(content)
        elements = data.get("UI_Elements", [])
        actions = data.get("Navigation_Actions", [])
        page_names = data.get("Page_Names", [])
        help_doc = generate_help_doc_with_llama(elements, actions, page_names)
        file_path = f"help_document.{file_type}"
        if file_type == "txt":
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(help_doc)
        elif file_type == "pdf":
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            for line in help_doc.split("\n"):
                pdf.cell(200, 10, txt=line, ln=True)
            pdf.output(file_path)
        else:
            raise HTTPException(status_code=400, detail="Invalid file type.")
        return FileResponse(file_path, filename=file_path, media_type="application/octet-stream")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/")
def root():
    return {"message": f"Upload a zipped Angular project to /process endpoint. Files are saved in {UPLOADS_DIR}"}
