import re
import os
from database_oracle import get_connection
from datetime import datetime
import shutil



def get_error_folder():
    """return the dynamical path for the error folder
        C:/reports/local_qst/errors/{year}/{month}/{day}/
    """
    ERROR_FOLDER = "C:/reports/local_qst/errors/"
    today = datetime.today()
    year = today.strftime("%Y")
    month = today.strftime("%B")
    day = today.strftime("%d")
    
    # Create the directory if it doesn't exist
    error_folder_path = os.path.join(ERROR_FOLDER, year, month, day)
    os.makedirs(error_folder_path, exist_ok=True)
    
    return error_folder_path

def move_to_error_folder(file_path, log_callback, show_error_dialog):
    error_folder_path = get_error_folder()
    os.makedirs(error_folder_path, exist_ok=True) # Crea la carpeta si no existe
    destination_path = os.path.join(error_folder_path, os.path.basename(file_path))
    try:
        shutil.move(file_path, destination_path)
        log_callback(f"Archivo movido a {error_folder_path}")
        show_error_dialog(os.path.basename(file_path), error_folder_path+"\n PORFAVOR: Reporte este error al técnico de pruebas")
    except FileNotFoundError:
        log_callback(f"ERROR: El archivo '{file_path}' no se encontró para mover a la carpeta de errores.")
    except PermissionError:
        log_callback(f"ERROR: Permiso denegado al intentar mover '{file_path}'. Asegúrate de que no esté en uso.")
    except Exception as move_error:
        log_callback(f"Error al mover el archivo: {str(move_error)}")

def parse_qst(file_path, log_callback, show_error_dialog):
    current_test_id = None
    conn = get_connection()
    cursor = conn.cursor()
    inserted_tested_unit = False
    inserted_tested_unit_details = 0
    processing_successful = False
    
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

                    tested_unit_id = cursor.var(int)

                    cursor.execute("""
                        BEGIN
                            INSERT INTO Tested_Units (
                                SERIAL_NUMBER, CUSTOMER_MODEL, INTERNAL_MODEL, TEST_DATE, NODE, OPERATOR, PROGRAM_NAME, PROGRAM_VERSION,
                                TEST_DURATION, TEST_RESULT
                            ) 
                            VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10)
                            RETURNING TESTED_UNIT_ID INTO :11;
                        END;
                    """, [
                        serial_number, customer_model, internal_model, test_date, node, operator, 
                        program_name, program_version, test_duration, test_result,
                        tested_unit_id
                    ])

                    current_test_id = tested_unit_id.getvalue()


                    # row = cursor.fetchone()
                    # current_test_id = row[0] if row else None

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
                            INSERT INTO Tested_Unit_Details (
                                TESTED_UNIT_ID, TEST_NAME, TEST_MEASUREMENT, MEASUREMENT_UNIT, 
                                LOW_LIMIT, HIGHT_LIMIT, TEST_RESULT
                            )
                            VALUES (:1, :2, :3, :4, :5, :6, :7)
                        """, [
                            current_test_id, test_name, test_measurement_value, unit, 
                            low_limit, high_limit, test_result
                        ])

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
            #log_callback(f"[NODE:{node}-{final_test_result}] Tests registered: {inserted_tested_unit_details} of 9 \n{os.path.basename(file_path)}")
            log_callback(f"[NODE:{node}-{final_test_result}]- Registrado correctamente en DB \n{os.path.basename(file_path)}")
            processing_successful = True
        else:
            reason = []
            if not inserted_tested_unit:
                reason.append("inserted_tested_unit es False")
            if node is None:
                reason.append("node es None")
            if current_test_id is None:
                reason.append("current_test_id es None")
            log_callback(f"ERROR: Fallo al registrar la unidad '{os.path.basename(file_path)}'. Razones: {', '.join(reason)}")
            move_to_error_folder(file_path, log_callback, show_error_dialog)
    except Exception as e:
        #print(f"Error procesando archivo {file_path}: {str(e)}")       
        log_callback(f"Error al procesar {os.path.basename(file_path)}: {str(e)}")
        move_to_error_folder(file_path, log_callback, show_error_dialog)
    finally:
        cursor.close()
        conn.close()
        return processing_successful 
