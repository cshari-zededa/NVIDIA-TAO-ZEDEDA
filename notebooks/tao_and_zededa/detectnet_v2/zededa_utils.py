from requests import Session

def create_image(session: Session, base_url: str, image_name: str, image_path: str) -> dict:
    response = session.post(f"{base_url}/images", json={"name": image_name, "path": image_path})
    response.raise_for_status()
    return response.json()

def create_app_bundle(session: Session, base_url: str, bundle_name: str, bundle_images: list) -> dict:
    response = session.post(f"{base_url}/app_bundles", json={"name": bundle_name, "images": bundle_images})
    response.raise_for_status()
    return response.json()
