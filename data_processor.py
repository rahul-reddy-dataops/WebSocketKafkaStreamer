import pandas as pd
import json
import logging
import os
from datetime import datetime
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        """Initialize the data processor"""
        self.last_processed_data = None
        self.supported_formats = ['.json', '.csv']
    
    def process_file(self, filepath):
        """Process uploaded file and return standardized DataFrame"""
        try:
            file_extension = os.path.splitext(filepath)[1].lower()
            
            if file_extension == '.json':
                return self._process_json_file(filepath)
            elif file_extension == '.csv':
                return self._process_csv_file(filepath)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
                
        except Exception as e:
            logger.error(f"Error processing file {filepath}: {str(e)}")
            raise
    
    def _process_json_file(self, filepath):
        """Process JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # If it's a single object, wrap in list
                if all(isinstance(v, (str, int, float, bool)) for v in data.values()):
                    df = pd.DataFrame([data])
                else:
                    # Try to find the main data array
                    main_key = self._find_main_data_key(data)
                    if main_key and isinstance(data[main_key], list):
                        df = pd.DataFrame(data[main_key])
                    else:
                        # Flatten the dictionary
                        df = pd.json_normalize(data)
            else:
                raise ValueError("JSON data must be an object or array")
            
            # Clean and standardize the data
            df = self._clean_dataframe(df)
            
            # Cache the processed data
            self.last_processed_data = df
            
            logger.info(f"Successfully processed JSON file: {len(df)} records")
            return df
            
        except Exception as e:
            logger.error(f"Error processing JSON file {filepath}: {str(e)}")
            raise
    
    def _process_csv_file(self, filepath):
        """Process CSV file"""
        try:
            # Try different encoding options
            encodings = ['utf-8', 'latin-1', 'cp1252']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(filepath, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise ValueError("Could not read CSV file with any supported encoding")
            
            # Clean and standardize the data
            df = self._clean_dataframe(df)
            
            # Cache the processed data
            self.last_processed_data = df
            
            logger.info(f"Successfully processed CSV file: {len(df)} records")
            return df
            
        except Exception as e:
            logger.error(f"Error processing CSV file {filepath}: {str(e)}")
            raise
    
    def _find_main_data_key(self, data):
        """Find the main data key in a JSON object"""
        # Common patterns for data arrays
        common_keys = ['data', 'items', 'records', 'results', 'rows', 'entries']
        
        for key in common_keys:
            if key in data and isinstance(data[key], list):
                return key
        
        # Look for the largest array
        max_len = 0
        max_key = None
        
        for key, value in data.items():
            if isinstance(value, list) and len(value) > max_len:
                max_len = len(value)
                max_key = key
        
        return max_key
    
    def _clean_dataframe(self, df):
        """Clean and standardize DataFrame"""
        try:
            # Remove completely empty rows and columns
            df = df.dropna(how='all').dropna(axis=1, how='all')
            
            # Clean column names
            df.columns = df.columns.astype(str)
            df.columns = [col.strip().replace(' ', '_').lower() for col in df.columns]
            
            # Handle datetime columns
            df = self._parse_datetime_columns(df)
            
            # Handle numeric columns
            df = self._parse_numeric_columns(df)
            
            # Add processing metadata
            df['_processed_at'] = datetime.now()
            df['_record_id'] = range(len(df))
            
            return df
            
        except Exception as e:
            logger.error(f"Error cleaning DataFrame: {str(e)}")
            return df  # Return original if cleaning fails
    
    def _parse_datetime_columns(self, df):
        """Parse potential datetime columns"""
        datetime_keywords = ['date', 'time', 'timestamp', 'created', 'updated', 'start', 'end']
        
        for col in df.columns:
            if any(keyword in col.lower() for keyword in datetime_keywords):
                try:
                    df[col] = pd.to_datetime(df[col], errors='ignore')
                except:
                    pass  # If conversion fails, keep original
        
        return df
    
    def _parse_numeric_columns(self, df):
        """Parse potential numeric columns"""
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    # Try to convert to numeric
                    numeric_series = pd.to_numeric(df[col], errors='coerce')
                    
                    # If more than 50% of values are numeric, convert
                    if numeric_series.notna().sum() / len(df) > 0.5:
                        df[col] = numeric_series
                except:
                    pass  # Keep as string if conversion fails
        
        return df
    
    def validate_data(self, df):
        """Validate processed data"""
        if df.empty:
            raise ValueError("Processed data is empty")
        
        if len(df.columns) == 0:
            raise ValueError("No columns found in processed data")
        
        logger.info(f"Data validation passed: {len(df)} rows, {len(df.columns)} columns")
        return True
    
    def get_data_summary(self, df):
        """Get summary statistics of the data"""
        try:
            summary = {
                'total_records': len(df),
                'total_columns': len(df.columns),
                'numeric_columns': len(df.select_dtypes(include=[np.number]).columns),
                'categorical_columns': len(df.select_dtypes(include=['object']).columns),
                'datetime_columns': len(df.select_dtypes(include=['datetime']).columns),
                'missing_values': df.isnull().sum().sum(),
                'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating data summary: {str(e)}")
            return {}
    
    def create_sample_data(self, num_records=100):
        """Create sample data for demonstration"""
        try:
            np.random.seed(42)  # For reproducible results
            
            data = {
                'id': range(1, num_records + 1),
                'timestamp': pd.date_range(start='2024-01-01', periods=num_records, freq='H'),
                'value': np.random.normal(100, 15, num_records).round(2),
                'category': np.random.choice(['A', 'B', 'C', 'D', 'E'], num_records),
                'status': np.random.choice(['active', 'inactive', 'pending'], num_records),
                'score': np.random.uniform(0, 100, num_records).round(2),
                'region': np.random.choice(['North', 'South', 'East', 'West'], num_records),
                'priority': np.random.choice(['high', 'medium', 'low'], num_records),
                'amount': np.random.exponential(50, num_records).round(2)
            }
            
            df = pd.DataFrame(data)
            df = self._clean_dataframe(df)
            
            logger.info(f"Created sample data with {len(df)} records")
            return df
            
        except Exception as e:
            logger.error(f"Error creating sample data: {str(e)}")
            raise
