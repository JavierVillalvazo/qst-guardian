import re
from database import get_connection
from datetime import datetime

def parse_qst(file_path):
    current_test_id = None
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                parts = line.strip().split('|')

                if parts[0] == 'EV':
                    customer_model = parts[1]
                    serial_number = parts[2]
                    internal_model = parts[2].split('-',1)[1]  # Extract internal_model from serial number
                    test_date = datetime.strptime(parts[3], "%Y%m%d%H%M%S")
                    node = int(re.search(r"_(\d+)_", file_path).group(1))
                    operator = parts[9]
                    program_name = parts[17]
                    program_version = parts[18]
                    test_duration = parts[6]
                    test_result = parts[14]
                    #equipment_name = parts[10]}
                    #assembly_revision = parts[-1]

                    cursor.execute("""
                        INSERT INTO TestedUnits (
                            SerialNumber, CustomerModel, InternalModel, TestDate, Node, Operator, ProgramName, ProgramVersion,
                            TestDuration, TestResult
                        ) 
                        OUTPUT INSERTED.TestedUnitID
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, serial_number, customer_model, internal_model, test_date, node, operator, 
                        program_name, program_version, test_duration, test_result)

                    row = cursor.fetchone()
                    current_test_id = row[0] if row else None

                    if current_test_id is not None:
                        conn.commit()
                    else:
                        print("No TestID returned. Could be due to INSERT failure.")
                
                elif parts[0] == 'ME':
                    test_measurement_raw = parts[6] # Raw measurement value i.e. "5.67V"
                    test_name = parts[9].strip()
                    match = re.search(r"([\d.]+)", test_measurement_raw)
                    test_measurement_value = float(match.group(1)) if match else None # Extract numeric value i.e. "5.67"
                    unit = re.search(r"[A-Za-z]+$", test_measurement_raw).group(0) if re.search(r"[A-Za-z]+$", test_measurement_raw) else "V"
                    # Extract unit from the raw measurement value i.e. "V" or "A" or "mA" or "mV" or "w" etc.
                    low_limit = float(parts[-4]) if parts[-4] else None
                    high_limit = float(parts[-3]) if parts[-3] else None
                    test_result = parts[7].strip()

                    cursor.execute("""
                        INSERT INTO TestedUnitDetails (
                            TestedUnitID, TestName, TestMeasurement, MeasurementUnit, 
                            LowLimit, HighLimit, TestResult
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, current_test_id, test_name, test_measurement_value, unit, 
                    low_limit, high_limit, test_result)
                    conn.commit()
    except Exception as e:
        print(f"❌ Error procesando archivo {file_path}: {str(e)}")       
    finally:
        cursor.close()
        conn.close()
