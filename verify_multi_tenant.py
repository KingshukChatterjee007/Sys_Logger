import requests
import time
import uuid

BASE_URL = "http://127.0.0.1:5000"

def test_multi_tenant():
    # 1. Register comp1 for OrgA
    print("Registering OrgA/comp1...")
    uuid_a = str(uuid.uuid4())
    resp_a = requests.post(f"{BASE_URL}/api/register_unit", json={
        "system_id": uuid_a,
        "org_id": "OrgA",
        "comp_id": "comp1",
        "hostname": "OrgA-PC1"
    })
    unit_a = resp_a.json()
    print(f"OrgA/comp1 response: {unit_a}")

    # 2. Register comp1 for OrgB (same computer ID, different Org)
    print("\nRegistering OrgB/comp1...")
    uuid_b = str(uuid.uuid4())
    resp_b = requests.post(f"{BASE_URL}/api/register_unit", json={
        "system_id": uuid_b,
        "org_id": "OrgB",
        "comp_id": "comp1",
        "hostname": "OrgB-PC1"
    })
    unit_b = resp_b.json()
    print(f"OrgB/comp1 response: {unit_b}")

    # 3. Submit usage for OrgA
    print("\nSubmitting usage for OrgA/comp1...")
    resp_submit = requests.post(f"{BASE_URL}/api/submit_usage", json={
        "system_id": uuid_a,
        "org_id": "OrgA",
        "cpu_usage": 45.5,
        "ram_usage": 60.1
    })
    print(f"Submit usage response: {resp_submit.status_code} - {resp_submit.text}")

    # Small delay for backend to process
    time.sleep(1)

    # 4. Check OrgA units again (ensure it exists)
    print(f"\nRe-checking OrgA units...")
    units_a = requests.get(f"{BASE_URL}/api/orgs/OrgA/units").json()
    print(f"OrgA units: {units_a}")

    # 5. Check OrgB units
    print(f"\nChecking OrgB units...")
    units_b = requests.get(f"{BASE_URL}/api/orgs/OrgB/units").json()
    print(f"OrgB units: {[u['comp_id'] for u in units_b]}")

    # 6. Verify isolation (OrgB should not see OrgA's unit)
    assert len(units_a) == 1
    assert units_a[0]['org_id'] == "OrgA"
    assert len(units_b) == 1
    assert units_b[0]['org_id'] == "OrgB"
    print("\n✓ Isolation Verified: OrgA and OrgB have separate unit lists.")

    # 7. Check OrgA usage data
    print(f"\nChecking OrgA usage aggregation...")
    usage_a = requests.get(f"{BASE_URL}/api/orgs/OrgA/usage").json()
    print(f"OrgA latest usage: {usage_a}")
    assert len(usage_a) == 1
    
    print("\n✓ Aggregation Verified: OrgA returns its specific usage data.")

if __name__ == "__main__":
    try:
        test_multi_tenant()
    except Exception as e:
        print(f"\nFAILED: {e}")
