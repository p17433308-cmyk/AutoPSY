"""AutoPSY test suite — protocols, recon, attacks, forensics, anti-forensics, reporting."""
import os
import sys
import json
import time
import struct
import hashlib
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestCANBus:
    def test_can_frame_build(self):
        from autopsy.protocols.can_bus import CANFrame
        frame = CANFrame(arb_id=0x0C0, data=b"\x1F\x40\x00\x00\x00\x00\x00\x00", dlc=8)
        raw = frame.to_bytes()
        assert len(raw) > 12
        assert struct.unpack("<I", raw[0:4])[0] == 0x0C0

    def test_can_frame_roundtrip(self):
        from autopsy.protocols.can_bus import CANFrame
        original = CANFrame(arb_id=0x1A0, data=b"\xAA\xBB\xCC\xDD", dlc=4)
        raw = original.to_bytes()
        parsed = CANFrame.from_bytes(raw)
        assert parsed is not None
        assert parsed.arb_id == 0x1A0
        assert parsed.data == b"\xAA\xBB\xCC\xDD"

    def test_can_frame_hex_dump(self):
        from autopsy.protocols.can_bus import CANFrame
        frame = CANFrame(arb_id=0x0C0, data=b"\x1F\x40", dlc=2, timestamp=1000.0)
        dump = frame.hex_dump()
        assert "0C0" in dump
        assert "1F 40" in dump

    def test_common_can_ids(self):
        from autopsy.protocols.can_bus import COMMON_CAN_IDS, OBD2_REQUEST_ID
        assert OBD2_REQUEST_ID == 0x7DF
        assert 0x7DF in COMMON_CAN_IDS

    def test_can_bus_interface(self):
        from autopsy.protocols.can_bus import CANBusInterface
        bus = CANBusInterface("vcan0")
        assert bus.interface == "vcan0"

    def test_analyze_can_traffic(self):
        from autopsy.protocols.can_bus import CANFrame, analyze_can_traffic
        frames = [
            CANFrame(arb_id=0x0C0, data=b"\x00" * 8, dlc=8, timestamp=1000.0 + i * 0.01)
            for i in range(20)
        ]
        result = analyze_can_traffic(frames)
        assert result["total_frames"] == 20
        assert result["unique_ids"] == 1

    def test_analyze_empty(self):
        from autopsy.protocols.can_bus import analyze_can_traffic
        result = analyze_can_traffic([])
        assert result["total_frames"] == 0


class TestDoIP:
    def test_doip_header_build(self):
        from autopsy.protocols.doip import build_vehicle_id_request, DOIP_PROTOCOL_VERSION
        pkt = build_vehicle_id_request()
        assert pkt[0] == DOIP_PROTOCOL_VERSION
        assert len(pkt) == 8

    def test_routing_activation(self):
        from autopsy.protocols.doip import build_routing_activation
        pkt = build_routing_activation(source_address=0x0E80)
        assert len(pkt) > 8
        payload_type = struct.unpack(">H", pkt[2:4])[0]
        assert payload_type == 0x0005

    def test_uds_read_data(self):
        from autopsy.protocols.doip import build_uds_read_data, UDSServiceID
        uds = build_uds_read_data(0xF190)
        assert uds[0] == UDSServiceID.READ_DATA_BY_ID
        assert struct.unpack(">H", uds[1:3])[0] == 0xF190

    def test_uds_security_access(self):
        from autopsy.protocols.doip import build_uds_security_access, UDSServiceID
        uds = build_uds_security_access(0x01)
        assert uds[0] == UDSServiceID.SECURITY_ACCESS
        assert uds[1] == 0x01

    def test_uds_clear_dtc(self):
        from autopsy.protocols.doip import build_uds_clear_dtc, UDSServiceID
        uds = build_uds_clear_dtc()
        assert uds[0] == UDSServiceID.CLEAR_DTC

    def test_uds_ecu_reset(self):
        from autopsy.protocols.doip import build_uds_ecu_reset, UDSServiceID
        uds = build_uds_ecu_reset(0x01)
        assert uds[0] == UDSServiceID.ECU_RESET

    def test_parse_doip_header(self):
        from autopsy.protocols.doip import build_vehicle_id_request, parse_doip_header
        pkt = build_vehicle_id_request()
        parsed = parse_doip_header(pkt)
        assert parsed is not None
        assert parsed["payload_type"] == 0x0001

    def test_parse_uds_positive(self):
        from autopsy.protocols.doip import parse_uds_response
        resp = parse_uds_response(bytes([0x62, 0xF1, 0x90]) + b"WBA11CF090CH77832")
        assert resp["type"] == "positive"
        assert resp["service"] == 0x22

    def test_parse_uds_negative(self):
        from autopsy.protocols.doip import parse_uds_response
        resp = parse_uds_response(bytes([0x7F, 0x22, 0x33]))
        assert resp["type"] == "negative"
        assert resp["nrc"] == 0x33

    def test_forensic_dids(self):
        from autopsy.protocols.doip import FORENSIC_DIDS, COMMON_DIDS
        assert 0xF190 in COMMON_DIDS
        assert 0xF186 in FORENSIC_DIDS
        assert len(FORENSIC_DIDS) >= 5


