import json
import random
import uuid
from datetime import datetime

def generate_call_event():
    return {
        'event_id': str(uuid.uuid4()),
        'timestamp': datetime.utcnow().isoformat(),
        'call_sid': f'CA{uuid.uuid4().hex[:32]}',
        'from': f'+1{random.randint(200,999)}{random.randint(200,999)}{random.randint(1000,9999)}',
        'event_type': random.choice(['speech_started', 'speech_finished', 'llm_thought_started', 'llm_thought_finished', 'tts_stream_started']),
        'payload': {
            'text': 'Hello, I am interested in your services.' if random.random() > 0.5 else None,
            'latency_ms': random.randint(50, 500)
        }
    }

if __name__ == '__main__':
    for _ in range(10):
        print(json.dumps(generate_call_event()))
