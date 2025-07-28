import ast
import os

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.classes = []
        self.functions = []
        self.methods = []
        self.global_vars = []
        self.imports = []

    def visit_ClassDef(self, node):
        self.classes.append(node.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if isinstance(node.parent, ast.ClassDef):
            self.methods.append(node.name)
        else:
            self.functions.append(node.name)
        self.generic_visit(node)

    def visit_Assign(self, node):
        if isinstance(node.parent, ast.Module):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.global_vars.append(target.id)
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.imports.append(f"{node.module}.{alias.name}" if node.module else alias.name)
        self.generic_visit(node)

def analyze_python_project(project_path):
    """Analyze a Python project and return a dictionary with extracted elements."""
    analysis = {}
    analyzer = CodeAnalyzer()

    for root, _, files in os.walk(project_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                try:
                    tree = ast.parse(code)
                    # Add parent references
                    for node in ast.walk(tree):
                        for child in ast.iter_child_nodes(node):
                            child.parent = node
                    analyzer.visit(tree)
                    analysis[file_path] = {
                        'classes': analyzer.classes,
                        'functions': analyzer.functions,
                        'methods': analyzer.methods,
                        'global_vars': analyzer.global_vars,
                        'imports': analyzer.imports
                    }
                    # Reset analyzer for next file
                    analyzer = CodeAnalyzer()
                except SyntaxError:
                    analysis[file_path] = {
                        'classes': [],
                        'functions': [],
                        'methods': [],
                        'global_vars': [],
                        'imports': []
                    }
    return analysis

def explain_python_code(project_path):
    """Generate a summary of the Python project structure."""
    analysis = analyze_python_project(project_path)
    total_classes = sum(len(data['classes']) for data in analysis.values())
    total_functions = sum(len(data['functions']) for data in analysis.values())
    total_methods = sum(len(data['methods']) for data in analysis.values())
    total_globals = sum(len(data['global_vars']) for data in analysis.values())
    total_imports = set(imp for data in analysis.values() for imp in data['imports'])
    summary = (
        f"Python project with {total_classes} classes, {total_functions} functions, "
        f"{total_methods} methods, and {total_globals} global variables.\n"
        f"Imported modules: {', '.join(total_imports) if total_imports else 'none'}.\n"
        f"The project is a code analysis tool using the `ast` module to parse Python source files."
    )
    return summary