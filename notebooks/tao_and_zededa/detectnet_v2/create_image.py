from requests import Session
import json

def create_image(session: Session, base_url: str, image_name: str, image_path: str, token: str) -> str:
    with open('/home/ubuntu/tao-getting-started_5.0.0/notebooks/tao_launcher_starter_kit/detectnet_v2/payload_templates/image_create.json') as f:
        payload = json.load(f)
    
    payload['name'] = image_name
    payload['title'] = image_name
    payload['imageRelUrl'] = image_path

    headers = {"Authorization": f"Bearer {token}"}
    #print(payload)
    response = session.post(f"{base_url}/api/v1/apps/images", json=payload, headers=headers)
    #print(response)
    response.raise_for_status()
    image_uuid = response.json()['objectId']

    # Uplink the image, to mark the image as READY
    with open('/home/ubuntu/tao-getting-started_5.0.0/notebooks/tao_launcher_starter_kit/detectnet_v2/payload_templates/image_uplink.json') as f:
        payload = json.load(f)

    payload['name'] = image_name
    payload['title'] = image_name
    payload['id'] = image_uuid 
    payload['imageRelUrl'] = image_path

    #print(payload)
    response = session.put(f"{base_url}/api/v1/apps/images/id/{image_uuid}/uplink", json=payload, headers=headers)
    response.raise_for_status()
    #print(response)
    return image_uuid

def delete_image(session: Session, base_url: str, image_id: str, token: str) -> dict:
   headers = {"Authorization": f"Bearer {token}"} 
   response = session.delete(f"{base_url}/api/v1/apps/images/id/{image_id}", headers=headers)
   #print(response)
   response.raise_for_status()
   return response.json()
