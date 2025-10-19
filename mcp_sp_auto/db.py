import os, pyodbc
from dotenv import load_dotenv
load_dotenv()

def get_conn():
    server = os.getenv("DB_SERVER")
    db = os.getenv("DB_NAME")
    cn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={db};"
        f"Trusted_Connection=yes;"
        f"TrustServerCertificate=yes"
    )
    return cn

def list_procedures():
    try:
        with get_conn() as cn:
            cursor = cn.cursor()
            cursor.execute("""
                SELECT p.name AS procedure_name, prm.name AS param_name, TYPE_NAME(prm.user_type_id) AS param_type, prm.max_length, prm.is_output FROM sys.procedures p
                LEFT JOIN sys.parameters prm ON p.object_id = prm.object_id ORDER BY p.name, prm.parameter_id
                           """)

            procedures = {}
            for row in cursor.fetchall():
                name = row.procedure_name
                if name not in procedures:
                    procedures[name] = []
                if row.param_name:
                    procedures[name].append({
                        "name": row.param_name,
                        "type": row.param_type,
                        "max_length": row.max_length,
                        "is_output": bool(row.is_output)
                    })

            return [{"name": n, "params": p} for n, p in procedures.items()]

    except pyodbc.Error as e:
        print("pyodbc.Error:", e.args)
        raise
    except Exception as e:
        print("일반 오류:", e)
        raise

