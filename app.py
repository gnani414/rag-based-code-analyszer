import streamlit as st
from analyzer.python_analyzer import analyze_python_project, explain_python_code
from analyzer.java_analyzer import analyze_java_project, explain_java_code
from analyzer.javascript_analyzer import analyze_javascript_project, explain_javascript_code
from analyzer.c_analyzer import analyze_c_project, explain_c_code
from analyzer.php_analyzer import analyze_php_project, explain_php_code
import os
import zipfile
import tempfile
import re
import requests
import uuid

st.set_page_config(page_title="Code Analyzer with Ollama", layout="wide")
st.title("🛠 Code Analyzer for Python, Java, JavaScript, C, and PHP with Ollama")

# Ollama configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "codellama:7b"

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

        # Detect languages by scanning file extensions
        languages_detected = []
        python_files = []
        java_files = []
        javascript_files = []
        c_files = []
        php_files = []
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
                    if 'Python' not in languages_detected:
                        languages_detected.append('Python')
                elif file.endswith('.java'):
                    java_files.append(os.path.join(root, file))
                    if 'Java' not in languages_detected:
                        languages_detected.append('Java')
                elif file.endswith('.js'):
                    javascript_files.append(os.path.join(root, file))
                    if 'JavaScript' not in languages_detected:
                        languages_detected.append('JavaScript')
                elif file.endswith(('.c', '.h')):
                    c_files.append(os.path.join(root, file))
                    if 'C' not in languages_detected:
                        languages_detected.append('C')
                elif file.endswith('.php'):
                    php_files.append(os.path.join(root, file))
                    if 'PHP' not in languages_detected:
                        languages_detected.append('PHP')

        if not languages_detected:
            st.error("No supported source files (.py, .java, .js, .c, .h, .php) found in the project.")
            st.stop()

        st.info(f"Detected languages: {', '.join(languages_detected)}")

        query = st.text_input(
            "Ask a question (e.g., classes, structs, traits, how many functions, list methods, what does code do, how many libraries):")

        if query:
            q = query.lower().strip()
            project_path = temp_dir

            # Perform analysis for each detected language
            analysis = {}
            python_analysis = {}
            java_analysis = {}
            javascript_analysis = {}
            c_analysis = {}
            php_analysis = {}
            context_parts = []

            if 'Python' in languages_detected:
                python_analysis = analyze_python_project(project_path)
                analysis.update({k: {'language': 'Python', **v} for k, v in python_analysis.items()})
                classes = [c for data in python_analysis.values() for c in data["classes"]]
                functions = [f for data in python_analysis.values() for f in data["functions"]]
                methods = [m for data in python_analysis.values() for m in data["methods"]]
                imports = [i for data in python_analysis.values() for i in data["imports"]]
                global_vars = [g for data in python_analysis.values() for g in data["global_vars"]]
                context_parts.append(
                    f"Python code with {len(classes)} classes ({', '.join(classes) if classes else 'none'}), "
                    f"{len(functions)} functions ({', '.join(functions) if functions else 'none'}), "
                    f"{len(methods)} methods ({', '.join(methods) if methods else 'none'}), "
                    f"{len(global_vars)} global variables ({', '.join(global_vars) if global_vars else 'none'}), "
                    f"and {len(imports)} imported modules ({', '.join(imports) if imports else 'none'})."
                )

            if 'Java' in languages_detected:
                java_analysis = analyze_java_project(project_path)
                analysis.update({k: {'language': 'Java', **v} for k, v in java_analysis.items()})
                classes = [c for v in java_analysis.values() for c in v["classes"]]
                methods = [m for v in java_analysis.values() for m in v["methods"]]
                imports = [i for v in java_analysis.values() for i in v["imports"]]
                superclasses = [sc for v in java_analysis.values() for sc in v["superclass"]]
                interfaces = [iface for v in java_analysis.values() for iface in v["interfaces"]]
                context_parts.append(
                    f"Java code with {len(classes)} classes ({', '.join(classes) if classes else 'none'}), "
                    f"{len(methods)} methods ({', '.join(methods) if methods else 'none'}), "
                    f"{len(imports)} imported packages ({', '.join(imports) if imports else 'none'}), "
                    f"superclasses ({', '.join(superclasses) if superclasses else 'none'}), "
                    f"and interfaces ({', '.join(interfaces) if interfaces else 'none'})."
                )

            if 'JavaScript' in languages_detected:
                javascript_analysis = analyze_javascript_project(project_path)
                analysis.update({k: {'language': 'JavaScript', **v} for k, v in javascript_analysis.items()})
                classes = [c for data in javascript_analysis.values() for c in data["classes"]]
                functions = [f for data in javascript_analysis.values() for f in data["functions"]]
                methods = [m for data in javascript_analysis.values() for m in data["methods"]]
                imports = [i for data in javascript_analysis.values() for i in data["imports"]]
                global_vars = [g for data in javascript_analysis.values() for g in data["global_vars"]]
                context_parts.append(
                    f"JavaScript code with {len(classes)} classes ({', '.join(classes) if classes else 'none'}), "
                    f"{len(functions)} functions ({', '.join(functions) if functions else 'none'}), "
                    f"{len(methods)} methods ({', '.join(methods) if methods else 'none'}), "
                    f"{len(global_vars)} global variables ({', '.join(global_vars) if global_vars else 'none'}), "
                    f"and {len(imports)} imported modules ({', '.join(imports) if imports else 'none'})."
                )

            if 'C' in languages_detected:
                c_analysis = analyze_c_project(project_path)
                analysis.update({k: {'language': 'C', **v} for k, v in c_analysis.items()})
                structs = [s for data in c_analysis.values() for s in data["structs"]]
                functions = [f for data in c_analysis.values() for f in data["functions"]]
                includes = [i for data in c_analysis.values() for i in data["includes"]]
                global_vars = [g for data in c_analysis.values() for g in data["global_vars"]]
                context_parts.append(
                    f"C code with {len(structs)} structs ({', '.join(structs) if structs else 'none'}), "
                    f"{len(functions)} functions ({', '.join(functions) if functions else 'none'}), "
                    f"{len(global_vars)} global variables ({', '.join(global_vars) if global_vars else 'none'}), "
                    f"and {len(includes)} included files ({', '.join(includes) if includes else 'none'})."
                )

            if 'PHP' in languages_detected:
                php_analysis = analyze_php_project(project_path)
                analysis.update({k: {'language': 'PHP', **v} for k, v in php_analysis.items()})
                classes = [c for data in php_analysis.values() for c in data["classes"]]
                functions = [f for data in php_analysis.values() for f in data["functions"]]
                methods = [m for data in php_analysis.values() for m in data["methods"]]
                uses = [u for data in php_analysis.values() for u in data["uses"]]
                parent_classes = [pc for data in php_analysis.values() for pc in data["parent_classes"]]
                interfaces = [iface for data in php_analysis.values() for iface in data["interfaces"]]
                traits = [trait for data in php_analysis.values() for trait in data["traits"]]
                context_parts.append(
                    f"PHP code with {len(classes)} classes ({', '.join(classes) if classes else 'none'}), "
                    f"{len(functions)} functions ({', '.join(functions) if functions else 'none'}), "
                    f"{len(methods)} methods ({', '.join(methods) if methods else 'none'}), "
                    f"{len(uses)} imported namespaces ({', '.join(uses) if uses else 'none'}), "
                    f"parent classes ({', '.join(parent_classes) if parent_classes else 'none'}), "
                    f"interfaces ({', '.join(interfaces) if interfaces else 'none'}), "
                    f"and traits ({', '.join(traits) if traits else 'none'})."
                )

            context = "Project contains: " + " ".join(context_parts) + " This is a multi-language project with the uploaded code structure."

            # Handle class/struct queries
            class_count_match = re.search(r'\b(how\s+many|count|number\s+of)\b.*\b(class|classes|struct|structs)\b', q)
            class_list_match = re.search(r'\b(name|list|show|what|which|all)\b.*\b(class|classes|struct|structs)\b',
                                         q) or q in ["classes", "structs"] or "name them" in q or "present in project" in q
            if class_count_match or class_list_match:
                python_classes = [c for data in python_analysis.values() for c in data.get("classes", [])]
                java_classes = [c for data in java_analysis.values() for c in data.get("classes", [])]
                js_classes = [c for data in javascript_analysis.values() for c in data.get("classes", [])]
                c_structs = [s for data in c_analysis.values() for s in data.get("structs", [])]
                php_classes = [c for data in php_analysis.values() for c in data.get("classes", [])]
                all_structures = (
                    [f"Python: {c}" for c in python_classes] +
                    [f"Java: {c}" for c in java_classes] +
                    [f"JavaScript: {c}" for c in js_classes] +
                    [f"C: {s}" for s in c_structs] +
                    [f"PHP: {c}" for c in php_classes]
                )
                count = len(all_structures)
                if class_count_match:
                    st.write(f"Total classes/structs: {count}")
                if class_list_match and all_structures:
                    st.write("Classes/Structs:\n" + "\n".join(all_structures))
                elif class_list_match:
                    st.write("No classes or structs found.")
            # Handle superclass/parent class queries (Java and PHP)
            elif re.search(r'\b(how\s+many|count|number\s+of)\b.*\b(superclass|superclasses|parent\s+class|parent\s+classes)\b', q):
                if 'Java' in languages_detected or 'PHP' in languages_detected:
                    java_superclasses = [sc for data in java_analysis.values() for sc in data.get("superclass", [])]
                    php_parent_classes = [pc for data in php_analysis.values() for pc in data.get("parent_classes", [])]
                    count = len([sc for sc in java_superclasses if "has no superclass" not in sc]) + \
                            len([pc for pc in php_parent_classes if "has no parent class" not in pc])
                    st.write(f"Total superclasses/parent classes (Java/PHP): {count}")
                else:
                    st.write("Superclass/parent class queries are only supported for Java and PHP code, which were not detected.")
            elif re.search(r'\b(name|list|show|what|which|all)\b.*\b(superclass|superclasses|parent\s+class|parent\s+classes)\b', q) or q in ["superclasses", "parent classes"]:
                if 'Java' in languages_detected or 'PHP' in languages_detected:
                    java_superclasses = [sc for data in java_analysis.values() for sc in data.get("superclass", [])]
                    php_parent_classes = [pc for data in php_analysis.values() for pc in data.get("parent_classes", [])]
                    all_parents = [sc for sc in java_superclasses if "has no superclass" not in sc] + \
                                  [pc for pc in php_parent_classes if "has no parent class" not in pc]
                    if all_parents:
                        st.write("Superclasses/Parent Classes (Java/PHP):\n" + "\n".join(all_parents))
                    else:
                        st.write("No superclasses or parent classes found.")
                else:
                    st.write("Superclass/parent class queries are only supported for Java and PHP code, which were not detected.")
            # Handle interface queries (Java and PHP)
            elif re.search(r'\b(how\s+many|count|number\s+of)\b.*\b(interface|interfaces)\b', q):
                if 'Java' in languages_detected or 'PHP' in languages_detected:
                    java_interfaces = [iface for data in java_analysis.values() for iface in data.get("interfaces", [])]
                    php_interfaces = [iface for data in php_analysis.values() for iface in data.get("interfaces", [])]
                    count = len([iface for iface in java_interfaces if "implements no interfaces" not in iface]) + \
                            len([iface for iface in php_interfaces if "implements no interfaces" not in iface])
                    st.write(f"Total interfaces (Java/PHP): {count}")
                else:
                    st.write("Interface queries are only supported for Java and PHP code, which were not detected.")
            elif re.search(r'\b(name|list|show|what|which|all)\b.*\b(interface|interfaces)\b', q) or q == "interfaces":
                if 'Java' in languages_detected or 'PHP' in languages_detected:
                    java_interfaces = [iface for data in java_analysis.values() for iface in data.get("interfaces", [])]
                    php_interfaces = [iface for data in php_analysis.values() for iface in data.get("interfaces", [])]
                    all_interfaces = [iface for iface in java_interfaces if "implements no interfaces" not in iface] + \
                                     [iface for iface in php_interfaces if "implements no interfaces" not in iface]
                    if all_interfaces:
                        st.write("Interfaces (Java/PHP):\n" + "\n".join(all_interfaces))
                    else:
                        st.write("No interfaces found.")
                else:
                    st.write("Interface queries are only supported for Java and PHP code, which were not detected.")
            # Handle trait queries (PHP only)
            elif re.search(r'\b(how\s+many|count|number\s+of)\b.*\b(trait|traits)\b', q):
                if 'PHP' in languages_detected:
                    traits = [trait for data in php_analysis.values() for trait in data.get("traits", [])]
                    count = len([trait for trait in traits if "uses no traits" not in trait])
                    st.write(f"Total traits (PHP): {count}")
                else:
                    st.write("Trait queries are only supported for PHP code, which was not detected.")
            elif re.search(r'\b(name|list|show|what|which|all)\b.*\b(trait|traits)\b', q) or q == "traits":
                if 'PHP' in languages_detected:
                    traits = [trait for data in php_analysis.values() for trait in data.get("traits", [])]
                    if traits:
                        st.write("Traits (PHP):\n" + "\n".join([trait for trait in traits if "uses no traits" not in trait]))
                    else:
                        st.write("No traits found.")
                else:
                    st.write("Trait queries are only supported for PHP code, which was not detected.")
            # Handle library/module/include/use queries
            elif re.search(r'\b(how\s+many|count|number\s+of)\b.*\b(librar(y|ies)|module|modules|package|packages|include|includes|use|uses)\b', q):
                imports = (
                    [i for data in python_analysis.values() for i in data.get("imports", [])] +
                    [i for data in java_analysis.values() for i in data.get("imports", [])] +
                    [i for data in javascript_analysis.values() for i in data.get("imports", [])] +
                    [i for data in c_analysis.values() for i in data.get("includes", [])] +
                    [u for data in php_analysis.values() for u in data.get("uses", [])]
                )
                unique_imports = sorted(set(imports))
                st.write(f"Total modules/packages/includes/uses: {len(unique_imports)}")
            elif re.search(r'\b(name|list|show|what|which|all)\b.*\b(librar(y|ies)|module|modules|package|packages|include|includes|use|uses)\b', q) or "name them" in q:
                imports = (
                    [f"Python: {i}" for data in python_analysis.values() for i in data.get("imports", [])] +
                    [f"Java: {i}" for data in java_analysis.values() for i in data.get("imports", [])] +
                    [f"JavaScript: {i}" for data in javascript_analysis.values() for i in data.get("imports", [])] +
                    [f"C: {i}" for data in c_analysis.values() for i in data.get("includes", [])] +
                    [f"PHP: {u}" for data in php_analysis.values() for u in data.get("uses", [])]
                )
                unique_imports = sorted(set(imports))
                if unique_imports:
                    st.write("Modules/Packages/Includes/Uses:\n" + "\n".join(unique_imports))
                else:
                    st.write("No modules, packages, includes, or uses found.")
            # Handle methods/functions
            elif re.search(r'\b(how\s+many|count|number\s+of)\b.*\b(function|functions|method|methods)\b', q):
                function_count = (
                    sum(len(data["functions"]) for data in python_analysis.values()) +
                    sum(len(data["functions"]) for data in javascript_analysis.values()) +
                    sum(len(data["functions"]) for data in c_analysis.values()) +
                    sum(len(data["functions"]) for data in php_analysis.values())
                )
                method_count = (
                    sum(len(data["methods"]) for data in python_analysis.values()) +
                    sum(len(data["methods"]) for data in java_analysis.values()) +
                    sum(len(data["methods"]) for data in javascript_analysis.values()) +
                    sum(len(data["methods"]) for data in php_analysis.values())
                )
                if function_count > 0:
                    st.write(f"Total functions (Python/JavaScript/C/PHP): {function_count}")
                if method_count > 0:
                    st.write(f"Total methods (Python/Java/JavaScript/PHP): {method_count}")
                if function_count == 0 and method_count == 0:
                    st.write("No functions or methods found.")
            elif re.search(r'\b(name|list|show|what|which|all)?\b.*\b(function|functions|method|methods)\b', q) or q in ["methods", "functions"]:
                functions = (
                    [f"Python: {f}" for data in python_analysis.values() for f in data.get("functions", [])] +
                    [f"JavaScript: {f}" for data in javascript_analysis.values() for f in data.get("functions", [])] +
                    [f"C: {f}" for data in c_analysis.values() for f in data.get("functions", [])] +
                    [f"PHP: {f}" for data in php_analysis.values() for f in data.get("functions", [])]
                )
                methods = (
                    [f"Python: {m}" for data in python_analysis.values() for m in data.get("methods", [])] +
                    [f"Java: {m}" for data in java_analysis.values() for m in data.get("methods", [])] +
                    [f"JavaScript: {m}" for data in javascript_analysis.values() for m in data.get("methods", [])] +
                    [f"PHP: {m}" for data in php_analysis.values() for m in data.get("methods", [])]
                )
                if functions or methods:
                    if functions:
                        st.write(f"Total functions: {len(functions)}")
                        st.write("Functions:\n" + ", ".join(functions))
                    if methods:
                        st.write(f"Total methods: {len(methods)}")
                        st.write("Methods:\n" + ", ".join(methods))
                else:
                    st.write("No functions or methods found.")
            # Handle global variables (Python, JavaScript, and C)
            elif re.search(r'\b(how\s+many|count|number\s+of)\b.*\b(global|globals|global\s+variables)\b', q):
                global_vars = (
                    [g for data in python_analysis.values() for g in data.get("global_vars", [])] +
                    [g for data in javascript_analysis.values() for g in data.get("global_vars", [])] +
                    [g for data in c_analysis.values() for g in data.get("global_vars", [])]
                )
                st.write(f"Total global variables (Python/JavaScript/C): {len(global_vars)}")
            elif re.search(r'\b(name|list|show|what|which|all)\b.*\b(global|globals|global\s+variables)\b', q) or q == "global variables":
                global_vars = (
                    [f"Python: {g}" for data in python_analysis.values() for g in data.get("global_vars", [])] +
                    [f"JavaScript: {g}" for data in javascript_analysis.values() for g in data.get("global_vars", [])] +
                    [f"C: {g}" for data in c_analysis.values() for g in data.get("global_vars", [])]
                )
                if global_vars:
                    st.write("Global Variables:\n" + "\n".join(global_vars))
                else:
                    st.write("No global variables found.")
            # Handle explanation queries
            elif re.search(r'\b(explain|describe|what|about|summary)\b.*\b(code|project|it|does|functionality|purpose)?\b', q) or q in ["explain", "what code describes", "describe code"]:
                purpose_parts = []
                base_explanations = []
                if 'Python' in languages_detected:
                    base_explanations.append(explain_python_code(project_path))
                    purpose_parts.append("The Python portion is a code analysis tool that parses Python source files to extract structural elements like classes, functions, methods, and global variables using the `ast` module.")
                if 'Java' in languages_detected:
                    base_explanations.append(explain_java_code(project_path))
                    purpose_parts.append("The Java portion is designed to manage its specific functionality based on the uploaded code.")
                if 'JavaScript' in languages_detected:
                    base_explanations.append(explain_javascript_code(project_path))
                    purpose_parts.append("The JavaScript portion is designed to manage its specific functionality based on the uploaded code.")
                if 'C' in languages_detected:
                    base_explanations.append(explain_c_code(project_path))
                    purpose_parts.append("The C portion is designed to manage its specific functionality based on the uploaded code.")
                if 'PHP' in languages_detected:
                    base_explanations.append(explain_php_code(project_path))
                    purpose_parts.append("The PHP portion is designed to manage its specific functionality based on the uploaded code.")
                purpose = " ".join(purpose_parts)
                base_explanation = "\n".join(base_explanations)
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
                prompt = f"{context}\n\nQuery: {query} [Unique ID: {uuid.uuid4()}]\n\nAnswer the query based on the project context. If it’s about code structure, summarize classes, structs, methods, functions, superclasses, interfaces, traits, includes, or imports. If it’s unclear, ask for clarification."
                response = query_ollama(prompt)
                st.write(f"Ollama Response: {response}")
else:
    st.info("Please upload a ZIP file containing your project.")