class TestSOMEIP:
    def test_someip_header_build(self):
        from autopsy.protocols.someip import SOMEIPHeader, build_someip_header
        hdr = SOMEIPHeader(service_id=0x1234, method_id=0x0001, payload=b"\x00" * 4)
        raw = build_someip_header(hdr)
        assert len(raw) == 20
        msg_id = struct.unpack(">I", raw[0:4])[0]
        assert (msg_id >> 16) == 0x1234

    def test_someip_parse_roundtrip(self):
        from autopsy.protocols.someip import SOMEIPHeader, build_someip_header, parse_someip_header
        hdr = SOMEIPHeader(service_id=0xABCD, method_id=0x0001, payload=b"\xDE\xAD")
        raw = build_someip_header(hdr)
        parsed = parse_someip_header(raw)
        assert parsed.service_id == 0xABCD
        assert parsed.payload == b"\xDE\xAD"

    def test_sd_message(self):
        from autopsy.protocols.someip import SDEntry, SDEntryType, build_sd_message
        entry = SDEntry(entry_type=SDEntryType.OFFER_SERVICE, service_id=0x1000, instance_id=0x0001)
        raw = build_sd_message([entry])
        assert len(raw) > 16


class TestForensicContainer:
    def test_evidence_block_hash(self):
        from autopsy.protocols.forensic_container import EvidenceBlock
        block = EvidenceBlock(block_type="can_capture", data=b"test data")
        assert block.sha256 == hashlib.sha256(b"test data").hexdigest()

    def test_container_add_verify(self):
        from autopsy.protocols.forensic_container import ForensicContainer, EvidenceBlock, CaseInfo
        container = ForensicContainer(case_info=CaseInfo(case_id="TEST-001", vehicle_vin="TEST"))
        container.add_evidence(EvidenceBlock(block_type="can_capture", data=b"can data"))
        container.add_evidence(EvidenceBlock(block_type="doip_session", data=b"doip data"))
        assert len(container.evidence_blocks) == 2
        assert container.verify_integrity()["valid"]

    def test_container_save_load(self, tmp_path):
        from autopsy.protocols.forensic_container import ForensicContainer, EvidenceBlock, CaseInfo
        container = ForensicContainer(case_info=CaseInfo(case_id="SAVE-001", vehicle_vin="WBA123"))
        container.add_evidence(EvidenceBlock(block_type="test", data=b"\xDE\xAD\xBE\xEF"))
        path = str(tmp_path / "evidence.json")
        container.save(path)
        loaded = ForensicContainer.load(path)
        assert loaded.case_info.case_id == "SAVE-001"
        assert len(loaded.evidence_blocks) == 1

    def test_container_integrity_failure(self):
        from autopsy.protocols.forensic_container import ForensicContainer, EvidenceBlock, CaseInfo
        container = ForensicContainer(case_info=CaseInfo(case_id="TAMPER"))
        container.add_evidence(EvidenceBlock(block_type="test", data=b"original"))
        container.evidence_blocks[0].sha256 = "0000000000000000000000000000000000000000000000000000000000000000"
        result = container.verify_integrity()
        assert not result["valid"]


class TestRecon:
    def test_ecu_info_dataclass(self):
        from autopsy.recon.scanner import ECUInfo
        ecu = ECUInfo(name="Engine_ECU", logical_address=0x0010, vin="WBA11CF090CH77832")
        d = ecu.to_dict()
        assert d["name"] == "Engine_ECU"
        assert d["vin"] == "WBA11CF090CH77832"

    def test_scan_result_summary(self):
        from autopsy.recon.scanner import VehicleScanResult
        result = VehicleScanResult(scan_time=time.time(), scan_duration=2.5)
        s = result.summary()
        assert s["doip_entities"] == 0
        assert s["ecus_fingerprinted"] == 0

    def test_scanner_class(self):
        from autopsy.recon.scanner import VehicleScanner
        scanner = VehicleScanner(target="192.168.1.10", interface="vcan0")
        assert scanner.target == "192.168.1.10"


