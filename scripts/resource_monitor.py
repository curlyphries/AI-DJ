import os
import time
import psutil
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'resource_monitor.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Target resource limits (50% as specified in the project plan)
TARGET_CPU_PERCENT = 50.0
TARGET_RAM_PERCENT = 50.0

def get_system_resources():
    """Get current system resource usage."""
    cpu_percent = psutil.cpu_percent(interval=1)
    ram_percent = psutil.virtual_memory().percent
    
    return {
        'cpu_usage': cpu_percent,
        'ram_usage': ram_percent,
        'timestamp': datetime.now().isoformat()
    }

def check_resource_limits(resources):
    """Check if resource usage exceeds limits."""
    if resources['cpu_usage'] > TARGET_CPU_PERCENT:
        logger.warning(f"CPU usage ({resources['cpu_usage']}%) exceeds target limit of {TARGET_CPU_PERCENT}%")
        return False
    
    if resources['ram_usage'] > TARGET_RAM_PERCENT:
        logger.warning(f"RAM usage ({resources['ram_usage']}%) exceeds target limit of {TARGET_RAM_PERCENT}%")
        return False
    
    return True

def save_resource_data(resources):
    """Save resource data to a JSON file for the web interface."""
    try:
        resources_file = os.path.join('logs', 'resources.json')
        
        # Create a list of recent resource measurements
        recent_resources = []
        
        # Load existing data if available
        if os.path.exists(resources_file):
            with open(resources_file, 'r') as f:
                try:
                    recent_resources = json.load(f)
                except json.JSONDecodeError:
                    recent_resources = []
        
        # Add new measurement
        recent_resources.append(resources)
        
        # Keep only the last 60 measurements (10 minutes at 10-second intervals)
        if len(recent_resources) > 60:
            recent_resources = recent_resources[-60:]
        
        # Save to file
        with open(resources_file, 'w') as f:
            json.dump(recent_resources, f)
    
    except Exception as e:
        logger.error(f"Error saving resource data: {str(e)}")

def throttle_if_needed(resources):
    """Apply throttling if resources exceed limits."""
    if resources['cpu_usage'] > TARGET_CPU_PERCENT or resources['ram_usage'] > TARGET_RAM_PERCENT:
        # Set a flag file to indicate throttling is needed
        with open(os.path.join('logs', 'throttle.flag'), 'w') as f:
            f.write('1')
        return True
    else:
        # Remove flag file if it exists
        flag_file = os.path.join('logs', 'throttle.flag')
        if os.path.exists(flag_file):
            os.remove(flag_file)
        return False

def main():
    """Main function to monitor system resources."""
    logger.info("Starting resource monitor...")
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    try:
        while True:
            # Get current resource usage
            resources = get_system_resources()
            
            # Log resource usage
            logger.info(f"CPU: {resources['cpu_usage']}%, RAM: {resources['ram_usage']}%")
            
            # Save resource data
            save_resource_data(resources)
            
            # Check if throttling is needed
            throttled = throttle_if_needed(resources)
            if throttled:
                logger.warning("Resource limits exceeded. Throttling enabled.")
            
            # Sleep for 10 seconds
            time.sleep(10)
    
    except KeyboardInterrupt:
        logger.info("Resource monitor stopped by user.")
    except Exception as e:
        logger.error(f"Error in resource monitor: {str(e)}")

if __name__ == "__main__":
    main()
