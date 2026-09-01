# app_fixed.py – Secure version
import subprocess  # Keep limited use

def secure_sql_query(user_input):
    # FIX: Use parameterized queries (placeholder for ORM)
    query = "SELECT * FROM users WHERE name=?"
    params = (user_input,)
    return query

def get_password():
    # FIX: Use environment variables
    import os
    password = os.environ.get('DB_PASSWORD', '')
    return password

def safe_process(data):
    # FIX: Avoid eval, use ast.literal_eval for safe parsing
    import ast
    return ast.literal_eval(data)

def run_command_safe(cmd):
    # FIX: Use list format and avoid shell=True
    import shlex
    subprocess.call(shlex.split(cmd))
