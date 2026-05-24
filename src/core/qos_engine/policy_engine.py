"""
QoS Policy Engine
Manages and applies Quality of Service policies to network devices
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
from enum import Enum

from src.models.schemas import (
    QoSPolicy, QoSPolicyRule, PolicyAction, PolicyActionType,
    TrafficClass, SNMPMetrics, RTCPMetrics
)
from src.config.settings import settings

logger = logging.getLogger(__name__)


class QoSPolicyEngine:
    """Engine for managing QoS policies"""
    
    def __init__(self):
        """Initialize QoS policy engine"""
        self.policies: Dict[str, QoSPolicy] = {}
        self.active_policies: Dict[str, QoSPolicy] = {}
        self.last_policy_update: Dict[str, datetime] = {}
        self.policy_change_count: Dict[str, int] = {}
        self.debounce_timers: Dict[str, datetime] = {}
    
    def create_policy(self, policy: QoSPolicy) -> bool:
        """Create a new QoS policy"""
        try:
            if policy.policy_id in self.policies:
                logger.warning(f"Policy {policy.policy_id} already exists")
                return False
            
            self.policies[policy.policy_id] = policy
            logger.info(f"Created QoS policy: {policy.policy_id} ({policy.name})")
            return True
        except Exception as e:
            logger.error(f"Error creating policy: {e}")
            return False
    
    def delete_policy(self, policy_id: str) -> bool:
        """Delete a QoS policy"""
        try:
            if policy_id not in self.policies:
                logger.warning(f"Policy {policy_id} not found")
                return False
            
            del self.policies[policy_id]
            if policy_id in self.active_policies:
                del self.active_policies[policy_id]
            
            logger.info(f"Deleted QoS policy: {policy_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting policy: {e}")
            return False
    
    def update_policy(self, policy_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing QoS policy"""
        try:
            if policy_id not in self.policies:
                logger.warning(f"Policy {policy_id} not found")
                return False
            
            policy = self.policies[policy_id]
            
            # Update fields
            if "name" in updates:
                policy.name = updates["name"]
            if "description" in updates:
                policy.description = updates["description"]
            if "enabled" in updates:
                policy.enabled = updates["enabled"]
            if "rules" in updates:
                policy.rules = updates["rules"]
            
            policy.updated_at = datetime.utcnow()
            
            logger.info(f"Updated QoS policy: {policy_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating policy: {e}")
            return False
    
    def get_policy(self, policy_id: str) -> Optional[QoSPolicy]:
        """Get a QoS policy by ID"""
        return self.policies.get(policy_id)
    
    def list_policies(self, device_id: Optional[str] = None) -> List[QoSPolicy]:
        """List all policies, optionally filtered by device"""
        if device_id:
            return [p for p in self.policies.values() if p.device_id == device_id]
        return list(self.policies.values())
    
    def apply_policy(self, policy_id: str) -> bool:
        """Apply a QoS policy"""
        try:
            policy = self.policies.get(policy_id)
            if not policy:
                logger.warning(f"Policy {policy_id} not found")
                return False
            
            if not policy.enabled:
                logger.warning(f"Policy {policy_id} is disabled")
                return False
            
            # Check validity period
            now = datetime.utcnow()
            if policy.valid_from and now < policy.valid_from:
                logger.warning(f"Policy {policy_id} is not yet valid")
                return False
            if policy.valid_to and now > policy.valid_to:
                logger.warning(f"Policy {policy_id} has expired")
                return False
            
            self.active_policies[policy_id] = policy
            self.last_policy_update[policy_id] = now
            
            logger.info(f"Applied QoS policy: {policy_id}")
            return True
        except Exception as e:
            logger.error(f"Error applying policy: {e}")
            return False
    
    def should_update_policy(self, device_id: str) -> bool:
        """Check if policy should be updated for device"""
        if device_id not in self.last_policy_update:
            return True
        
        last_update = self.last_policy_update[device_id]
        time_since_update = (datetime.utcnow() - last_update).total_seconds()
        
        if time_since_update < settings.QOS_POLICY_UPDATE_INTERVAL_SEC:
            return False
        
        # Check debounce timer
        if device_id in self.debounce_timers:
            if datetime.utcnow() < self.debounce_timers[device_id]:
                return False
        
        # Check hourly change limit
        if device_id not in self.policy_change_count:
            self.policy_change_count[device_id] = 0
        
        if self.policy_change_count[device_id] >= settings.QOS_MAX_POLICY_CHANGES_PER_HOUR:
            logger.warning(f"Policy change limit reached for {device_id}")
            return False
        
        return True
    
    def record_policy_change(self, device_id: str):
        """Record a policy change"""
        if device_id not in self.policy_change_count:
            self.policy_change_count[device_id] = 0
        
        self.policy_change_count[device_id] += 1
        
        # Set debounce timer
        self.debounce_timers[device_id] = datetime.utcnow() + timedelta(
            seconds=settings.QOS_CHANGE_DEBOUNCE_SEC
        )


