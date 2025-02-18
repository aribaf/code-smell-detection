import os
import ast
import json

# Define thresholds for code smells (LLF, LSC, LPL, LMC)
THRESHOLDS = {
    'LPL': 5,    # Long Parameter List threshold
    'LSC': 3,    # Long Scope Chaining threshold
    'LLF': 48,   # Long Lambda Function threshold in characters
    'LMC': 5,    # Long Message Chain threshold
    'LBCL': 3,   # Long Base Class List threshold
}

def add_smell(smells, name, lineno, details, file_path):
    """Add a code smell to the list."""
    smells.append({
        "file": file_path,
        "code_smell": name,
        "line_number": lineno,
        "details": details
    })

def count_nested_levels(node):
    """Count nested levels for Long Scope Chaining (LSC)."""
    max_depth = 1
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.If, ast.While, ast.For)):
            max_depth = max(max_depth, 1 + count_nested_levels(child))
    return max_depth

def count_message_chain_length(node):
    """Count the length of the message chain for Long Message Chain (LMC)."""
    length = 0
    while isinstance(node, ast.Attribute):
        length += 1
        node = node.value
    return length

def analyze_file(file_path, smells):
    """Analyze a Python file for code smells."""
    try:
        with open(file_path, 'r') as file:
            tree = ast.parse(file.read(), filename=file_path)

        for node in ast.walk(tree):
            # Long Parameter List (LPL)
            if isinstance(node, ast.FunctionDef):
                if len(node.args.args) > THRESHOLDS['LPL']:
                    add_smell(smells, "Long Parameter List (LPL)", node.lineno, f"Parameters: {len(node.args.args)}", file_path)

                # Long Scope Chaining (LSC)
                if any(isinstance(stmt, (ast.If, ast.While, ast.For)) and count_nested_levels(stmt) > THRESHOLDS['LSC'] for stmt in node.body):
                    add_smell(smells, "Long Scope Chaining (LSC)", node.lineno, f"Nested Levels > {THRESHOLDS['LSC']}", file_path)

                # Long Lambda Function (LLF)
                for expr in ast.walk(node):
                    if isinstance(expr, ast.Lambda):
                        lambda_length = len(ast.dump(expr))
                        if lambda_length > THRESHOLDS['LLF']:
                            add_smell(smells, "Long Lambda Function (LLF)", expr.lineno, f"Length: {lambda_length}", file_path)

            # Long Base Class List (LBCL)
            if isinstance(node, ast.ClassDef):
                # Correctly check for the number of base classes
                base_class_count = len(node.bases)
                if base_class_count > THRESHOLDS['LBCL']:
                    add_smell(smells, "Long Base Class List (LBCL)", node.lineno, f"Bases: {base_class_count}", file_path)

            # Long Message Chain (LMC)
            if isinstance(node, ast.Attribute):
                chain_length = count_message_chain_length(node)
                if chain_length > THRESHOLDS['LMC']:
                    add_smell(smells, "Long Message Chain (LMC)", node.lineno, f"Chain Length: {chain_length}", file_path)

    except SyntaxError as e:
        print(f"Skipping file {file_path} due to syntax error: {e}")
    except Exception as e:
        print(f"Error analyzing file {file_path}: {e}")


def detect_code_smells_in_file(file_path, report_path):
    smells = []
    print(f"Scanning file: {file_path}")
    print(f"Saving report to: {report_path}")
    
    # Directly analyze the file without traversing directories
    analyze_file(file_path, smells)

    # Save the comined  report to a JSON file
    try:
        with open(report_path, 'w') as report_file:
            print(smells)
            json.dump(smells, report_file, indent=4)
        print(f"Code smells report saved to {report_path}")
    except Exception as e:
        print(f"Error saving report to {report_path}: {e}")

# Test the code smell detector
if __name__ == "__main__":
    detect_code_smells_in_file("path_to_your_file.py", "code_smell_report.json")
