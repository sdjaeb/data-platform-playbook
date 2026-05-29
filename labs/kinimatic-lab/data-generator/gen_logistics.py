import json
import random
import uuid
from datetime import datetime

def generate_logistics_event():
    return {
        'event_id': str(uuid.uuid4()),
        'source': 'WMS-NORTH-01',
        'type': random.choice(['ORDER_CREATED', 'ITEM_PICKED', 'SHIPMENT_DEPARTED', 'INVENTORY_ADJUSTED']),
        'timestamp': datetime.utcnow().isoformat(),
        'data': {
            'order_id': f'ORD-{random.randint(10000,99999)}',
            'sku': f'SKU-{random.randint(100,999)}',
            'quantity': random.randint(1, 50),
            'warehouse_id': f'WH-{random.randint(1,350)}'
        }
    }

if __name__ == '__main__':
    for _ in range(10):
        print(json.dumps(generate_logistics_event()))