class QoSDecisionEngine:
    """Decision engine for QoS actions based on metrics"""
    
    def __init__(self, policy_engine: QoSPolicyEngine):
        """Initialize decision engine"""
        self.policy_engine = policy_engine
        self.action_history: List[PolicyAction] = []
    
    async def analyze_metrics(self, snmp_metrics: List[SNMPMetrics],
                             rtcp_metrics: List[RTCPMetrics]) -> List[PolicyAction]:
        """Analyze metrics and generate policy actions"""
        actions = []
        
        # Analyze jitter
        jitter_actions = await self._analyze_jitter(rtcp_metrics)
        actions.extend(jitter_actions)
        
        # Analyze packet loss
        loss_actions = await self._analyze_packet_loss(rtcp_metrics)
        actions.extend(loss_actions)
        
        # Analyze buffer
        buffer_actions = await self._analyze_buffer(snmp_metrics)
        actions.extend(buffer_actions)
        
        # Analyze bandwidth utilization
        bw_actions = await self._analyze_bandwidth(snmp_metrics)
        actions.extend(bw_actions)
        
        # Record actions
        self.action_history.extend(actions)
        
        logger.info(f"Generated {len(actions)} policy actions from metrics")
        return actions
    
    async def _analyze_jitter(self, rtcp_metrics: List[RTCPMetrics]) -> List[PolicyAction]:
        """Analyze jitter and generate actions"""
        actions = []
        
        for metric in rtcp_metrics:
            if metric.jitter_ms > settings.JITTER_THRESHOLD_MS:
                action = PolicyAction(
                    action_type=PolicyActionType.INCREASE_PRIORITY,
                    target_device_id="edge-router-1",  # Would be determined dynamically
                    priority=1,
                    parameters={
                        "traffic_class": TrafficClass.EF,
                        "guaranteed_bandwidth_percent": 30,
                        "dscp_value": 46
                    },
                    reason=f"Jitter {metric.jitter_ms}ms exceeds threshold {settings.JITTER_THRESHOLD_MS}ms"
                )
                actions.append(action)
                logger.warning(f"High jitter detected: {metric.jitter_ms}ms for session {metric.session_id}")
        
        return actions
    
    async def _analyze_packet_loss(self, rtcp_metrics: List[RTCPMetrics]) -> List[PolicyAction]:
        """Analyze packet loss and generate actions"""
        actions = []
        
        for metric in rtcp_metrics:
            if metric.packet_loss_percent > settings.PACKET_LOSS_THRESHOLD_PERCENT:
                action = PolicyAction(
                    action_type=PolicyActionType.ENABLE_AQM,
                    target_device_id="aggregation-switch-1",
                    priority=2,
                    parameters={
                        "algorithm": "WRED",
                        "early_threshold_percent": 70,
                        "max_threshold_percent": 100
                    },
                    reason=f"Packet loss {metric.packet_loss_percent}% exceeds threshold {settings.PACKET_LOSS_THRESHOLD_PERCENT}%"
                )
                actions.append(action)
                logger.warning(f"High packet loss detected: {metric.packet_loss_percent}% for session {metric.session_id}")
        
        return actions
    
    async def _analyze_buffer(self, snmp_metrics: List[SNMPMetrics]) -> List[PolicyAction]:
        """Analyze buffer utilization and generate actions"""
        actions = []
        
        for metric in snmp_metrics:
            if metric.buffer_utilization_percent > settings.BUFFER_FILL_THRESHOLD_PERCENT:
                action = PolicyAction(
                    action_type=PolicyActionType.ENABLE_AQM,
                    target_device_id=metric.device_id,
                    priority=1,
                    parameters={
                        "algorithm": "CoDel",
                        "target_delay_ms": 5,
                        "interval_ms": 100
                    },
                    reason=f"Buffer fill {metric.buffer_utilization_percent}% exceeds threshold {settings.BUFFER_FILL_THRESHOLD_PERCENT}%"
                )
                actions.append(action)
                logger.warning(f"High buffer utilization on {metric.device_id}: {metric.buffer_utilization_percent}%")
        
        return actions
    
    async def _analyze_bandwidth(self, snmp_metrics: List[SNMPMetrics]) -> List[PolicyAction]:
        """Analyze bandwidth utilization and generate actions"""
        actions = []
        
        for metric in snmp_metrics:
            if metric.bandwidth_utilization_percent > 80:
                action = PolicyAction(
                    action_type=PolicyActionType.SCALE_VNF,
                    target_device_id=metric.device_id,
                    priority=3,
                    parameters={
                        "vnf_type": "vShaper",
                        "action": "scale_out",
                        "replicas": 2
                    },
                    reason=f"Bandwidth utilization {metric.bandwidth_utilization_percent}% is high"
                )
                actions.append(action)
                logger.info(f"High bandwidth on {metric.device_id}: {metric.bandwidth_utilization_percent}%")
        
        return actions
    
    def get_action_history(self, limit: int = 100) -> List[PolicyAction]:
        """Get recent policy actions"""
        return self.action_history[-limit:]


class QoSPolicyManager:
    """High-level QoS management"""
    
    def __init__(self):
        """Initialize QoS manager"""
        self.policy_engine = QoSPolicyEngine()
        self.decision_engine = QoSDecisionEngine(self.policy_engine)
    
    async def process_metrics(self, snmp_metrics: List[SNMPMetrics],
                             rtcp_metrics: List[RTCPMetrics]) -> List[PolicyAction]:
        """Process metrics and generate actions"""
        return await self.decision_engine.analyze_metrics(snmp_metrics, rtcp_metrics)


# Global QoS manager instance
qos_manager = QoSPolicyManager()


def get_qos_manager() -> QoSPolicyManager:
    """Get QoS manager instance"""
    return qos_manager
