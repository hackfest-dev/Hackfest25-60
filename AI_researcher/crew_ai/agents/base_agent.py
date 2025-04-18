import threading
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable

from crew_ai.utils.messaging import MessageBroker
from crew_ai.models.llm_client import LLMClient, get_llm_client
from crew_ai.config.config import Config, LLMProvider

class BaseAgent(ABC):
    """Base class for all agents in the Crew AI framework."""
    
    def __init__(self, agent_id: Optional[str] = None, 
                 llm_client: Optional[LLMClient] = None,
                 llm_provider: Optional[LLMProvider] = None,
                 message_broker: Optional[MessageBroker] = None):
        """Initialize the base agent."""
        self.agent_id = agent_id or str(uuid.uuid4())
        self.llm_client = llm_client or get_llm_client(llm_provider)
        self.message_broker = message_broker or MessageBroker()
        
        # Initialize agent-specific queue
        self.queue_name = f"agent_{self.agent_id}"
        self.message_broker.create_queue(self.queue_name, [self.queue_name])
        
        # Start message consumer thread
        self.consumer_thread = self.message_broker.start_consumer_thread(
            self.queue_name, self._process_message
        )
        
        # Message handlers
        self.message_handlers = {}
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default message handlers."""
        self.register_handler("ping", self._handle_ping)
        self.register_handler("stop", self._handle_stop)
    
    def register_handler(self, message_type: str, handler: Callable):
        """Register a message handler."""
        self.message_handlers[message_type] = handler
    
    def _process_message(self, message: Dict[str, Any], correlation_id: str):
        """Process incoming messages."""
        message_type = message.get("type")
        
        if message_type in self.message_handlers:
            try:
                response = self.message_handlers[message_type](message, correlation_id)
                
                # If there's a reply_to in the message, send a response
                if "reply_to" in message:
                    self.message_broker.publish_message(
                        message["reply_to"],
                        {
                            "type": f"{message_type}_response",
                            "status": "success",
                            "data": response,
                            "agent_id": self.agent_id
                        },
                        correlation_id
                    )
            except Exception as e:
                print(f"Error processing message: {e}")
                
                # If there's a reply_to in the message, send an error response
                if "reply_to" in message:
                    self.message_broker.publish_message(
                        message["reply_to"],
                        {
                            "type": f"{message_type}_response",
                            "status": "error",
                            "error": str(e),
                            "agent_id": self.agent_id
                        },
                        correlation_id
                    )
        else:
            print(f"Unknown message type: {message_type}")
    
    def _handle_ping(self, message: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Handle ping messages."""
        return {"status": "alive", "agent_id": self.agent_id, "agent_type": self.__class__.__name__}
    
    def _handle_stop(self, message: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Handle stop messages."""
        self.stop()
        return {"status": "stopped", "agent_id": self.agent_id}
    
    def send_message(self, target_agent_id: str, message_type: str, 
                    data: Dict[str, Any], wait_for_response: bool = False,
                    timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Send a message to another agent."""
        message = {
            "type": message_type,
            "data": data,
            "agent_id": self.agent_id,
        }
        
        if wait_for_response:
            # Create a temporary queue for the response
            temp_queue = f"response_{uuid.uuid4()}"
            self.message_broker.create_queue(temp_queue, [temp_queue])
            
            # Add reply_to to the message
            message["reply_to"] = temp_queue
            
            # Create a response event
            response_event = threading.Event()
            response_data = [None]
            
            # Define response handler
            def response_handler(resp_message, resp_correlation_id):
                response_data[0] = resp_message
                response_event.set()
            
            # Start temporary consumer for the response
            temp_consumer = self.message_broker.start_consumer_thread(
                temp_queue, response_handler
            )
            
            # Send the message
            correlation_id = str(uuid.uuid4())
            self.message_broker.publish_message(
                f"agent_{target_agent_id}", message, correlation_id
            )
            
            # Wait for response
            if response_event.wait(timeout):
                return response_data[0]
            else:
                return {"status": "error", "error": "Timeout waiting for response"}
        else:
            # Send the message without waiting for response
            correlation_id = str(uuid.uuid4())
            self.message_broker.publish_message(
                f"agent_{target_agent_id}", message, correlation_id
            )
            return None
    
    def broadcast_message(self, message_type: str, data: Dict[str, Any]):
        """Broadcast a message to all agents."""
        message = {
            "type": message_type,
            "data": data,
            "agent_id": self.agent_id,
        }
        
        correlation_id = str(uuid.uuid4())
        self.message_broker.publish_message(
            "broadcast", message, correlation_id
        )
    
    def stop(self):
        """Stop the agent."""
        # Close message broker connection
        self.message_broker.close()
    
    @abstractmethod
    def run(self, *args, **kwargs):
        """Run the agent's main task."""
        pass
