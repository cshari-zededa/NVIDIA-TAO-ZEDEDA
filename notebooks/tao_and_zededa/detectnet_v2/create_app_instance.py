from requests import Session
import json

def create_app_instance(session: Session, base_url: str, profile: dict, device: dict, app_type: str, token: str) -> dict:
    if app_type == "triton":
        template = "/home/ubuntu/tao-getting-started_5.0.0/notebooks/tao_launcher_starter_kit/detectnet_v2/payload_templates/triton_appinst.json" 
        ipAddr = '10.3.0.2'
    elif app_type == "edgeaiapp":
        template = "/home/ubuntu/tao-getting-started_5.0.0/notebooks/tao_launcher_starter_kit/detectnet_v2/payload_templates/edgeappinst.json"
        ipAddr = '10.3.0.3'
    elif app_type == "prometheus":
        template = "/home/ubuntu/tao-getting-started_5.0.0/notebooks/tao_launcher_starter_kit/detectnet_v2/payload_templates/prometheus.json"
        ipAddr = '10.3.0.4'
    else:
        return {}
    
    with open(template) as f:
        request = json.load(f)
    
    request['name'] = f"{profile['name']}-{app_type}-{device['name']}"
    request['title'] = request['name'] 
    request['projectId'] = device['projectId']
    request['deviceId'] = device['id']
    request['appId'] = profile['application_bundles'][app_type]['bundle_uuid']
    request['interfaces'][0]['netinstname'] = f"EdgeAI-NetInstance-{device['name']}"
    request['interfaces'][0]['ipaddr'] = ipAddr 
    if app_type == "prometheus":
        print(f"Marking source as {request['name']} for prometheus exporter app instance")
        request["customConfig"]["variableGroups"][0]["variables"][0]["value"] = request['name'] 

    headers = {"Authorization": f"Bearer {token}"}
    response = session.post(f"{base_url}/api/v2/apps/instances", json=request, headers=headers)
    response.raise_for_status()

    response = session.get(f"{base_url}/api/v2/apps/instances/name/{request['name']}", headers=headers)  
    #print(response.json())
    response.raise_for_status()
    return {"uuid": response.json()['id'], "name": response.json()['name']} 

def delete_app_instance(session: Session, base_url: str, app_instance_id: str, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    response = session.delete(f"{base_url}/api/v2/apps/instances/id/{app_instance_id}", headers=headers)
    #print(response)
    response.raise_for_status()
    return response.json() 
