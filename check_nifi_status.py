#!/usr/bin/env python3
"""Check NiFi Process Group and Controller Services Status"""

import sys
sys.path.append('src')
from nifi_api_client import NiFiAPIClient
import json

def check_nifi_status():
    client = NiFiAPIClient('http://nifi.nks.stjeong.com/nifi-api')
    pg_id = '4cc2258f-0198-1000-6594-f0b789be82ef'

    try:
        # Controller Services 조회
        cs_url = f'{client.base_url}/flow/process-groups/{pg_id}/controller-services'
        response = client.session.get(cs_url)
        cs_list = response.json()['controllerServices']
        
        print(f'=== Controller Services ({len(cs_list)}) ===')
        for cs in cs_list:
            comp = cs['component']
            print(f'\n- {comp["name"]}')
            print(f'  ID: {comp["id"]}')
            print(f'  Type: {comp["type"]}')
            print(f'  State: {comp["state"]}')
            if comp["state"] != "ENABLED":
                print(f'  Validation Errors: {comp.get("validationErrors", [])}')
            
            # 속성 확인
            if 'properties' in comp:
                print(f'  Properties:')
                for key, value in comp['properties'].items():
                    if key != 'Password':  # 비밀번호는 숨김
                        print(f'    {key}: {value}')
                        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_nifi_status()