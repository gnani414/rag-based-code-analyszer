from tree_sitter_languages import get_language, get_parser
import os

# Initialize the PHP language and parser
PHP_LANGUAGE = get_language('php')
parser = get_parser('php')

def analyze_php_project(project_path):
    """Analyze a PHP project and return a dictionary with classes, parent classes, interfaces, traits, methods, functions, and use statements."""
    analysis = {}
    for root, _, files in os.walk(project_path):
        for file in files:
            if file.endswith('.php'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                tree = parser.parse(bytes(code, 'utf-8'))
                analysis[file_path] = {
                    'classes': [],
                    'parent_classes': [],  # Store parent class for each class (extends)
                    'interfaces': [],      # Store interfaces implemented by each class
                    'traits': [],          # Store traits used by each class
                    'methods': [],
                    'functions': [],
                    'uses': []             # Store use statements (imports)
                }
                root_node = tree.root_node
                # Extract use statements
                for node in root_node.children:
                    if node.type == 'use_declaration':
                        for child in node.children:
                            if child.type == 'name':
                                use_name = code[child.start_byte:child.end_byte].strip()
                                if use_name not in analysis[file_path]['uses']:
                                    analysis[file_path]['uses'].append(use_name)
                # Extract classes, parent classes, interfaces, traits, methods, and functions
                def traverse(node):
                    if node.type == 'class_declaration':
                        class_name_node = node.child_by_field_name('name')
                        if class_name_node:
                            class_name = code[class_name_node.start_byte:class_name_node.end_byte]
                            analysis[file_path]['classes'].append(class_name)
                            # Extract parent class (extends)
                            parent_class_node = node.child_by_field_name('base_clause')
                            if parent_class_node:
                                for child in parent_class_node.children:
                                    if child.type == 'name':
                                        parent_name = code[child.start_byte:child.end_byte]
                                        analysis[file_path]['parent_classes'].append(f"{class_name} extends {parent_name}")
                                        break
                            else:
                                analysis[file_path]['parent_classes'].append(f"{class_name} has no parent class")
                            # Extract interfaces (implements)
                            interfaces_node = node.child_by_field_name('class_interface_clause')
                            interfaces = []
                            if interfaces_node:
                                for child in interfaces_node.children:
                                    if child.type == 'name':
                                        interface_name = code[child.start_byte:child.end_byte]
                                        interfaces.append(interface_name)
                                if interfaces:
                                    analysis[file_path]['interfaces'].append(f"{class_name} implements {', '.join(interfaces)}")
                                else:
                                    analysis[file_path]['interfaces'].append(f"{class_name} implements no interfaces")
                            else:
                                analysis[file_path]['interfaces'].append(f"{class_name} implements no interfaces")
                            # Extract traits (use statements within class body)
                            body_node = node.child_by_field_name('body')
                            traits = []
                            if body_node:
                                for child in body_node.children:
                                    if child.type == 'trait_use_clause':
                                        for grand_child in child.children:
                                            if grand_child.type == 'name':
                                                trait_name = code[grand_child.start_byte:grand_child.end_byte]
                                                traits.append(trait_name)
                                        if traits:
                                            analysis[file_path]['traits'].append(f"{class_name} uses {', '.join(traits)}")
                                if not traits:
                                    analysis[file_path]['traits'].append(f"{class_name} uses no traits")
                            else:
                                analysis[file_path]['traits'].append(f"{class_name} uses no traits")
                    elif node.type == 'method_declaration':
                        method_name_node = node.child_by_field_name('name')
                        if method_name_node:
                            method_name = code[method_name_node.start_byte:method_name_node.end_byte]
                            analysis[file_path]['methods'].append(method_name)
                    elif node.type == 'function_declaration':
                        func_name_node = node.child_by_field_name('name')
                        if func_name_node:
                            func_name = code[func_name_node.start_byte:func_name_node.end_byte]
                            analysis[file_path]['functions'].append(func_name)
                    for child in node.children:
                        traverse(child)
                traverse(root_node)
    return analysis

def explain_php_code(project_path):
    """Generate a summary of the PHP project structure based on the current analysis."""
    analysis = analyze_php_project(project_path)
    total_classes = sum(len(data['classes']) for data in analysis.values())
    total_methods = sum(len(data['methods']) for data in analysis.values())
    total_functions = sum(len(data['functions']) for data in analysis.values())
    total_uses = set(use for data in analysis.values() for use in data['uses'])
    parent_classes = [pc for data in analysis.values() for pc in data['parent_classes']]
    interfaces = [iface for data in analysis.values() for iface in data['interfaces']]
    traits = [trait for data in analysis.values() for trait in data['traits']]
    summary = (
        f"PHP project with {total_classes} classes, {total_functions} functions, "
        f"{total_methods} methods.\n"
        f"Imported namespaces/classes: {', '.join(total_uses) if total_uses else 'none'}.\n"
        f"Parent classes: {', '.join(parent_classes) if parent_classes else 'none'}.\n"
        f"Interfaces: {', '.join(interfaces) if interfaces else 'none'}.\n"
        f"Traits: {', '.join(traits) if traits else 'none'}.\n"
        f"This project’s purpose is based on the uploaded PHP code structure."
    )
    return summary