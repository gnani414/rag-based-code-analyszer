from tree_sitter_languages import get_language, get_parser
import os

# Initialize the JavaScript language and parser
JAVASCRIPT_LANGUAGE = get_language('javascript')
parser = get_parser('javascript')

def analyze_javascript_project(project_path):
    """Analyze a JavaScript project and return a dictionary with classes, functions, methods, imports, and global variables."""
    analysis = {}
    for root, _, files in os.walk(project_path):
        for file in files:
            if file.endswith('.js'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                tree = parser.parse(bytes(code, 'utf-8'))
                analysis[file_path] = {
                    'classes': [],
                    'functions': [],
                    'methods': [],
                    'imports': [],
                    'global_vars': []
                }
                root_node = tree.root_node
                # Extract imports (both ES6 import and CommonJS require)
                for node in root_node.children:
                    if node.type == 'import_statement':
                        import_text = code[node.start_byte:node.end_byte].strip()
                        import_clause = node.child_by_field_name('source')
                        if import_clause:
                            module_name = code[import_clause.start_byte:import_clause.end_byte].strip("'\"")
                            analysis[file_path]['imports'].append(module_name)
                    elif node.type == 'variable_declarator':
                        call_expression = node.child_by_field_name('value')
                        if call_expression and call_expression.type == 'call_expression':
                            callee = call_expression.child_by_field_name('function')
                            if callee and code[callee.start_byte:callee.end_byte] == 'require':
                                args = call_expression.child_by_field_name('arguments')
                                if args and args.child_count > 0:
                                    module_name = code[args.children[0].start_byte:args.children[0].end_byte].strip("'\"")
                                    analysis[file_path]['imports'].append(module_name)
                    # Extract global variables
                    elif node.type == 'variable_declaration' and node.parent.type == 'program':
                        for declarator in node.children:
                            if declarator.type == 'variable_declarator':
                                name_node = declarator.child_by_field_name('name')
                                if name_node and name_node.type == 'identifier':
                                    var_name = code[name_node.start_byte:name_node.end_byte]
                                    analysis[file_path]['global_vars'].append(var_name)
                # Extract classes, functions, and methods
                def traverse(node):
                    if node.type == 'class_declaration':
                        class_name_node = node.child_by_field_name('name')
                        if class_name_node:
                            class_name = code[class_name_node.start_byte:class_name_node.end_byte]
                            analysis[file_path]['classes'].append(class_name)
                            body_node = node.child_by_field_name('body')
                            if body_node:
                                for child in body_node.children:
                                    if child.type in ('method_definition', 'public_field_definition'):
                                        method_name_node = child.child_by_field_name('name')
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

def explain_javascript_code(project_path):
    """Generate a summary of the JavaScript project structure based on the current analysis."""
    analysis = analyze_javascript_project(project_path)
    total_classes = sum(len(data['classes']) for data in analysis.values())
    total_functions = sum(len(data['functions']) for data in analysis.values())
    total_methods = sum(len(data['methods']) for data in analysis.values())
    total_imports = set(imp for data in analysis.values() for imp in data['imports'])
    total_globals = sum(len(data['global_vars']) for data in analysis.values())
    summary = (
        f"JavaScript project with {total_classes} classes, {total_functions} functions, "
        f"{total_methods} methods, {total_globals} global variables, "
        f"and {len(total_imports)} imported modules.\n"
        f"Imported modules: {', '.join(total_imports) if total_imports else 'none'}.\n"
        f"This project is a JavaScript application based on the uploaded code structure."
    )
    return summary