class TestAttacks:
    def test_attack_result_dataclass(self):
        from autopsy.attack.vehicle_attacks import AttackResult
        r = AttackResult(attack_name="CAN Injection", target="vcan0",
                         success=True, packets_sent=100, detail="Injected 100 frames",
                         wire_data=b"\x00" * 16)
        assert r.success
        assert r.packets_sent == 100

    def test_can_injection_builds_frames(self):
        from autopsy.attack.vehicle_attacks import CANAttacks
        result = CANAttacks.message_injection("vcan0", 0x0C0, b"\x1F\x40\x00\x00\x00\x00\x00\x00", count=10)
        assert result.attack_name == "CAN Message Injection"
        assert result.packets_sent == 10
        assert len(result.wire_data) > 0

    def test_doip_session_hijack(self):
        from autopsy.attack.vehicle_attacks import DoIPAttacks
        result = DoIPAttacks.session_hijack("192.168.1.10")
        assert "DoIP Session Hijack" in result.attack_name
        assert len(result.wire_data) > 0

    def test_someip_fake_offer(self):
        from autopsy.attack.vehicle_attacks import SOMEIPAttacks
        result = SOMEIPAttacks.fake_service_offer()
        assert result.attack_name == "SOME/IP Fake Service Offer"
        assert len(result.wire_data) > 0

    def test_run_all_attacks(self):
        from autopsy.attack.vehicle_attacks import run_all_attacks_demo
        results = run_all_attacks_demo("192.168.1.10")
        assert len(results) >= 5
        for r in results:
            assert r.attack_name
            assert r.wire_data is not None


class TestForensicAcquisition:
    def test_acquisition_class(self):
        from autopsy.protocols.forensic_container import CaseInfo
        from autopsy.forensics.acquisition import ForensicAcquisition
        case = CaseInfo(case_id="ACQ-001", examiner="Test", vehicle_vin="WBA123")
        acq = ForensicAcquisition(case)
        assert acq is not None

    def test_full_acquisition(self):
        from autopsy.protocols.forensic_container import CaseInfo
        from autopsy.forensics.acquisition import ForensicAcquisition
        case = CaseInfo(case_id="ACQ-002", vehicle_vin="WBA11CF090CH77832")
        acq = ForensicAcquisition(case)
        container = acq.full_acquisition(target_ip="192.168.1.10", can_interface="vcan0")
        assert len(container.evidence_blocks) > 0
        assert container.verify_integrity()["valid"]


class TestAntiForensics:
    def test_tamper_indicator(self):
        from autopsy.antiforensics.detector import TamperIndicator
        ind = TamperIndicator(
            indicator_type="firmware_tamper", severity="critical",
            confidence=0.95, description="Firmware hash mismatch",
            evidence="Expected abc, got def",
            forensic_significance="ECU firmware was modified",
        )
        d = ind.to_dict()
        assert d["severity"] == "critical"
        assert "95" in str(d["confidence"])

    def test_report_dataclass(self):
        from autopsy.antiforensics.detector import AntiForensicReport, TamperIndicator
        report = AntiForensicReport(vehicle_vin="WBA123")
        report.indicators.append(TamperIndicator(
            indicator_type="test", severity="high", confidence=0.8,
            description="Test indicator",
        ))
        d = report.to_dict()
        assert d["indicator_count"] == 1

    def test_run_demo_analysis(self):
        from autopsy.antiforensics.detector import run_demo_analysis
        report = run_demo_analysis()
        d = report.to_dict()
        assert d["indicator_count"] > 0
        assert d["overall_risk"] in ("low", "medium", "high", "critical")

    def test_detector_class(self):
        from autopsy.antiforensics.detector import AntiForensicDetector
        detector = AntiForensicDetector(vin="WBA11CF090CH77832")
        assert detector.vin == "WBA11CF090CH77832"


class TestReporting:
    def test_json_report(self, tmp_path):
        from autopsy.protocols.forensic_container import ForensicContainer, EvidenceBlock, CaseInfo
        from autopsy.reporting.report_gen import generate_json_report
        container = ForensicContainer(case_info=CaseInfo(case_id="RPT-001", vehicle_vin="WBA123"))
        container.add_evidence(EvidenceBlock(block_type="test", data=b"evidence"))
        path = str(tmp_path / "report.json")
        generate_json_report(container, None, path)
        assert os.path.exists(path)
        with open(path) as f:
            data = json.load(f)
        assert "RPT-001" in json.dumps(data)

    def test_markdown_report(self, tmp_path):
        from autopsy.protocols.forensic_container import ForensicContainer, EvidenceBlock, CaseInfo
        from autopsy.reporting.report_gen import generate_markdown_report
        container = ForensicContainer(case_info=CaseInfo(case_id="RPT-002", vehicle_vin="WBA456"))
        container.add_evidence(EvidenceBlock(block_type="test", data=b"evidence"))
        path = str(tmp_path / "report.md")
        generate_markdown_report(container, None, path)
        assert os.path.exists(path)
        with open(path) as f:
            content = f.read()
        assert "RPT-002" in content


class TestExports:
    def test_all_exports(self):
        import autopsy
        assert len(autopsy.__all__) >= 50
        for name in autopsy.__all__:
            assert hasattr(autopsy, name), f"Missing export: {name}"

    def test_version(self):
        import autopsy
        assert autopsy.__version__ == "1.0.0"
