"""
Data Models for Telemetry, QoS, and Alerts
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== Enums ====================

class TrafficClass(str, Enum):
    """Traffic classification"""
    EF = "EF"  # Expedited Forwarding (real-time)
    AF41 = "AF41"  # Assured Forwarding (video)
    AF31 = "AF31"  # Assured Forwarding (voice)
    BE = "BE"  # Best Effort (background)


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class CommandStatus(str, Enum):
    """Command execution status"""
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class PolicyActionType(str, Enum):
    """QoS policy action types"""
    INCREASE_PRIORITY = "increase_priority"
    DECREASE_PRIORITY = "decrease_priority"
    INCREASE_BANDWIDTH = "increase_bandwidth"
    DECREASE_BANDWIDTH = "decrease_bandwidth"
    ENABLE_AQM = "enable_aqm"
    SCALE_VNF = "scale_vnf"
    REROUTE = "reroute"
    ENABLE_GDR = "enable_gdr"


# ==================== Telemetry Models ====================

class SNMPMetrics(BaseModel):
    """SNMP collected metrics"""
    device_id: str = Field(..., description="Network device identifier")
    device_name: str = Field(..., description="Device name")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    port_id: str
    interface_name: str
    
    # Traffic metrics
    bytes_in: int = 0
    bytes_out: int = 0
    packets_in: int = 0
    packets_out: int = 0
    dropped_packets: int = 0
    error_packets: int = 0
    
    # Queue metrics
    queue_length: int = 0
    buffer_utilization_percent: float = Field(0.0, ge=0, le=100)
    
    # Performance metrics
    bandwidth_utilization_percent: float = Field(0.0, ge=0, le=100)
    cpu_utilization_percent: float = Field(0.0, ge=0, le=100)
    memory_utilization_percent: float = Field(0.0, ge=0, le=100)


class RTCPMetrics(BaseModel):
    """RTCP collected metrics for RTP streams"""
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Delay metrics
    round_trip_delay_ms: float = Field(0.0, ge=0)
    one_way_delay_ms: float = Field(0.0, ge=0)
    jitter_ms: float = Field(0.0, ge=0)
    
    # Loss metrics
    packet_loss_percent: float = Field(0.0, ge=0, le=100)
    packets_lost: int = 0
    
    # Quality metrics
    mos_score: float = Field(4.0, ge=1, le=5)  # Mean Opinion Score
    video_artifacts: bool = False


class NetFlowData(BaseModel):
    """NetFlow v5/v9 collected data"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_ip: str
    destination_ip: str
    source_port: int
    destination_port: int
    protocol: str
    bytes: int
    packets: int
    flow_duration_sec: float
    tos_dscp: int  # DSCP value


class MetricsPayload(BaseModel):
    """Batch metrics payload"""
    snmp_metrics: Optional[List[SNMPMetrics]] = []
    rtcp_metrics: Optional[List[RTCPMetrics]] = []
    netflow_data: Optional[List[NetFlowData]] = []


# ==================== QoS Policy Models ====================

class QoSPolicyRule(BaseModel):
    """Individual QoS policy rule"""
    rule_id: str
    traffic_class: TrafficClass
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    protocol: Optional[str] = None
    priority: int = Field(0, ge=0, le=7)
    guaranteed_bandwidth_percent: float = Field(0.0, ge=0, le=100)
    maximum_bandwidth_percent: float = Field(100.0, ge=0, le=100)
    dscp_value: int = Field(0, ge=0, le=63)


class QoSPolicy(BaseModel):
    """Complete QoS policy"""
    policy_id: str = Field(..., description="Unique policy identifier")
    name: str = Field(..., description="Policy name")
    description: Optional[str] = None
    enabled: bool = True
    device_id: str = Field(..., description="Target device ID")
    rules: List[QoSPolicyRule] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None


class QoSPolicyUpdate(BaseModel):
    """QoS policy update request"""
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    rules: Optional[List[QoSPolicyRule]] = None


# ==================== Decision & Command Models ====================

class PolicyAction(BaseModel):
    """Action to be taken by decision engine"""
    action_id: str = Field(default_factory=lambda: f"action_{datetime.utcnow().timestamp()}")
    action_type: PolicyActionType
    target_device_id: str
    priority: int = Field(1, ge=1, le=10)  # 1 = highest priority
    parameters: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    reason: str = Field(..., description="Reason for this action")


class NetworkCommand(BaseModel):
    """Network command to be executed"""
    command_id: str = Field(default_factory=lambda: f"cmd_{datetime.utcnow().timestamp()}")
    device_id: str
    command_type: str  # e.g., "qos_update", "scale_vnf", "reroute"
    payload: Dict[str, Any]
    status: CommandStatus = CommandStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    result: Optional[str] = None


class VNFScalingCommand(BaseModel):
    """Virtual Network Function scaling command"""
    vnf_id: str
    action: str = Field(..., description="scale_out or scale_in")
    replicas: int = Field(1, ge=1)
    timeout_sec: int = 300


class RemoteDeviceCommand(BaseModel):
    """TR-069 remote device command"""
    device_serial: str
    command_type: str  # "reboot", "update_firmware", "get_config", etc.
    parameters: Dict[str, Any] = {}


# ==================== Alert Models ====================

class Alert(BaseModel):
    """Alert/Incident notification"""
    alert_id: str = Field(default_factory=lambda: f"alert_{datetime.utcnow().timestamp()}")
    severity: AlertSeverity
    title: str = Field(..., description="Alert title")
    description: str = Field(..., description="Detailed description")
    device_id: Optional[str] = None
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    tags: List[str] = []
    related_actions: List[str] = []  # IDs of related policy actions


class AlertFilter(BaseModel):
    """Alert filtering criteria"""
    severity: Optional[AlertSeverity] = None
    device_id: Optional[str] = None
    acknowledged: Optional[bool] = None
    resolved: Optional[bool] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


# ==================== Analytics Models ====================

class LoadForecast(BaseModel):
    """Load forecast prediction"""
    forecast_id: str = Field(default_factory=lambda: f"forecast_{datetime.utcnow().timestamp()}")
    device_id: str
    metric_type: str  # "bandwidth", "jitter", "packet_loss", etc.
    forecast_timestamp: datetime
    predicted_value: float
    confidence_interval: float = Field(0.95, ge=0, le=1)
    lower_bound: float
    upper_bound: float


class AnomalyDetection(BaseModel):
    """Anomaly detection result"""
    anomaly_id: str = Field(default_factory=lambda: f"anomaly_{datetime.utcnow().timestamp()}")
    device_id: str
    metric_name: str
    detected_at: datetime
    anomaly_score: float = Field(0.0, ge=0, le=1)  # 0=normal, 1=definitely anomaly
    expected_value: float
    actual_value: float
    deviation_percent: float


class SLAReport(BaseModel):
    """Service Level Agreement compliance report"""
    report_id: str
    period_start: datetime
    period_end: datetime
    device_id: str
    
    # SLA metrics
    availability_percent: float = Field(99.99, ge=0, le=100)
    jitter_ms_avg: float = 0.0
    jitter_ms_max: float = 0.0
    delay_ms_avg: float = 0.0
    delay_ms_max: float = 0.0
    packet_loss_percent: float = 0.0
    
    # Compliance
    compliant: bool = True
    compliance_percent: float = 100.0


# ==================== Health Check Models ====================

class HealthStatus(BaseModel):
    """System health status"""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    components: Dict[str, str] = {}
    metrics: Dict[str, Any] = {}
