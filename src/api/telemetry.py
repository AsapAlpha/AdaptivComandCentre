"""
API Endpoints - Telemetry Collection
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from datetime import datetime

from src.models.schemas import (
    SNMPMetrics, RTCPMetrics, NetFlowData, MetricsPayload
)
from src.core.telemetry.collector import get_telemetry_service

router = APIRouter()
telemetry_service = get_telemetry_service()


@router.post("/snmp", response_model=dict, status_code=status.HTTP_201_CREATED)
async def receive_snmp_metrics(metrics: List[SNMPMetrics]):
    """
    Receive and process SNMP metrics
    
    Args:
        metrics: List of SNMP metrics from network devices
    
    Returns:
        dict: Processing status
    """
    try:
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No metrics provided"
            )
        
        # Validate metrics
        valid_metrics = []
        for metric in metrics:
            if await telemetry_service.snmp_collector.validate(metric):
                valid_metrics.append(metric)
        
        return {
            "status": "success",
            "received": len(metrics),
            "valid": len(valid_metrics),
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing SNMP metrics: {str(e)}"
        )


@router.post("/rtcp", response_model=dict, status_code=status.HTTP_201_CREATED)
async def receive_rtcp_metrics(metrics: List[RTCPMetrics]):
    """
    Receive and process RTCP metrics from RTP sessions
    
    Args:
        metrics: List of RTCP metrics
    
    Returns:
        dict: Processing status
    """
    try:
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No metrics provided"
            )
        
        # Validate metrics
        valid_metrics = []
        for metric in metrics:
            if await telemetry_service.rtcp_collector.validate(metric):
                valid_metrics.append(metric)
        
        return {
            "status": "success",
            "received": len(metrics),
            "valid": len(valid_metrics),
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing RTCP metrics: {str(e)}"
        )


@router.post("/netflow", response_model=dict, status_code=status.HTTP_201_CREATED)
async def receive_netflow_data(flows: List[NetFlowData]):
    """
    Receive and process NetFlow data
    
    Args:
        flows: List of NetFlow records
    
    Returns:
        dict: Processing status
    """
    try:
        if not flows:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No flows provided"
            )
        
        # Validate flows
        valid_flows = []
        for flow in flows:
            if await telemetry_service.netflow_collector.validate(flow):
                valid_flows.append(flow)
        
        return {
            "status": "success",
            "received": len(flows),
            "valid": len(valid_flows),
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing NetFlow data: {str(e)}"
        )


@router.post("/batch", response_model=dict, status_code=status.HTTP_201_CREATED)
async def receive_batch_metrics(payload: MetricsPayload):
    """
    Receive batch of metrics from multiple sources
    
    Args:
        payload: Metrics payload containing SNMP, RTCP, and NetFlow data
    
    Returns:
        dict: Processing status for each metric type
    """
    try:
        results = {
            "snmp_received": len(payload.snmp_metrics) if payload.snmp_metrics else 0,
            "rtcp_received": len(payload.rtcp_metrics) if payload.rtcp_metrics else 0,
            "netflow_received": len(payload.netflow_data) if payload.netflow_data else 0,
            "timestamp": datetime.utcnow()
        }
        
        # Process each metric type
        if payload.snmp_metrics:
            valid_snmp = []
            for metric in payload.snmp_metrics:
                if await telemetry_service.snmp_collector.validate(metric):
                    valid_snmp.append(metric)
            results["snmp_valid"] = len(valid_snmp)
        
        if payload.rtcp_metrics:
            valid_rtcp = []
            for metric in payload.rtcp_metrics:
                if await telemetry_service.rtcp_collector.validate(metric):
                    valid_rtcp.append(metric)
            results["rtcp_valid"] = len(valid_rtcp)
        
        if payload.netflow_data:
            valid_flows = []
            for flow in payload.netflow_data:
                if await telemetry_service.netflow_collector.validate(flow):
                    valid_flows.append(flow)
            results["netflow_valid"] = len(valid_flows)
        
        results["status"] = "success"
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing batch metrics: {str(e)}"
        )


@router.get("/collect", response_model=MetricsPayload)
async def collect_all_metrics():
    """
    Trigger telemetry collection from all sources
    
    Returns:
        MetricsPayload: Collected metrics from all sources
    """
    try:
        payload = await telemetry_service.collect_all()
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error collecting metrics: {str(e)}"
        )


@router.post("/device/register", response_model=dict)
async def register_snmp_device(device_id: str, device_ip: str):
    """
    Register a device for SNMP monitoring
    
    Args:
        device_id: Unique device identifier
        device_ip: IP address of the device
    
    Returns:
        dict: Registration status
    """
    try:
        telemetry_service.register_snmp_device(device_id, device_ip)
        return {
            "status": "registered",
            "device_id": device_id,
            "device_ip": device_ip,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering device: {str(e)}"
        )


@router.post("/session/register", response_model=dict)
async def register_rtcp_session(session_id: str, source_ip: str, destination_ip: str):
    """
    Register an RTP session for RTCP monitoring
    
    Args:
        session_id: Unique session identifier
        source_ip: Source IP address
        destination_ip: Destination IP address
    
    Returns:
        dict: Registration status
    """
    try:
        telemetry_service.register_rtcp_session(session_id, source_ip, destination_ip)
        return {
            "status": "registered",
            "session_id": session_id,
            "source_ip": source_ip,
            "destination_ip": destination_ip,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering session: {str(e)}"
        )


@router.delete("/session/{session_id}", response_model=dict)
async def unregister_rtcp_session(session_id: str):
    """
    Unregister an RTP session
    
    Args:
        session_id: Session identifier to unregister
    
    Returns:
        dict: Unregistration status
    """
    try:
        telemetry_service.unregister_rtcp_session(session_id)
        return {
            "status": "unregistered",
            "session_id": session_id,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error unregistering session: {str(e)}"
        )


@router.get("/status", response_model=dict)
async def telemetry_status():
    """
    Get telemetry service status
    
    Returns:
        dict: Service status and statistics
    """
    return {
        "status": "operational",
        "collection_count": telemetry_service.collection_count,
        "last_collection": telemetry_service.last_collection_time,
        "snmp_devices": len(telemetry_service.snmp_collector.devices),
        "rtcp_sessions": len(telemetry_service.rtcp_collector.active_sessions),
        "timestamp": datetime.utcnow()
    }
