"""AutoPSY — Anti-Forensic Detection & Evidence Integrity Framework for Software-Defined Vehicles."""
__version__ = "1.0.0"

from .protocols.can_bus import (
    CANFrame, CANFrameType, CANBusInterface,
    COMMON_CAN_IDS, OBD2_REQUEST_ID, OBD2_RESPONSE_BASE,
    analyze_can_traffic,
)

from .protocols.doip import (
    DoIPPayloadType, UDSServiceID, DiagnosticSession, NRC,
    DTCStatusMask, DoIPHeader, COMMON_DIDS, FORENSIC_DIDS,
    build_doip_header, build_vehicle_id_request, build_routing_activation,
    build_diagnostic_message, build_uds_session_control,
    build_uds_extended_session, build_uds_programming_session,
    build_uds_security_access, build_uds_read_data, build_uds_read_multi_data,
    build_uds_ecu_reset, build_uds_clear_dtc, build_uds_read_dtc,
    build_uds_read_dtc_by_status, build_uds_read_memory,
    build_uds_request_download, build_uds_routine_control,
    build_uds_tester_present, build_uds_write_data,
    parse_doip_header, parse_uds_response,
)

from .protocols.someip import (
    SOMEIPHeader, SDEntry, SDOption, MessageType, ReturnCode, SDEntryType,
    build_someip_header, build_sd_entry, build_sd_option_ipv4, build_sd_message,
    parse_someip_header,
    SOMEIP_SD_PORT, SOMEIP_SD_MULTICAST,
)

from .protocols.forensic_container import (
    EvidenceBlock, CaseInfo, ForensicContainer,
)

from .recon.scanner import (
    VehicleScanner, VehicleScanResult, ECUInfo, SOMEIPService,
)

from .attack.vehicle_attacks import (
    AttackResult, CANAttacks, DoIPAttacks, SOMEIPAttacks,
    run_all_attacks_demo,
)

from .forensics.acquisition import ForensicAcquisition

from .antiforensics.detector import (
    TamperIndicator, AntiForensicReport, AntiForensicDetector,
    run_demo_analysis,
)

from .reporting.report_gen import generate_json_report, generate_markdown_report

__all__ = [
    "CANFrame", "CANFrameType", "CANBusInterface",
    "COMMON_CAN_IDS", "OBD2_REQUEST_ID", "OBD2_RESPONSE_BASE",
    "analyze_can_traffic",
    "DoIPPayloadType", "UDSServiceID", "DiagnosticSession", "NRC",
    "DTCStatusMask", "DoIPHeader", "COMMON_DIDS", "FORENSIC_DIDS",
    "build_doip_header", "build_vehicle_id_request", "build_routing_activation",
    "build_diagnostic_message", "build_uds_session_control",
    "build_uds_extended_session", "build_uds_programming_session",
    "build_uds_security_access", "build_uds_read_data", "build_uds_read_multi_data",
    "build_uds_ecu_reset", "build_uds_clear_dtc", "build_uds_read_dtc",
    "build_uds_read_dtc_by_status", "build_uds_read_memory",
    "build_uds_request_download", "build_uds_routine_control",
    "build_uds_tester_present", "build_uds_write_data",
    "parse_doip_header", "parse_uds_response",
    "SOMEIPHeader", "SDEntry", "SDOption", "MessageType", "ReturnCode", "SDEntryType",
    "build_someip_header", "build_sd_entry", "build_sd_option_ipv4", "build_sd_message",
    "parse_someip_header", "SOMEIP_SD_PORT", "SOMEIP_SD_MULTICAST",
    "EvidenceBlock", "CaseInfo", "ForensicContainer",
    "VehicleScanner", "VehicleScanResult", "ECUInfo", "SOMEIPService",
    "AttackResult", "CANAttacks", "DoIPAttacks", "SOMEIPAttacks",
    "run_all_attacks_demo",
    "ForensicAcquisition",
    "TamperIndicator", "AntiForensicReport", "AntiForensicDetector",
    "run_demo_analysis",
    "generate_json_report", "generate_markdown_report",
]
