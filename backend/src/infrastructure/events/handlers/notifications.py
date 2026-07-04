"""
Notification Handlers for real-time updates.

These handlers send WebSocket notifications to connected clients
when events occur that they should be aware of.
"""

import logging
from typing import Dict, Any, Set, Optional
from uuid import UUID
from datetime import datetime
import json

# WebSocket manager would be imported here
# from src.api.websocket.manager import WebSocketManager

from src.domain.shared.events import DomainEvent
from src.domain.experiments.events import ExperimentStarted, MetricLogged
from src.domain.notebooks.events import NotebookUpdated

logger = logging.getLogger(__name__)


class NotificationHandler:
    """
    Sends real-time notifications via WebSocket.
    
    Notifications are sent to:
    - Organization members (broadcast)
    - Specific users (targeted)
    - Project members (scoped)
    """
    
    def __init__(self, websocket_manager = None):
        # self.ws_manager = websocket_manager or WebSocketManager()
        self.ws_manager = None  # Placeholder for now
        
    async def handle_experiment_started(self, event: ExperimentStarted) -> None:
        """
        Notify organization about new experiment.
        
        Sends broadcast to organization members.
        """
        if not self.ws_manager:
            return
        
        notification = {
            "type": "experiment.started",
            "experiment_id": str(event.experiment_id),
            "name": event.name,
            "project_id": str(event.project_id),
            "started_by": str(event.created_by),
            "timestamp": event.timestamp.isoformat(),
        }
        
        try:
            # Broadcast to organization
            await self.ws_manager.broadcast_to_organization(
                organization_id=event.organization_id,
                message=json.dumps(notification),
                event_type="experiment.started"
            )
            
            logger.debug(
                f"Sent experiment started notification for {event.experiment_id}"
            )
            
        except Exception as e:
            logger.error(
                f"Error sending experiment started notification: {e}"
            )
            # Don't raise - notifications shouldn't block event processing
    
    async def handle_metric_logged(self, event: MetricLogged) -> None:
        """
        Send real-time metric updates.
        
        Sends to users watching the specific experiment/run.
        """
        if not self.ws_manager:
            return
        
        notification = {
            "type": "metric.logged",
            "run_id": str(event.run_id),
            "experiment_id": str(event.experiment_id),
            "key": event.key,
            "value": event.value,
            "step": event.step,
            "timestamp": event.timestamp.isoformat(),
        }
        
        try:
            # Send to users subscribed to this run
            await self.ws_manager.send_to_run_subscribers(
                run_id=event.run_id,
                message=json.dumps(notification),
                event_type="metric.logged"
            )
            
            logger.debug(
                f"Sent metric update for run {event.run_id}, key {event.key}"
            )
            
        except Exception as e:
            logger.error(
                f"Error sending metric notification: {e}"
            )
    
    async def handle_notebook_updated(self, event: NotebookUpdated) -> None:
        """
        Notify about notebook changes.
        
        Sends to users watching the notebook.
        """
        if not self.ws_manager:
            return
        
        notification = {
            "type": "notebook.updated",
            "notebook_id": str(event.notebook_id),
            "operation": event.operation,
            "block_id": str(event.block_id) if event.block_id else None,
            "timestamp": event.timestamp.isoformat(),
        }
        
        try:
            # Send to notebook collaborators
            await self.ws_manager.send_to_notebook_collaborators(
                notebook_id=event.notebook_id,
                message=json.dumps(notification),
                event_type="notebook.updated"
            )
            
            logger.debug(
                f"Sent notebook update notification for {event.notebook_id}"
            )
            
        except Exception as e:
            logger.error(
                f"Error sending notebook notification: {e}"
            )
    
    async def handle_generic_event(self, event: DomainEvent) -> None:
        """
        Send generic event notifications.
        
        Used for audit trail and system notifications.
        """
        if not self.ws_manager:
            return
        
        notification = {
            "type": "system.event",
            "event_id": str(event.event_id),
            "event_type": event.event_type,
            "aggregate_type": event.aggregate_type,
            "timestamp": event.timestamp.isoformat(),
        }
        
        try:
            # Send to system admins
            organization_id = getattr(event, 'organization_id', None)
            if organization_id:
                await self.ws_manager.send_to_organization_admins(
                    organization_id=organization_id,
                    message=json.dumps(notification),
                    event_type="system.event"
                )
            
            logger.debug(
                f"Sent system notification for event {event.event_id}"
            )
            
        except Exception as e:
            logger.error(
                f"Error sending system notification: {e}"
            )


class NotificationManager:
    """
    Manages notification routing and delivery.
    
    Routes events to appropriate notification handlers and manages
    notification preferences and delivery channels.
    """
    
    def __init__(self, websocket_manager = None):
        self.handlers = NotificationHandler(websocket_manager)
        
        # Event type to handler mapping
        self.handler_map: Dict[str, callable] = {
            "experiment.started": self.handlers.handle_experiment_started,
            "metric.logged": self.handlers.handle_metric_logged,
            "notebook.updated": self.handlers.handle_notebook_updated,
        }
        
        # Notification preferences per user/organization
        self.preferences: Dict[str, Set[str]] = {}
    
    async def handle_event(self, event: DomainEvent) -> None:
        """
        Route event to notification handlers.
        
        Checks notification preferences before sending.
        """
        handler = self.handler_map.get(event.event_type)
        
        if handler:
            logger.info(
                f"Routing event {event.event_id} ({event.event_type}) "
                f"for notification"
            )
            
            # Check if notifications are enabled for this event type
            if self._notifications_enabled(event):
                await handler(event)
            
        else:
            # Handle generic events
            await self.handlers.handle_generic_event(event)
    
    def _notifications_enabled(self, event: DomainEvent) -> bool:
        """
        Check if notifications are enabled for this event.
        
        In production, this would check user/organization preferences.
        """
        organization_id = getattr(event, 'organization_id', None)
        if not organization_id:
            return True  # Default to enabled
        
        org_key = f"org:{organization_id}"
        
        # Check if event type is in blocked list
        blocked_events = self.preferences.get(f"{org_key}:blocked", set())
        
        if event.event_type in blocked_events:
            logger.debug(
                f"Notifications blocked for {event.event_type} "
                f"in organization {organization_id}"
            )
            return False
        
        return True
    
    async def update_preferences(
        self,
        organization_id: UUID,
        user_id: Optional[UUID] = None,
        preferences: Dict[str, Any] = None
    ) -> None:
        """
        Update notification preferences.
        
        Args:
            organization_id: Organization ID
            user_id: User ID (optional, for user-specific preferences)
            preferences: Dictionary of preference settings
        """
        if preferences is None:
            preferences = {}
            
        key = f"org:{organization_id}"
        if user_id:
            key = f"{key}:user:{user_id}"
        
        # Update in-memory preferences
        if "blocked_events" in preferences:
            self.preferences[f"{key}:blocked"] = set(preferences["blocked_events"])
        
        logger.info(f"Updated notification preferences for {key}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for notification manager"""
        ws_connected = self.handlers.ws_manager is not None
        
        return {
            "status": "healthy" if ws_connected else "degraded",
            "websocket_connected": ws_connected,
            "handlers_registered": len(self.handler_map),
            "timestamp": datetime.utcnow().isoformat()
        }