from tree_sitter_languages import get_language, get_parser
import os

# Initialize the C language and parser
C_LANGUAGE = get_language('c')
parser = get_parser('c')

def analyze_c_project(project_path):
    """Analyze a C project and return a dictionary with structs, functions, includes, and global variables."""
    analysis = {}
    for root, _, files in os.walk(project_path):
        for file in files:
            if file.endswith(('.c', '.h')):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                tree = parser.parse(bytes(code, 'utf-8'))
                analysis[file_path] = {
                    'structs': [],
                    'functions': [],
                    'includes': [],
                    'global_vars': []
                }
                root_node = tree.root_node
                # Extract includes
                for node in root_node.children:
                    if node.type == 'preproc_include':
                        include_name_node = node.child_by_field_name('path')
                        if include_name_node:
                            include_name = code[include_name_node.start_byte:include_name_node.end_byte].strip("'\"<>")
                            if include_name not in analysis[file_path]['includes']:
                                analysis[file_path]['includes'].append(include_name)
                # Extract structs, functions, and global variables
                def traverse(node):
                    if node.type in ('struct_specifier', 'union_specifier'):
                        name_node = node.child_by_field_name('name')
                        if name_node:
                            struct_name = code[name_node.start_byte:name_node.end_byte]
                            analysis[file_path]['structs'].append(struct_name)
                    elif node.type == 'function_definition':
                        declarator_node = node.child_by_field_name('declarator')
                        if declarator_node:
                            func_name_node = declarator_node.child_by_field_name('declarator')
                            if func_name_node and func_name_node.type == 'identifier':
                                func_name = code[func_name_node.start_byte:func_name_node.end_byte]
                                analysis[file_path]['functions'].append(func_name)
                    elif node.type == 'declaration' and node.parent.type == 'translation_unit':
                        declarator_node = node.child_by_field_name('declarator')
                        if declarator_node and declarator_node.type == 'init_declarator':
                            var_name_node = declarator_node.child_by_field_name('declarator')
                            if var_name_node and var_name_node.type == 'identifier':
                                var_name = code[var_name_node.start_byte:var_name_node.end_byte]
                                analysis[file_path]['global_vars'].append(var_name)
                    for child in node.children:
                        traverse(child)
                traverse(root_node)
    return analysis

def explain_c_code(project_path):
    """Generate a summary of the C project structure based on the current analysis."""
    analysis = analyze_c_project(project_path)
    total_structs = sum(len(data['structs']) for data in analysis.values())
    total_functions = sum(len(data['functions']) for data in analysis.values())
    total_includes = set(inc for data in analysis.values() for inc in data['includes'])
    total_globals = sum(len(data['global_vars']) for data in analysis.values())
    summary = (
        f"C project with {total_structs} structs, {total_functions} functions.\n"
        f"Included files: {', '.join(total_includes) if total_includes else 'none'}.\n"
        f"Global variables: {total_globals} ({', '.join([g for data in analysis.values() for g in data['global_vars']]) if total_globals else 'none'}).\n"
        f"This project’s purpose is based on the uploaded C code structure."
    )
    return summary