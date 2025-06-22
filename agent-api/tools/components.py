import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any
from pydantic import BaseModel
from dataclasses import dataclass, asdict
import random
import psycopg2
from loguru import logger

logger.add(
    "logs/detailed.log",
    format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
    level="INFO"
)


class EnvironmentSensorData(BaseModel):
    """Data from environment sensors data"""
    temperature: float
    humidity: float
    et0: float


class WateringScheduleTableColumns(BaseModel):
    """Input data for watering schedule"""
    time_waiting: int
    next_time_watering: str
    watering_traffic: str
    environ_sensor_data: EnvironmentSensorData
    reason: str
    
class ReflectionTableColumns(BaseModel):
    """Input data for reflection"""
    reflection_text: str

class OuputDataTableColumns(BaseModel):
    """Output data for watering schedule"""
    time_full: int
    EC: float


    

class PostgreSQLDatabase:
    """Database for storing irrigation cycles"""
    
    def __init__(
        self,
    ) -> None:
        
        conn = psycopg2.connect(
            host = os.getenv("DB_HOST", "localhost"),
            port = os.getenv("DB_PORT", "35432"),
            database = os.getenv("DB_NAME", "mimosatek_db"),
            user = os.getenv("DB_USER", "mimosatek_user"),
            password = os.getenv("DB_PASSWORD", "mimosatek_password")
        )
        
        self.cur = conn.cursor()
    
        logger.info("PostgreSQLDatabase initialized successfully.")
    
    def get_all_table(
        self
    ) -> List[str]:
        """
        Get all table names in the database.
        
        Returns:
            List[str]: A list of table names.
        """
        query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        self.cur.execute(query)
        tables = self.cur.fetchall()
        
        if not tables:
            logger.warning("No tables found in the database.")
            return []
        
        table_names = [table[0] for table in tables]
        logger.info(f"Tables found: {table_names}")
        return table_names

    def get_columns_of_table(
        self,
        table_name: str,
    ) -> List[str]:
        """
        Get the column names of a specified table.
        
        Args:
            table_name (str): The name of the table to query.
        
        Returns:
            List[str]: A list of column names in the specified table.
        """
        query = f"SELECT column_name FROM information_schema.columns WHERE table_name = %s"
        self.cur.execute(query, (table_name,))
        columns = self.cur.fetchall()
        
        if not columns:
            logger.warning(f"No columns found in table {table_name}.")
            return []
        
        column_names = [column[0] for column in columns]
        logger.info(f"Columns in {table_name}: {column_names}")
        return column_names
    
    def add_record_to_wateringschedule_table(
        self,
        record: WateringScheduleTableColumns
    ) -> None:
        """
        Add a record to the watering schedule table.
        
        Args:
            record (WateringScheduleTableColumns): The record to add.
        """
        query = """
            INSERT INTO watering_schedule (time_waiting, next_time_watering, watering_traffic, environ_sensor_data, reason)
            VALUES (%s, %s, %s, %s, %s)
        """
        self.cur.execute(query, (
            record.time_waiting,
            record.next_time_watering,
            record.watering_traffic,
            json.dumps(record.environ_sensor_data),
            record.reason
        ))
        logger.info(f"Record added to watering_schedule: {asdict(record)}")
    
    def add_record_to_reflection_table(
        self,
        record: ReflectionTableColumns
    ) -> None:
        """
        Add a record to the reflection table.
        
        Args:
            record (ReflectionTableColumns): The record to add.
        """
        query = """
            INSERT INTO reflection (reflection_text)
            VALUES (%s)
        """
        self.cur.execute(query, (record.reflection_text,))
        logger.info(f"Record added to reflection: {asdict(record)}")
    
    def add_record_to_outputdata_table(
        self,
        record: OuputDataTableColumns
    ) -> None:
        """
        Add a record to the output data table.
        
        Args:
            record (OuputDataTableColumns): The record to add.
        """
        query = """
            INSERT INTO output_data (time_full, EC)
            VALUES (%s, %s)
        """
        self.cur.execute(query, (record.time_full, record.EC))
        logger.info(f"Record added to output_data: {asdict(record)}")
    
    
    def get_last_record(
        self,
        table_name: str,
    ) -> Dict[str, Any]:
        """
        Get the last record from a specified table.
        
        Args:
            table_name (str): The name of the table to query.
        
        Returns:
            dict: The last record from the specified table.
        """
        query = f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 1"
        self.cur.execute(query)
        record = self.cur.fetchone()
        
        if record is None:
            logger.warning(f"No records found in {table_name}.")
            return {}
        
        columns = [desc[0] for desc in self.cur.description]
        result = dict(zip(columns, record))
        
        logger.info(f"Last record from {table_name}: {result}")
        return result

    def get_recent_records(
        self,
        table_name: str,
        num_records: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get recent records from a specified table.
        
        Args:
            table_name (str): The name of the table to query.
            num_records (int): The number of recent records to retrieve.
        
        Returns:
            List[dict]: A list of recent records from the specified table.
        """
        query = f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT %s"
        self.cur.execute(query, (num_records,))
        records = self.cur.fetchall()
        
        if not records:
            logger.warning(f"No recent records found in {table_name}.")
            return []
        
        columns = [desc[0] for desc in self.cur.description]
        result = [dict(zip(columns, record)) for record in records]
        
        logger.info(f"Recent records from {table_name}: {result}")
        return result
    
    def update_record(
        self,
        table_name: str,
        record_id: int,
        updates: Dict[str, Any]
    ) -> None:
        """
        Update a record in a specified table.
        
        Args:
            table_name (str): The name of the table to update.
            record_id (int): The ID of the record to update.
            updates (Dict[str, Any]): A dictionary of column names and their new values.
        """
        set_clause = ", ".join([f"{key} = %s" for key in updates.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE id = %s"
        self.cur.execute(query, list(updates.values()) + [record_id])
        logger.info(f"Record with ID {record_id} updated in {table_name}: {updates}")
    
    def close_connection(
        self
    ) -> None:
        """
        Close the database connection.
        """
        self.cur.close()
        logger.info("Database connection closed.")
    