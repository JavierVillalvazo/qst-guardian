import re
from datetime import datetime

filename = "2510SMT0374-MX12ELWC1A8UB0000-00MX_4_20250326132740_PASS.qst"
file_path = "/" + filename

def parse_qst_filename(filename):
    # Ejemplo: 2510SMT0374-MX12ELWC1A8UB0000-00MX_4_20250326132740_PASS.qst
    match = re.search(r"_(\d+)_(\d{14})_(PASS|FAIL)\.qst", filename)
    if match:
        node = match.group(1)
        date_str = match.group(2)
        result = match.group(3)
        test_date = datetime.strptime(date_str, "%Y%m%d%H%M%S")
        return {"node": node, "test_date": test_date, "result": result}
    else:
        raise ValueError("Formato de archivo incorrecto")


def parse_qst_content(file_path):
    with open(file_path, "r") as f:
        lines = f.readlines()
        # Extraer datos de las pruebas (ej: líneas ME|...|PASS)
        # Implementar lógica según estructura de logs
        return {"measurements": [...]}

print(parse_qst_filename(filename).get("result"))