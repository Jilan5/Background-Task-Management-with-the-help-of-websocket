import asyncio
import aiohttp
import time
import random

async def send_task_request(session, url, task_type='default'):
    """Send a task request to the API"""
    endpoint = url
    if task_type == 'high':
        endpoint = f"{url}/high-priority"
    elif task_type == 'low':
        endpoint = f"{url}/low-priority"
        
    async with session.post(endpoint) as response:
        return await response.json()

async def main():
    """Main function that simulates multiple clients sending requests"""
    base_url = "http://localhost:8000/tasks"
    concurrent_requests = 50
    task_types = ['default', 'high', 'low']
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(concurrent_requests):
            # Randomly select task type to simulate different client needs
            task_type = random.choice(task_types)
            tasks.append(send_task_request(session, base_url, task_type))
            
        print(f"Sending {concurrent_requests} concurrent requests...")
        start_time = time.time()
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        print(f"All requests completed in {end_time - start_time:.2f} seconds")
        print(f"Average response time: {(end_time - start_time) / concurrent_requests:.4f} seconds")
        
        # Count task types
        task_types_count = {
            'default': 0,
            'high': 0,
            'low': 0
        }
        
        for response in responses:
            if 'High priority' in response.get('status', ''):
                task_types_count['high'] += 1
            elif 'Low priority' in response.get('status', ''):
                task_types_count['low'] += 1
            else:
                task_types_count['default'] += 1
                
        print(f"Task distribution: {task_types_count}")

if __name__ == "__main__":
    asyncio.run(main())