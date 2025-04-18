import pika
import json
import uuid
import threading
import time
from typing import Dict, Any, Callable, Optional
from crew_ai.config.config import Config
import os

class MessageBroker:
    """Message broker for agent communication using RabbitMQ."""
    
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None, 
                user: Optional[str] = None, password: Optional[str] = None,
                use_mock: bool = False):
        self.host = host or Config.RABBITMQ_HOST
        self.port = port or Config.RABBITMQ_PORT
        self.user = user or Config.RABBITMQ_USER
        self.password = password or Config.RABBITMQ_PASSWORD
        self.use_mock = use_mock or os.getenv("USE_MOCK_BROKER", "false").lower() == "true"
        
        self.connection = None
        self.channel = None
        
        if not self.use_mock:
            try:
                self._connect()
                
                # Declare common exchanges
                self.channel.exchange_declare(
                    exchange='agent_messages',
                    exchange_type='topic',
                    durable=True
                )
            except Exception as e:
                print(f"Warning: Could not connect to RabbitMQ: {e}")
                print("Falling back to mock message broker")
                self.use_mock = True
        
        # Initialize mock message storage if using mock
        if self.use_mock:
            self.mock_queues = {}
            self.mock_messages = {}
            print("Using mock message broker")
    
    def _connect(self):
        """Connect to RabbitMQ server."""
        if self.use_mock:
            return
            
        credentials = pika.PlainCredentials(self.user, self.password)
        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
    
    def close(self):
        """Close the connection to RabbitMQ."""
        if not self.use_mock and self.connection and self.connection.is_open:
            self.connection.close()
    
    def publish_message(self, routing_key: str, message: Dict[str, Any], 
                       correlation_id: Optional[str] = None):
        """Publish a message to the exchange."""
        if self.use_mock:
            # Store message in mock storage
            if routing_key not in self.mock_messages:
                self.mock_messages[routing_key] = []
            
            self.mock_messages[routing_key].append({
                "message": message,
                "correlation_id": correlation_id or str(uuid.uuid4()),
                "timestamp": time.time()
            })
            
            # Deliver to any bound queues
            for queue_name, bindings in self.mock_queues.items():
                if routing_key in bindings:
                    if queue_name not in self.mock_messages:
                        self.mock_messages[queue_name] = []
                    
                    self.mock_messages[queue_name].append({
                        "message": message,
                        "correlation_id": correlation_id or str(uuid.uuid4()),
                        "timestamp": time.time()
                    })
            
            return
            
        if not self.connection or self.connection.is_closed:
            self._connect()
        
        properties = pika.BasicProperties(
            content_type='application/json',
            delivery_mode=2,  # Persistent message
            correlation_id=correlation_id or str(uuid.uuid4())
        )
        
        self.channel.basic_publish(
            exchange='agent_messages',
            routing_key=routing_key,
            body=json.dumps(message),
            properties=properties
        )
    
    def create_queue(self, queue_name: str, routing_keys: list):
        """Create a queue and bind it to the exchange with routing keys."""
        if self.use_mock:
            # Create mock queue
            self.mock_queues[queue_name] = routing_keys
            if queue_name not in self.mock_messages:
                self.mock_messages[queue_name] = []
            return
            
        if not self.connection or self.connection.is_closed:
            self._connect()
        
        self.channel.queue_declare(queue=queue_name, durable=True)
        
        for routing_key in routing_keys:
            self.channel.queue_bind(
                exchange='agent_messages',
                queue=queue_name,
                routing_key=routing_key
            )
    
    def consume_messages(self, queue_name: str, callback: Callable):
        """Consume messages from a queue."""
        if self.use_mock:
            # In mock mode, this is a no-op as we handle message delivery differently
            return
            
        if not self.connection or self.connection.is_closed:
            self._connect()
        
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback,
            auto_ack=False
        )
        
        self.channel.start_consuming()
    
    def start_consumer_thread(self, queue_name: str, callback: Callable):
        """Start a consumer thread for the queue."""
        if self.use_mock:
            # Start a mock consumer thread
            consumer_thread = threading.Thread(
                target=self._mock_consumer_thread,
                args=(queue_name, callback),
                daemon=True
            )
            consumer_thread.start()
            return consumer_thread
            
        consumer_thread = threading.Thread(
            target=self._consumer_thread,
            args=(queue_name, callback),
            daemon=True
        )
        consumer_thread.start()
        return consumer_thread
    
    def _mock_consumer_thread(self, queue_name: str, callback: Callable):
        """Mock consumer thread function."""
        # Create queue if it doesn't exist
        if queue_name not in self.mock_messages:
            self.mock_messages[queue_name] = []
        
        # Process messages in a loop
        while True:
            # Check if there are messages in the queue
            if queue_name in self.mock_messages and self.mock_messages[queue_name]:
                # Get the first message
                message_data = self.mock_messages[queue_name].pop(0)
                
                # Call the callback
                try:
                    callback(message_data["message"], message_data["correlation_id"])
                except Exception as e:
                    print(f"Error processing mock message: {e}")
            
            # Sleep to avoid busy waiting
            time.sleep(0.1)
    
    def _consumer_thread(self, queue_name: str, callback: Callable):
        """Consumer thread function."""
        if self.use_mock:
            return self._mock_consumer_thread(queue_name, callback)
            
        # Create a new connection for this thread
        credentials = pika.PlainCredentials(self.user, self.password)
        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        def wrapped_callback(ch, method, properties, body):
            try:
                message = json.loads(body)
                callback(message, properties.correlation_id)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f"Error processing message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
        channel.basic_consume(
            queue=queue_name,
            on_message_callback=wrapped_callback,
            auto_ack=False
        )
        
        try:
            channel.start_consuming()
        except Exception as e:
            print(f"Consumer thread error: {e}")
        finally:
            if connection and connection.is_open:
                connection.close()

