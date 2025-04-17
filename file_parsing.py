import re
import os
from database import get_connection
from datetime import datetime
import shutil

ERROR_FOLDER = "C:/reports/local_qst/errores/"

def parse_qst(file_path, log_callback, show_error_dialog):
    current_test_id = None
    conn = get_connection()
    cursor = conn.cursor()
    inserted_tested_unit = False
    inserted_tested_unit_details = 0
    
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
                    final_test_result = test_result
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
                        inserted_tested_unit = True
                    else:
                        print("No TestID returned. Could be due to INSERT failure.")
                
                elif parts[0] == 'ME':
                    test_measurement_raw = parts[6] # Raw measurement value i.e. "5.67V"
                    test_name = parts[9].strip()
                    match = re.search(r"([\d.]+)", test_measurement_raw)
                    test_measurement_value = float(match.group(1)) if match else 0 # Extract numeric value i.e. "5.67" if None then
                    unit = re.search(r"[A-Za-z]+$", test_measurement_raw).group(0) if re.search(r"[A-Za-z]+$", test_measurement_raw) else "NA"
                    # Extract unit from the raw measurement value i.e. "V" or "A" or "mA" or "mV" or "w" etc.
                    low_limit = float(parts[-4]) if parts[-4] else None
                    high_limit = float(parts[-3]) if parts[-3] else None
                    test_result = parts[7].strip()
                    
                    if test_measurement_value is not None and current_test_id is not None:
                        cursor.execute("""
                        INSERT INTO TestedUnitDetails (
                            TestedUnitID, TestName, TestMeasurement, MeasurementUnit, 
                            LowLimit, HighLimit, TestResult
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, current_test_id, test_name, test_measurement_value, unit, 
                        low_limit, high_limit, test_result)
                        conn.commit()
                        inserted_tested_unit_details += cursor.rowcount
                        if test_result == "FAIL":
                            final_test_result = "FAIL"
                        #log_callback(f"Procesado correctamente: {os.path.basename(file_path)}")
                    elif test_measurement_value is None:
                        log_callback(f"Advertencia: No se encontró valor de medición para '{test_name}' en '{os.path.basename(file_path)}'. Línea omitida.")
                    elif current_test_id is None:
                        log_callback(f"Advertencia: No hay TestID disponible para '{test_name}' en '{os.path.basename(file_path)}'. Línea omitida.")
                    else:
                        log_callback(f"ERROR: Ha ocurrido un error con el archivo, reporte esto al técnico de pruebas'{os.path.basename(file_path)}'.")
        if inserted_tested_unit and node is not None and current_test_id is not None:
            # log_callback(f"[{final_test_result}-Node:{node}] [TestID:{current_test_id}][{inserted_tested_unit_details} Tests] {os.path.basename(file_path)}")
            #log_callback(f"Insertadas {inserted_tested_unit_details} mediciones en TestedUnitDetails para: {os.path.basename(file_path)}")
            log_callback(f"[{final_test_result}-Node:{node}]{os.path.basename(file_path)}")
        elif inserted_tested_unit:
            log_callback(f"{final_test_result}: {os.path.basename(file_path)} - {inserted_tested_unit_details} tests registered.")
        else:
            log_callback(f"ERROR: en def parse_qst(else block) {os.path.basename(file_path)}")
    except Exception as e:
        #print(f"Error procesando archivo {file_path}: {str(e)}")       
        log_callback(f"Error al procesar {os.path.basename(file_path)}: {str(e)}")
        try:
            os.makedirs(ERROR_FOLDER, exist_ok=True) # Crea la carpeta si no existe
            destination_path = os.path.join(ERROR_FOLDER, os.path.basename(file_path))
            shutil.move(file_path, destination_path)
            log_callback(f"Archivo movido a {ERROR_FOLDER}")
            show_error_dialog(os.path.basename(file_path), ERROR_FOLDER)
        except Exception as move_error:
            log_callback(f"Error al mover el archivo: {str(move_error)}")
    finally:
        cursor.close()
        conn.close()
