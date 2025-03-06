from requests import Session
import json

def create_app_bundle(session: Session, base_url: str, bundle_name: str, bundle_images: list, token: str) -> dict:
    if len(bundle_images) > 1:
        # Treat bundle with more than 1 image as Triton server
        template_path = '/home/ubuntu/tao-getting-started_5.0.0/notebooks/tao_launcher_starter_kit/detectnet_v2/payload_templates/triton_bundle.json'
    elif "Prometheus" in bundle_name:
        template_path = '/home/ubuntu/tao-getting-started_5.0.0/notebooks/tao_launcher_starter_kit/detectnet_v2/payload_templates/prometheus_bundle.json'
    elif "EdgeAIApp" in bundle_name:
        template_path = '/home/ubuntu/tao-getting-started_5.0.0/notebooks/tao_launcher_starter_kit/detectnet_v2/payload_templates/edgeapp_bundle.json'
    else:
        raise ValueError("Unsupported bundle type")
    
    with open(template_path) as f:
        payload = json.load(f)

    payload['name'] = bundle_name
    payload['title'] = bundle_name

    for i, image in enumerate(bundle_images):
        payload['manifestJSON']['images'][i]['imagename'] = image['name']
        payload['manifestJSON']['images'][i]['imageid'] = image['uuid']

    headers = {"Authorization": f"Bearer {token}"}
    #print(payload)
    response = session.post(f"{base_url}/api/v1/apps", json=payload, headers=headers)
    #print(response.json())
    response.raise_for_status()
    return response.json()

def delete_app_bundle(session: Session, base_url: str, bundle_uuid: str, token: str) -> dict:
   headers = {"Authorization": f"Bearer {token}"} 
   response = session.delete(f"{base_url}/api/v1/apps/id/{bundle_uuid}", headers=headers)
   #print(response)
   response.raise_for_status()
   return response.json()