class RPC:
    """RPC client for synchronous agent communication."""
    
    def __init__(self, broker: MessageBroker):
        self.broker = broker
        self.response = None
        self.correlation_id = None
        self.callback_queue = None
    
    def initialize(self):
        """Initialize the RPC client."""
        # If using mock broker, no need for special initialization
        if self.broker.use_mock:
            self.callback_queue = f"rpc_callback_{uuid.uuid4()}"
            self.broker.create_queue(self.callback_queue, [self.callback_queue])
            return
            
        # Create a callback queue
        result = self.broker.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue
        
        # Start consuming from the callback queue
        self.broker.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self._on_response,
            auto_ack=True
        )
    
    def _on_response(self, ch, method, props, body):
        """Handle RPC response."""
        if self.correlation_id == props.correlation_id:
            self.response = json.loads(body)
    
    def call(self, routing_key: str, message: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
        """Make an RPC call and wait for response."""
        self.response = None
        self.correlation_id = str(uuid.uuid4())
        
        # Add reply_to to the message
        message["reply_to"] = self.callback_queue
        
        if self.broker.use_mock:
            # For mock broker, publish and wait
            self.broker.publish_message(
                routing_key=routing_key,
                message=message,
                correlation_id=self.correlation_id
            )
            
            # Wait for response with timeout
            start_time = time.time()
            while self.response is None:
                # Check if there's a response in the callback queue
                if (self.callback_queue in self.broker.mock_messages and 
                    self.broker.mock_messages[self.callback_queue]):
                    for i, msg_data in enumerate(self.broker.mock_messages[self.callback_queue]):
                        if msg_data["correlation_id"] == self.correlation_id:
                            self.response = msg_data["message"]
                            # Remove the message
                            self.broker.mock_messages[self.callback_queue].pop(i)
                            break
                
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"RPC call to {routing_key} timed out after {timeout} seconds")
                time.sleep(0.1)
            
            return self.response
        
        properties = pika.BasicProperties(
            reply_to=self.callback_queue,
            correlation_id=self.correlation_id,
            content_type='application/json',
            delivery_mode=2  # Persistent message
        )
        
        self.broker.channel.basic_publish(
            exchange='agent_messages',
            routing_key=routing_key,
            body=json.dumps(message),
            properties=properties
        )
        
        # Wait for response with timeout
        start_time = time.time()
        while self.response is None:
            self.broker.connection.process_data_events()
            if time.time() - start_time > timeout:
                raise TimeoutError(f"RPC call to {routing_key} timed out after {timeout} seconds")
            time.sleep(0.1)
        
        return self.response
