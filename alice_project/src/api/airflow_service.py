"""
Airflow REST API client for asynchronous job triggering and monitoring
"""

import requests
import logging
from typing import Dict, Any
from config.settings import settings

logger = logging.getLogger(__name__)


class AirflowClient:
    """Client for interacting with Airflow REST API"""
    
    def __init__(self, base_url: str = None, username: str = "admin", password: str = "admin"):
        self.base_url = base_url or settings.AIRFLOW_BASE_URL
        self.username = username
        self.password = password
        self.auth = (username, password)
        self._session = requests.Session()
        self._session.auth = self.auth
    
    def trigger_dag(self, dag_id: str, conf: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Trigger a DAG execution asynchronously
        
        Args:
            dag_id: DAG identifier
            conf: Configuration dictionary to pass to DAG
            
        Returns:
            Response with dag_run_id and other metadata
        """
        url = f"{self.base_url}/dags/{dag_id}/dagRuns"
        payload = {"conf": conf or {}}
        
        try:
            response = self._session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info(f"DAG {dag_id} triggered successfully. Run ID: {data.get('dag_run_id')}")
            return {
                "dag_run_id": data.get("dag_run_id"),
                "state": data.get("state"),
                "execution_date": data.get("execution_date"),
                "start_date": data.get("start_date"),
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to trigger DAG {dag_id}: {str(e)}")
            raise
    
    def get_dag_run_status(self, dag_id: str, dag_run_id: str) -> Dict[str, Any]:
        """
        Get the status of a specific DAG run
        
        Args:
            dag_id: DAG identifier
            dag_run_id: DAG run identifier
            
        Returns:
            DAG run status information
        """
        url = f"{self.base_url}/dags/{dag_id}/dagRuns/{dag_run_id}"
        
        try:
            response = self._session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.debug(f"DAG run {dag_run_id} state: {data.get('state')}")
            return {
                "dag_run_id": data.get("dag_run_id"),
                "state": data.get("state"),
                "start_date": data.get("start_date"),
                "end_date": data.get("end_date"),
                "execution_date": data.get("execution_date"),
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get DAG run status: {str(e)}")
            raise
    
    def get_task_instance_logs(self, dag_id: str, dag_run_id: str, task_id: str) -> str:
        """
        Get logs from a specific task instance
        
        Args:
            dag_id: DAG identifier
            dag_run_id: DAG run identifier
            task_id: Task identifier
            
        Returns:
            Task logs as string
        """
        url = f"{self.base_url}/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs"
        
        try:
            response = self._session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get task logs for {task_id}: {str(e)}")
            raise
    
    def get_all_dag_runs(self, dag_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get all DAG runs for a specific DAG
        
        Args:
            dag_id: DAG identifier
            limit: Maximum number of runs to return
            
        Returns:
            List of DAG runs
        """
        url = f"{self.base_url}/dags/{dag_id}/dagRuns?limit={limit}&order_by=-start_date"
        
        try:
            response = self._session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return {
                "total_entries": data.get("total_entries", 0),
                "dag_runs": data.get("dag_runs", [])
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get DAG runs: {str(e)}")
            raise


# Global client instance
airflow_client = AirflowClient()