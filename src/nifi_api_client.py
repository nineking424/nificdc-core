import requests
import json
from typing import Dict, Any, Optional
import time


class NiFiAPIClient:
    def __init__(self, base_url: str, username: Optional[str] = None, password: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.username = username
        self.password = password
        
        if username and password:
            self._authenticate()
    
    def _authenticate(self):
        """Authenticate with NiFi if credentials are provided"""
        auth_url = f"{self.base_url}/access/token"
        response = self.session.post(auth_url, data={
            'username': self.username,
            'password': self.password
        })
        if response.status_code == 201:
            token = response.text
            self.session.headers['Authorization'] = f'Bearer {token}'
    
    def _get_client_id(self) -> str:
        """Get client ID for requests that require it"""
        return f"nifi-cdc-client-{int(time.time())}"
    
    def create_process_group(self, parent_id: str, name: str) -> Dict[str, Any]:
        """Create a new process group"""
        url = f"{self.base_url}/process-groups/{parent_id}/process-groups"
        payload = {
            "revision": {"version": 0},
            "component": {
                "name": name,
                "position": {"x": 0, "y": 0}
            }
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def create_processor(self, process_group_id: str, processor_type: str, 
                        name: str, properties: Dict[str, str], 
                        position: Dict[str, float] = None) -> Dict[str, Any]:
        """Create a new processor in a process group"""
        url = f"{self.base_url}/process-groups/{process_group_id}/processors"
        
        if position is None:
            position = {"x": 0, "y": 0}
        
        payload = {
            "revision": {"version": 0},
            "component": {
                "type": processor_type,
                "name": name,
                "position": position,
                "config": {
                    "properties": properties,
                    "autoTerminatedRelationships": []
                }
            }
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def create_controller_service(self, process_group_id: str, service_type: str,
                                 name: str, properties: Dict[str, str]) -> Dict[str, Any]:
        """Create a controller service"""
        url = f"{self.base_url}/process-groups/{process_group_id}/controller-services"
        
        payload = {
            "revision": {"version": 0},
            "component": {
                "type": service_type,
                "name": name,
                "properties": properties
            }
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def enable_controller_service(self, service_id: str):
        """Enable a controller service"""
        url = f"{self.base_url}/controller-services/{service_id}"
        
        # First get the current revision
        response = self.session.get(url)
        response.raise_for_status()
        current = response.json()
        
        # Enable the service
        payload = {
            "revision": current["revision"],
            "component": {
                "id": service_id,
                "state": "ENABLED"
            }
        }
        
        response = self.session.put(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def create_connection(self, process_group_id: str, source_id: str, 
                         destination_id: str, relationships: list) -> Dict[str, Any]:
        """Create a connection between processors"""
        url = f"{self.base_url}/process-groups/{process_group_id}/connections"
        
        payload = {
            "revision": {"version": 0},
            "component": {
                "source": {
                    "id": source_id,
                    "groupId": process_group_id,
                    "type": "PROCESSOR"
                },
                "destination": {
                    "id": destination_id,
                    "groupId": process_group_id,
                    "type": "PROCESSOR"
                },
                "selectedRelationships": relationships,
                "flowFileExpiration": "0 sec",
                "backPressureDataSizeThreshold": "1 GB",
                "backPressureObjectThreshold": "10000"
            }
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def start_processor(self, processor_id: str):
        """Start a processor"""
        url = f"{self.base_url}/processors/{processor_id}"
        
        # Get current revision
        response = self.session.get(url)
        response.raise_for_status()
        current = response.json()
        
        # Start the processor
        payload = {
            "revision": current["revision"],
            "component": {
                "id": processor_id,
                "state": "RUNNING"
            }
        }
        
        response = self.session.put(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_process_group(self, process_group_id: str) -> Dict[str, Any]:
        """Get process group details"""
        url = f"{self.base_url}/process-groups/{process_group_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()