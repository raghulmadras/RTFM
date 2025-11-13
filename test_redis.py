import redis
import sys

def test_redis_connection():
    """Test Redis connectivity"""
    try:
        # Connect to Redis
        redis_client = redis.Redis(
            host='redis',
            port=6379,
            decode_responses=True,
            socket_connect_timeout=5
        )
        
        # Test ping
        response = redis_client.ping()
        if response:
            print("✅ Redis connection successful!")
            print(f"✅ Redis PING response: {response}")
            
            # Test set/get
            redis_client.set('test_key', 'test_value')
            value = redis_client.get('test_key')
            print(f"✅ Redis SET/GET test: {value}")
            
            # Clean up
            redis_client.delete('test_key')
            
            return True
        else:
            print("❌ Redis ping failed")
            return False
            
    except redis.ConnectionError as e:
        print(f"❌ Redis connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_redis_connection()
    sys.exit(0 if success else 1)
