"""
Telemetry Collection Service
Collects metrics from SNMP, NetFlow, and RTCP sources
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
from abc import ABC, abstractmethod

from src.models.schemas import SNMPMetrics, RTCPMetrics, NetFlowData, MetricsPayload

logger = logging.getLogger(__name__)


class TelemetryCollector(ABC):
    """Abstract base class for telemetry collectors"""
    
    @abstractmethod
    async def collect(self) -> List[Any]:
        """Collect telemetry data"""
        pass
    
    @abstractmethod
    async def validate(self, data: Any) -> bool:
        """Validate collected data"""
        pass


class SNMPCollector(TelemetryCollector):
    """SNMP metrics collector"""
    
    def __init__(self, community: str = "public", version: str = "2c", 
                 timeout: int = 5, retries: int = 3):
        """Initialize SNMP collector"""
        self.community = community
        self.version = version
        self.timeout = timeout
        self.retries = retries
        self.devices: Dict[str, str] = {}  # device_id -> device_ip
    
    def register_device(self, device_id: str, device_ip: str):
        """Register a device for monitoring"""
        self.devices[device_id] = device_ip
        logger.info(f"Registered SNMP device: {device_id} ({device_ip})")
    
    async def collect(self) -> List[SNMPMetrics]:
        """Collect SNMP metrics from registered devices"""
        metrics = []
        
        for device_id, device_ip in self.devices.items():
            try:
                device_metrics = await self._collect_device_metrics(device_id, device_ip)
                metrics.extend(device_metrics)
            except Exception as e:
                logger.error(f"Error collecting SNMP metrics from {device_id}: {e}")
        
        return metrics
    
    async def _collect_device_metrics(self, device_id: str, device_ip: str) -> List[SNMPMetrics]:
        """Collect metrics from a single device"""
        # Simulated SNMP collection
        # In production, use pysnmp library
        await asyncio.sleep(0.1)  # Simulate network delay
        
        metrics = []
        for port_id in range(1, 5):
            metric = SNMPMetrics(
                device_id=device_id,
                device_name=f"router-{device_id}",
                port_id=f"ge-0/0/{port_id}",
                interface_name=f"GigaEthernet0/0/{port_id}",
                bytes_in=1000000 + port_id * 100000,
                bytes_out=800000 + port_id * 80000,
                packets_in=10000 + port_id * 1000,
                packets_out=8000 + port_id * 800,
                dropped_packets=10 + port_id,
                queue_length=50 + port_id * 10,
                buffer_utilization_percent=45.5 + port_id * 5,
                bandwidth_utilization_percent=65.0 + port_id * 2,
                cpu_utilization_percent=35.0,
                memory_utilization_percent=42.0,
            )
            metrics.append(metric)
        
        return metrics
    
    async def validate(self, data: SNMPMetrics) -> bool:
        """Validate SNMP metrics"""
        # Check for required fields
        if not data.device_id or not data.interface_name:
            logger.warning("Invalid SNMP metric: missing required fields")
            return False
        
        # Check for reasonable values
        if data.buffer_utilization_percent < 0 or data.buffer_utilization_percent > 100:
            logger.warning(f"Invalid buffer utilization: {data.buffer_utilization_percent}%")
            return False
        
        return True


class RTCPCollector(TelemetryCollector):
    """RTCP metrics collector for RTP streams"""
    
    def __init__(self):
        """Initialize RTCP collector"""
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    def register_session(self, session_id: str, source_ip: str, destination_ip: str):
        """Register an RTP session"""
        self.active_sessions[session_id] = {
            "source_ip": source_ip,
            "destination_ip": destination_ip,
            "created_at": datetime.utcnow()
        }
        logger.info(f"Registered RTP session: {session_id}")
    
    def unregister_session(self, session_id: str):
        """Unregister an RTP session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Unregistered RTP session: {session_id}")
    
    async def collect(self) -> List[RTCPMetrics]:
        """Collect RTCP metrics from active sessions"""
        metrics = []
        
        for session_id in self.active_sessions.keys():
            try:
                metric = await self._collect_session_metrics(session_id)
                if metric:
                    metrics.append(metric)
            except Exception as e:
                logger.error(f"Error collecting RTCP metrics for {session_id}: {e}")
        
        return metrics
    
    async def _collect_session_metrics(self, session_id: str) -> Optional[RTCPMetrics]:
        """Collect metrics from a single RTP session"""
        # Simulated RTCP collection
        # In production, parse actual RTCP packets
        await asyncio.sleep(0.05)  # Simulate processing
        
        metric = RTCPMetrics(
            session_id=session_id,
            round_trip_delay_ms=45.5,
            one_way_delay_ms=22.5,
            jitter_ms=8.5,
            packet_loss_percent=0.2,
            packets_lost=5,
            mos_score=4.2,
            video_artifacts=False
        )
        
        return metric
    
    async def validate(self, data: RTCPMetrics) -> bool:
        """Validate RTCP metrics"""
        if data.jitter_ms < 0 or data.packet_loss_percent < 0:
            return False
        
        if data.mos_score < 1.0 or data.mos_score > 5.0:
            logger.warning(f"Invalid MOS score: {data.mos_score}")
            return False
        
        return True


