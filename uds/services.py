from uds import responses
from loggers.logger_app import logger

SUPPORTED_PIDS_RESPONSE_MASK = 0x80000000

SUPPORTED_PIDS_RESPONSE_INIT_VALUE = 0x00000001

SUPPORTED_PIDS_RESPONSE_NUMBER_OF_PIDs = 32

POSITIVE_RESPONSE_MASK = 0x40

BIG_ENDIAN = "big"

FUEL_TYPE = responses.get_fuel_type()

DTCs = responses.get_dtcs()

VIN = responses.get_vin()

CVN = responses.get_cvn()

CAL_ID = responses.get_cal_id()

ECU_NAME = responses.get_ecu_name()

BOX_CODE = responses.get_box_code()

SW_VERS = responses.get_sw_vers()

FAZIT = responses.get_fazit()

SERIAL = responses.get_serial()

TCU_ASW = responses.get_tcu_asw()

SERVICES = [
    {"id": 0x01, "description": "Show current data", "response": lambda: None,
     "pids": [
         {"id": 0x05, "description": "Engine coolant temperature", "response": lambda: responses.get_engine_temperature()},
         {"id": 0x0D, "description": "Vehicle speed", "response": lambda: responses.get_vehicle_speed()},
         {"id": 0x2F, "description": "Fuel tank level input", "response": lambda: responses.get_fuel_level()},
         {"id": 0x51, "description": "Fuel type", "response": lambda: FUEL_TYPE}
     ]},
    {"id": 0x03, "description": "Show DTCs", "response": lambda: DTCs},
    {"id": 0x09, "description": "Request vehicle information", "response": lambda: None,
     "pids": [
         {"id": 0x02, "description": "Vehicle Identification Number(VIN)", "response": lambda: VIN},
         {"id": 0x06, "description": "CVN", "response": lambda: CVN},
         {"id": 0x04, "description": "CAL ID", "response": lambda: CAL_ID},
         {"id": 0x0A, "description": "ECU name", "response": lambda: ECU_NAME}
     ]},
    {"id": 0x22, "description": "Request Data By Identifier", "response": lambda: None,
     "pids": [
         {"id": 0xF187, "description": "VW Spare Part Number", "response": lambda: BOX_CODE},
         {"id": 0xF189, "description": "VW Application SW Version", "response": lambda: SW_VERS},
         {"id": 0xF17C, "description": "VW FAZIT ID String", "response": lambda: FAZIT},
         {"id": 0xF18C, "description": "Controller Serial Number", "response": lambda: SERIAL},
         {"id": 0x110D, "description": "TCU Application SW Vers", "response": lambda: TCU_ASW}
     ]}

]


def process_service_request(requested_sid, requested_pid):
    if is_service_request_valid(requested_sid, requested_pid):
        service_response, service_pids = get_service(requested_sid)
        if service_pids is not None and requested_pid is not None:
            if is_supported_pids_request(requested_pid):
                response = get_supported_pids_response(service_pids, requested_pid)
                return add_response_prefix(requested_sid, requested_pid, response)
            return add_response_prefix(requested_sid, requested_pid, get_pid_response(requested_pid, service_pids))
        return add_response_prefix(requested_sid, requested_pid, service_response)
    else:
        logger.warning("Invalid request")
        return None


def add_response_prefix(requested_sid, requested_pid, response):
    if response is not None:
        response_sid = bytes([POSITIVE_RESPONSE_MASK + requested_sid])
        if requested_pid is None:
            return response_sid + response
        return response_sid + requested_pid.to_bytes(2, byteorder='big') + response
    return None


def is_service_request_valid(requested_sid, requested_pid):
    is_sid_valid_ = is_sid_valid(requested_sid)
    return is_sid_valid_ and is_pid_valid(requested_pid) or (is_sid_valid_ and requested_pid is None)


def is_sid_valid(sid):
    return isinstance(sid, int)


def is_pid_valid(pid):
    return isinstance(pid, int)


def get_service(requested_sid):
    for service in SERVICES:
        if service.get("id") == requested_sid:
            logger.info("Requested OBD SID " + hex(requested_sid) + ": " + service.get("description"))
            return service.get("response")(), service.get("pids")
    logger.warning("Requested SID " + hex(requested_sid) + " not supported")
    return None, None


def get_pid_response(requested_pid, pids):
    for pid in pids:
        if pid.get("id") == requested_pid:
            logger.info("Requested PID " + hex(requested_pid) + ": " + pid.get("description"))
            return pid.get("response")()
    logger.warning("Requested PID " + hex(requested_pid) + " not supported")
    return None


def is_supported_pids_request(requested_pid):
    return requested_pid % SUPPORTED_PIDS_RESPONSE_NUMBER_OF_PIDs == 0


def get_supported_pids_response(supported_pids, requested_pid):
    supported_pids_response = init_supported_pids_response(requested_pid)
    for pid in supported_pids:
        supported_pid = pid.get("id")
        if requested_pid < supported_pid < (requested_pid + SUPPORTED_PIDS_RESPONSE_NUMBER_OF_PIDs):
            supported_pids_response |= SUPPORTED_PIDS_RESPONSE_MASK >> (supported_pid - requested_pid - 1)
    return supported_pids_response.to_bytes(4, BIG_ENDIAN)


def init_supported_pids_response(requested_pid):
    if requested_pid / SUPPORTED_PIDS_RESPONSE_NUMBER_OF_PIDs > 6:
        return SUPPORTED_PIDS_RESPONSE_INIT_VALUE >> 1
    return SUPPORTED_PIDS_RESPONSE_INIT_VALUE
