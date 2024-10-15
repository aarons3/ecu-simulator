import isotp
import ecu_config
from uds import services
from addresses import UDS_ECU_ADDRESS, UDS_TARGET_ADDRESS
from loggers.logger_app import logger

CAN_INTERFACE = ecu_config.get_can_interface()


def start():
    request_socket = create_isotp_socket(UDS_ECU_ADDRESS, UDS_TARGET_ADDRESS)
    response_socket = create_isotp_socket(UDS_ECU_ADDRESS, UDS_TARGET_ADDRESS)
    while True:
        request = request_socket.recv()
        requested_pid, requested_sid = get_sid_and_pid(request)
        if requested_sid is not None:
            log_request(request)
            response = services.process_service_request(requested_sid, requested_pid)
            if response is not None:
                log_response(response)
                response_socket.send(response)

def create_isotp_socket(receiver_address, target_address):
    socket = isotp.socket()
    socket.bind(CAN_INTERFACE, isotp.Address(rxid=receiver_address, txid=target_address))
    return socket


def get_sid_and_pid(request):
    pid, sid = None, None
    if request is not None:
        request_bytes_length = len(request)
        if request_bytes_length >= 1:
            sid = request[0]
        if request_bytes_length == 2:
            pid = request[1]
        if request_bytes_length == 3:
            pid = int.from_bytes(request[1:3], byteorder='big')
    return pid, sid


def log_request(request):
    logger.info("Receiving on UDS address " + hex(UDS_ECU_ADDRESS) + " from " + hex(UDS_TARGET_ADDRESS)
                + " Request: 0x" + request.hex())


def log_response(response):
    logger.info("Sending to " + hex(UDS_TARGET_ADDRESS) + " Response: 0x" + response.hex())