import streamlit as st
from analyzer.python_analyzer import analyze_python_project, explain_python_code
from analyzer.java_analyzer import analyze_java_project, explain_java_code
import os
import zipfile
import tempfile
import re
import requests
import shutil
import uuid

st.set_page_config(page_title="Code Analyzer with Ollama", layout="wide")
st.title("🛠 Code Analyzer for Python and Java with Ollama")

# Ollama configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "codellama:7b"

language = st.selectbox("Select Language", ["Python", "Java"])
uploaded_file = st.file_uploader("Upload a ZIP file containing your project", type=["zip"])

def query_ollama(prompt):
    """Send query to Ollama and return response."""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3}
            }
        )
        response.raise_for_status()
        return response.json().get("response", "Error: No response from Ollama")
    except requests.exceptions.HTTPError as e:
        return f"Error querying Ollama: {str(e)}. Ensure model `{OLLAMA_MODEL}` is listed in `ollama list` and server is running (`ollama serve`)."
    except requests.exceptions.ConnectionError:
        return "Error: Ollama server not running at localhost:11434. Start it with `ollama serve`."
    except Exception as e:
        return f"Unexpected error querying Ollama: {str(e)}. Check server and model availability."

if uploaded_file is not None:
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save the uploaded ZIP file to the temporary directory
        zip_path = os.path.join(temp_dir, uploaded_file.name)
        with open(zip_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Extract the ZIP file
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            st.success(f"ZIP file extracted to temporary directory: {temp_dir}")
        except zipfile.BadZipFile:
            st.error("Invalid ZIP file. Please upload a valid ZIP file.")
            st.stop()

        query = st.text_input(
            "Ask a question (e.g., classes, how many classes and name them, show methods, what does code do, how many libraries):")

        if query:
            q = query.lower().strip()
            project_path = temp_dir

            # Perform fresh analysis for each query
            if language == "Python":
                analysis = analyze_python_project(project_path)
                classes = [c for data in analysis.values() for c in data["classes"]]
                functions = [f for data in analysis.values() for f in data["functions"]]
                methods = [m for data in analysis.values() for m in data["methods"]]
                imports = [i for data in analysis.values() for i in data["imports"]]
                context = (
                    f"Python project with {len(classes)} classes ({', '.join(classes)}), "
                    f"{len(functions)} functions ({', '.join(functions) if functions else 'none'}), "
                    f"{len(methods)} methods ({', '.join(methods) if methods else 'none'}), "
                    f"and {len(imports)} imported modules ({', '.join(imports) if imports else 'none'}). "
                    f"It’s a code analysis tool using the `ast` module."
                )
            else:
                analysis = analyze_java_project(project_path)
                classes = [c for v in analysis.values() for c in v["classes"]]
                methods = [m for v in analysis.values() for m in v["methods"]]
                imports = [i for v in analysis.values() for i in v["imports"]]
                superclasses = [sc for v in analysis.values() for sc in v["superclass"]]
                interfaces = [iface for v in analysis.values() for iface in v["interfaces"]]
                context = (
                    f"Java project with {len(classes)} classes ({', '.join(classes)}), "
                    f"{len(methods)} methods ({', '.join(methods) if methods else 'none'}), "
                    f"{len(imports)} imported packages ({', '.join(imports) if imports else 'none'}), "
                    f"superclasses ({', '.join(superclasses) if superclasses else 'none'}), "
                    f"and interfaces ({', '.join(interfaces) if interfaces else 'none'}). "
                    f"This is a Java project with the uploaded code structure."
                )

            # Handle combined class queries
            class_count_match = re.search(r'\b(how\s+many|count|number\s+of)\b.*\b(class|classes)\b', q)
            class_list_match = re.search(r'\b(name|list|show|what|which|all)\b.*\b(class|classes)\b',
                                         q) or q == "classes" or "name them" in q or "present in project" in q
            if class_count_match or class_list_match:
                count = sum(len(data["classes"]) for data in analysis.values())
                classes = [c for data in analysis.values() for c in data["classes"]]
                if class_count_match:
                    st.write(f"Total classes: {count}")
                if class_list_match and classes:
                    st.write("Classes:\n" + "\n".join(classes))
                elif class_list_match:
                    st.write("No classes found.")
            # Handle superclass queries
            elif language == "Java" and re.search(r'\b(how\s+many|count|number\s+of)\b.*\b(superclass|superclasses)\b', q):
                superclasses = [sc for data in analysis.values() for sc in data["superclass"]]
                count = len([sc for sc in superclasses if "has no superclass" not in sc])
                st.write(f"Total superclasses: {count}")
            elif language == "Java" and (re.search(r'\b(name|list|show|what|which|all)\b.*\b(superclass|superclasses)\b', q) or q == "superclasses"):
                superclasses = [sc for data in analysis.values() for sc in data["superclass"]]
                if superclasses:
                    st.write("Superclasses:\n" + "\n".join([sc for sc in superclasses if "has no superclass" not in sc]))
                else:
                    st.write("No superclasses found.")
            # Handle interface queries
            elif language == "Java" and re.search(r'\b(how\s+many|count|number\s+of)\b.*\b(interface|interfaces)\b', q):
                interfaces = [iface for data in analysis.values() for iface in data["interfaces"]]
                count = len([iface for iface in interfaces if "implements no interfaces" not in iface])
                st.write(f"Total interfaces: {count}")
            elif language == "Java" and (re.search(r'\b(name|list|show|what|which|all)\b.*\b(interface|interfaces)\b', q) or q == "interfaces"):
                interfaces = [iface for data in analysis.values() for iface in data["interfaces"]]
                if interfaces:
                    st.write("Interfaces:\n" + "\n".join([iface for iface in interfaces if "implements no interfaces" not in iface]))
                else:
                    st.write("No interfaces found.")
            # Handle library queries
            elif re.search(r'\b(how\s+many|count|number\s+of)\b.*\b(librar(y|ies)|module|modules|package|packages)\b', q):
                imports = [i for data in analysis.values() for i in data["imports"]]
                unique_imports = sorted(set(imports))
                st.write(f"Total {('modules' if language == 'Python' else 'packages')}: {len(unique_imports)}")
            elif re.search(r'\b(name|list|show|what|which|all)\b.*\b(librar(y|ies)|module|modules|package|packages)\b', q) or "name them" in q:
                imports = [i for data in analysis.values() for i in data["imports"]]
                unique_imports = sorted(set(imports))
                if unique_imports:
                    st.write(f"{('Modules' if language == 'Python' else 'Packages')}:\n" + "\n".join(unique_imports))
                else:
                    st.write(f"No {('modules' if language == 'Python' else 'packages')} found.")
            # Handle methods/functions
            elif re.search(r'\b(how\s+many|count|number\s+of)\b.*\b(function|functions|method|methods)\b', q):
                if language == "Python":
                    count = sum(len(data["functions"]) for data in analysis.values())
                    st.write(f"Total functions: {count}")
                else:
                    count = sum(len(v["methods"]) for v in analysis.values())
                    st.write(f"Total methods: {count}")
            elif re.search(r'\b(name|list|show|what|which|all)?\b.*\b(function|functions|method|methods)\b', q) or q in ["methods", "functions"]:
                if language == "Python":
                    functions = [f for data in analysis.values() for f in data["functions"]]
                    methods = [m for data in analysis.values() for m in data["methods"]]
                    if functions or methods:
                        st.write(f"Total functions: {len(functions)}")
                        if functions:
                            st.write("Functions:\n" + ", ".join(functions))
                        st.write(f"Total methods: {len(methods)}")
                        if methods:
                            st.write("Methods:\n" + ", ".join(methods))
                    else:
                        st.write("No functions or methods found.")
                else:
                    methods = [m for v in analysis.values() for m in v["methods"]]
                    if methods:
                        st.write(f"Total methods: {len(methods)}")
                        st.write("Methods:\n" + ", ".join(methods))
                    else:
                        st.write("No methods found.")
            # Handle explanation queries
            elif re.search(r'\b(explain|describe|what|about|summary)\b.*\b(code|project|it|does|functionality|purpose)?\b', q) or q in ["explain", "what code describes", "describe code"]:
                if language == "Python":
                    base_explanation = explain_python_code(project_path)
                    purpose = "This Python project is a code analysis tool that parses Python source files to extract structural elements like classes, functions, methods, and global variables using the `ast` module."
                else:
                    base_explanation = explain_java_code(project_path)
                    purpose = f"This Java project is designed to manage its specific functionality based on the uploaded code. {base_explanation}"
                prompt = f"{context}\n\nStructural analysis:\n{base_explanation}\n\nQuery: {query} [Unique ID: {uuid.uuid4()}]\n\nProvide a clear, concise explanation addressing the query, using the context and analysis. Focus on the project's functionality and purpose."
                response = query_ollama(prompt)
                st.subheader("📝 Project Explanation")
                st.markdown(f"{purpose}\n\n{response}")
            # Show extracted elements
            elif "show extracted elements" in q or "extracted elements" in q:
                st.subheader("📋 Extracted Elements")
                st.json(analysis)
            # Fallback to Ollama
            else:
                prompt = f"{context}\n\nQuery: {query} [Unique ID: {uuid.uuid4()}]\n\nAnswer the query based on the project context. If it’s about code structure, summarize classes, methods, superclasses, interfaces, or imports. If it’s unclear, ask for clarification."
                response = query_ollama(prompt)
                st.write(f"Ollama Response: {response}")
else:
    st.info("Please upload a ZIP file containing your project.")