from tree_sitter_languages import get_language, get_parser
import os

# Initialize the Java language and parser
JAVA_LANGUAGE = get_language('java')
parser = get_parser('java')

def analyze_java_project(project_path):
    """Analyze a Java project and return a dictionary with classes, superclasses, interfaces, methods, and imports."""
    analysis = {}
    for root, _, files in os.walk(project_path):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                tree = parser.parse(bytes(code, 'utf-8'))
                analysis[file_path] = {
                    'classes': [],
                    'superclass': [],  # Store superclass for each class
                    'interfaces': [],  # Store interfaces implemented by each class
                    'methods': [],
                    'imports': []
                }
                root_node = tree.root_node
                # Extract imports
                for node in root_node.children:
                    if node.type == 'import_declaration':
                        import_text = code[node.start_byte:node.end_byte].strip()
                        package = import_text.replace('import ', '').replace(';', '').strip()
                        if package not in analysis[file_path]['imports']:
                            analysis[file_path]['imports'].append(package)
                # Extract classes, superclasses, interfaces, and methods
                def traverse(node):
                    if node.type == 'class_declaration':
                        class_name_node = node.child_by_field_name('name')
                        if class_name_node:
                            class_name = code[class_name_node.start_byte:class_name_node.end_byte]
                            analysis[file_path]['classes'].append(class_name)
                            # Extract superclass (extends)
                            superclass_node = node.child_by_field_name('superclass')
                            if superclass_node:
                                superclass_name = code[superclass_node.start_byte:superclass_node.end_byte]
                                analysis[file_path]['superclass'].append(f"{class_name} extends {superclass_name}")
                            else:
                                analysis[file_path]['superclass'].append(f"{class_name} has no superclass")
                            # Extract interfaces (implements)
                            interfaces_node = node.child_by_field_name('interfaces')
                            interfaces = []
                            if interfaces_node:
                                for child in interfaces_node.children:
                                    if child.type == 'type_identifier' or child.type == 'generic_type':
                                        interface_name = code[child.start_byte:child.end_byte]
                                        interfaces.append(interface_name)
                                if interfaces:
                                    analysis[file_path]['interfaces'].append(f"{class_name} implements {', '.join(interfaces)}")
                                else:
                                    analysis[file_path]['interfaces'].append(f"{class_name} implements no interfaces")
                            else:
                                analysis[file_path]['interfaces'].append(f"{class_name} implements no interfaces")
                    elif node.type == 'method_declaration':
                        method_name_node = node.child_by_field_name('name')
                        if method_name_node:
                            method_name = code[method_name_node.start_byte:method_name_node.end_byte]
                            analysis[file_path]['methods'].append(method_name)
                    for child in node.children:
                        traverse(child)
                traverse(root_node)
    return analysis

def explain_java_code(project_path):
    """Generate a summary of the Java project structure based on the current analysis."""
    analysis = analyze_java_project(project_path)
    total_classes = sum(len(data['classes']) for data in analysis.values())
    total_methods = sum(len(data['methods']) for data in analysis.values())
    total_imports = set(pkg for data in analysis.values() for pkg in data['imports'])
    superclasses = [sc for data in analysis.values() for sc in data['superclass']]
    interfaces = [iface for data in analysis.values() for iface in data['interfaces']]
    summary = (
        f"Java project with {total_classes} classes, {total_methods} methods.\n"
        f"Imported packages: {', '.join(total_imports) if total_imports else 'none'}.\n"
        f"Superclasses: {', '.join(superclasses) if superclasses else 'none'}.\n"
        f"Interfaces: {', '.join(interfaces) if interfaces else 'none'}.\n"
        f"This project’s purpose is based on the uploaded Java code structure."
    )
    return summary