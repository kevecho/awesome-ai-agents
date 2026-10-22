"""Comprehensive API test script for AI Medical Consultant"""
import httpx
import asyncio
import json
import sys

BASE_URL = "http://localhost:9000"
USERNAME = "testuser"
PASSWORD = "123456"

async def main():
    passed = 0
    failed = 0

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
        # 1. Login
        print("=" * 60)
        print("1. Login")
        r = await client.post('/api/v1/user/login', json={'username': USERNAME, 'password': PASSWORD})
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            token = r.json()['access_token']
            print(f"   [PASS] Token: {token[:30]}...")
            passed += 1
        else:
            print(f"   [FAIL] {r.text}")
            failed += 1
            return

        headers = {'Authorization': f'Bearer {token}'}

        # 2. Health check
        print("\n2. Health Check")
        r = await client.get('/health')
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            print(f"   [PASS] {r.json()}")
            passed += 1
        else:
            print(f"   [FAIL] {r.text}")
            failed += 1

        # 3. Create consultation
        print("\n3. Create Consultation")
        r = await client.post('/api/v1/consult/', json={'title': 'Test'}, headers=headers)
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            consult = r.json()
            cid = consult['id']
            print(f"   [PASS] Created id={cid}, title={consult.get('title','?')}")
            passed += 1
        else:
            print(f"   [FAIL] {r.text}")
            failed += 1
            cid = None

        # 4. List consultations
        print("\n4. List Consultations")
        r = await client.get('/api/v1/consult/', headers=headers)
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"   [PASS] Count: {len(data) if isinstance(data, list) else 'N/A'}")
            passed += 1
        else:
            print(f"   [FAIL] {r.text}")
            failed += 1

        # 5. Get consultation detail
        if cid:
            print("\n5. Get Consultation Detail")
            r = await client.get(f'/api/v1/consult/{cid}', headers=headers)
            print(f"   Status: {r.status_code}")
            if r.status_code == 200:
                print(f"   [PASS] Messages: {len(r.json().get('messages', []))}")
                passed += 1
            else:
                print(f"   [FAIL] {r.text}")
                failed += 1

        # 6. Agent Triage
        if cid:
            print("\n6. Agent Triage")
            r = await client.post('/api/v1/agent/triage', json=[
                {"name": "headache", "location": "head", "duration": "2 days", "severity": "moderate", "description": "持续头痛"},
                {"name": "fever", "duration": "2 days", "severity": "mild", "description": "低烧37.5度"},
                {"name": "cough", "duration": "2 days", "severity": "mild", "description": "干咳"}
            ], headers=headers)
            print(f"   Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                print(f"   [PASS] Response keys: {list(data.keys())}")
                passed += 1
            else:
                print(f"   [FAIL] {r.text}")
                failed += 1

        # 7. Agent Diagnose
        if cid:
            print("\n7. Agent Diagnose")
            r = await client.post('/api/v1/agent/diagnose', json=[
                {"name": "headache", "location": "head", "duration": "2 days", "severity": "moderate", "description": "持续性钝痛"},
                {"name": "fever", "duration": "2 days", "severity": "moderate", "description": "体温38度"},
                {"name": "cough", "duration": "3 days", "severity": "mild", "description": "干咳无痰"},
                {"name": "fatigue", "duration": "3 days", "severity": "moderate", "description": "全身乏力"}
            ], headers=headers)
            print(f"   Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                print(f"   [PASS] Response keys: {list(data.keys())}")
                passed += 1
            else:
                print(f"   [FAIL] {r.text}")
                failed += 1

        # 8. Knowledge Search
        print("\n8. Knowledge Search")
        r = await client.post('/api/v1/knowledge/search', json={
            'query': 'cold and fever',
            'top_k': 3
        }, headers=headers)
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            # API returns list directly
            result_count = len(data) if isinstance(data, list) else len(data.get('results', []))
            print(f"   [PASS] Results: {result_count}")
            passed += 1
        else:
            print(f"   [FAIL] {r.text}")
            failed += 1

        # 9. Knowledge Stats
        print("\n9. Knowledge Stats")
        r = await client.get('/api/v1/knowledge/stats', headers=headers)
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            print(f"   [PASS] {r.json()}")
            passed += 1
        else:
            print(f"   [FAIL] {r.text}")
            failed += 1

        # 10. List Knowledge Documents (read-only, no side effects)
        print("\n10. List Knowledge Documents")
        r = await client.get('/api/v1/knowledge/documents', headers=headers)
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            doc_count = len(data) if isinstance(data, list) else 'N/A'
            print(f"   [PASS] Documents listed: {doc_count}")
            passed += 1
        else:
            print(f"   [FAIL] {r.text}")
            failed += 1

        # 11. User info
        print("\n11. Get Current User")
        r = await client.get('/api/v1/user/me', headers=headers)
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            print(f"   [PASS] User: {r.json().get('username', '?')}")
            passed += 1
        else:
            print(f"   [FAIL] {r.text}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0

if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