class NetFlowCollector(TelemetryCollector):
    """NetFlow data collector"""
    
    def __init__(self, listen_port: int = 2055):
        """Initialize NetFlow collector"""
        self.listen_port = listen_port
        self.flow_buffer: List[NetFlowData] = []
    
    async def collect(self) -> List[NetFlowData]:
        """Collect NetFlow data"""
        # Simulated NetFlow collection
        # In production, listen on UDP port and parse NetFlow v5/v9
        await asyncio.sleep(0.1)
        
        flows = []
        # Simulate some flows
        for i in range(5):
            flow = NetFlowData(
                source_ip=f"192.168.1.{100+i}",
                destination_ip=f"10.0.0.{50+i}",
                source_port=5000 + i * 100,
                destination_port=80,
                protocol="TCP",
                bytes=1000000 + i * 100000,
                packets=10000 + i * 1000,
                flow_duration_sec=300.0,
                tos_dscp=46 if i < 2 else 0  # EF for first 2 flows
            )
            flows.append(flow)
        
        return flows
    
    async def validate(self, data: NetFlowData) -> bool:
        """Validate NetFlow data"""
        if not data.source_ip or not data.destination_ip:
            return False
        
        if data.source_port < 0 or data.source_port > 65535:
            return False
        
        if data.tos_dscp < 0 or data.tos_dscp > 63:
            return False
        
        return True


class TelemetryService:
    """Central telemetry collection service"""
    
    def __init__(self):
        """Initialize telemetry service"""
        self.snmp_collector = SNMPCollector()
        self.rtcp_collector = RTCPCollector()
        self.netflow_collector = NetFlowCollector()
        self.last_collection_time: Optional[datetime] = None
        self.collection_count = 0
    
    async def collect_all(self) -> MetricsPayload:
        """Collect metrics from all sources"""
        try:
            # Collect in parallel
            snmp_metrics, rtcp_metrics, netflow_data = await asyncio.gather(
                self.snmp_collector.collect(),
                self.rtcp_collector.collect(),
                self.netflow_collector.collect(),
                return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(snmp_metrics, Exception):
                logger.error(f"SNMP collection error: {snmp_metrics}")
                snmp_metrics = []
            if isinstance(rtcp_metrics, Exception):
                logger.error(f"RTCP collection error: {rtcp_metrics}")
                rtcp_metrics = []
            if isinstance(netflow_data, Exception):
                logger.error(f"NetFlow collection error: {netflow_data}")
                netflow_data = []
            
            # Validate metrics
            snmp_metrics = [m for m in snmp_metrics if asyncio.run(self.snmp_collector.validate(m))]
            rtcp_metrics = [m for m in rtcp_metrics if asyncio.run(self.rtcp_collector.validate(m))]
            netflow_data = [m for m in netflow_data if asyncio.run(self.netflow_collector.validate(m))]
            
            self.last_collection_time = datetime.utcnow()
            self.collection_count += 1
            
            logger.info(
                f"Telemetry collection #{self.collection_count}: "
                f"SNMP={len(snmp_metrics)}, RTCP={len(rtcp_metrics)}, NetFlow={len(netflow_data)}"
            )
            
            return MetricsPayload(
                snmp_metrics=snmp_metrics,
                rtcp_metrics=rtcp_metrics,
                netflow_data=netflow_data
            )
        
        except Exception as e:
            logger.error(f"Fatal error in telemetry collection: {e}", exc_info=True)
            return MetricsPayload()
    
    def register_snmp_device(self, device_id: str, device_ip: str):
        """Register SNMP device"""
        self.snmp_collector.register_device(device_id, device_ip)
    
    def register_rtcp_session(self, session_id: str, source_ip: str, destination_ip: str):
        """Register RTCP session"""
        self.rtcp_collector.register_session(session_id, source_ip, destination_ip)
    
    def unregister_rtcp_session(self, session_id: str):
        """Unregister RTCP session"""
        self.rtcp_collector.unregister_session(session_id)


# Global telemetry service instance
telemetry_service = TelemetryService()


def get_telemetry_service() -> TelemetryService:
    """Get telemetry service instance"""
    return telemetry_service
