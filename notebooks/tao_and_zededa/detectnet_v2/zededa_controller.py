from requests import Session
import sqlite3
import uuid
import os
from create_image import create_image, delete_image
from create_app_bundle import create_app_bundle, delete_app_bundle
from create_app_instance import create_app_instance, delete_app_instance
import urllib

class ZededaController:
    def __init__(self):
        self.base_url = os.getenv('ZEDEDA_URL')
        self.token = os.getenv('ZEDEDA_TOKEN')
        self.session = Session()
        self.conn = sqlite3.connect('profiles.db')
        self._create_profiles_table()
        self._create_profile_deployments_table()

    def _create_profiles_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS profiles (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    oci_triton_inference_server TEXT,
                    oci_model_repository TEXT,
                    oci_prometheus_server TEXT,
                    oci_edge_ai_app TEXT,
                    oci_triton_inference_server_image_name TEXT,
                    oci_triton_inference_server_image_uuid TEXT,
                    oci_model_repository_image_name TEXT,
                    oci_model_repository_image_uuid TEXT,
                    oci_prometheus_server_image_name TEXT,
                    oci_prometheus_server_image_uuid TEXT,
                    oci_edge_ai_app_image_name TEXT,
                    oci_edge_ai_app_image_uuid TEXT,
                    triton_bundle_name TEXT,
                    triton_bundle_uuid TEXT,
                    prometheus_bundle_name TEXT,
                    prometheus_bundle_uuid TEXT,
                    edgeaiapp_bundle_name TEXT,
                    edgeaiapp_bundle_uuid TEXT
                )
            ''')

    def _create_profile_deployments_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS profile_deployments (
                    id TEXT PRIMARY KEY,
                    profile_deployment_id TEXT,
                    profile_id TEXT,
                    device_tag TEXT,
                    devices TEXT,
                    triton_instance_name TEXT,
                    triton_instance_uuid TEXT,
                    edge_ai_app_instance_name TEXT,
                    edge_ai_app_instance_uuid TEXT,
                    prometheus_instance_name TEXT,
                    prometheus_instance_uuid TEXT,
                    FOREIGN KEY(profile_id) REFERENCES profiles(id)
                )
            ''')

    def get_devices(self, tag=None):
        if tag:
            encoded_tag = urllib.parse.quote(tag)
            url = f"{self.base_url}/api/v1/devices/status-config?tags={{{encoded_tag}}}"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.session.get(url, headers=headers)
        response.raise_for_status()
        device_list = [{"id": x['id'], "name": x['name'], "projectId": x['projectId']} for x in response.json()['list']]
        return device_list

    def create_profile(self, profile_data):
        """
        profile_data should be a dictionary with the following fields:
        - oci_triton_inference_server: str
        - oci_model_repository: str
        - oci_prometheus_server: str
        - oci_edge_ai_app: str
        """
        profile_id = str(uuid.uuid4())
        profile_data['id'] = profile_id
        profile_data['images'] = {}
        profile_data['application_bundles'] = {}

        # Create Image objects in ZEDEDA Controller
        image_fields = [
            "oci_triton_inference_server",
            "oci_model_repository",
            "oci_prometheus_server",
            "oci_edge_ai_app"
        ]
        image_uuids = {}
        for field in image_fields:
            image_name = f"{profile_data['profile_name']}_{field}"
            print("Creating image for:", field)
            image_uuid = create_image(self.session, self.base_url, image_name, profile_data[field], self.token)
            print("Created image with name:", image_name, "and uuid:", image_uuid)
            image_uuids[field] = image_uuid 
            profile_data['images'][field] = {
                "image_name": image_name,
                "image_uuid": image_uuid
            }

        # Create Application bundles in ZEDEDA Controller
        app_bundles = {
            "Triton": ["oci_triton_inference_server", "oci_model_repository"],
            "Prometheus": ["oci_prometheus_server"],
            "EdgeAIApp": ["oci_edge_ai_app"]
        }
        for app_name, images in app_bundles.items():
            bundle_name = f"{profile_data['profile_name']}_{app_name}"
            bundle_images = [{"uuid": image_uuids[image]} for image in images]
            bundle_images = [{"uuid": image_uuids[image], "name": profile_data['images'][image]['image_name']} for image in images]
            print("Creating bundle for app:", app_name)
            bundle_data = create_app_bundle(self.session, self.base_url, bundle_name, bundle_images, self.token)
            print("Created bundle with name:", bundle_name, "and uuid:", bundle_data['objectId'])
            profile_data['application_bundles'][app_name.lower()] = {
                "bundle_name": bundle_name,
                "bundle_uuid": bundle_data['objectId']
            }

        # Store profile data in SQLite
        with self.conn:
            self.conn.execute('''
                INSERT INTO profiles (id, name, oci_triton_inference_server, oci_model_repository, oci_prometheus_server, oci_edge_ai_app,
                oci_triton_inference_server_image_name, oci_triton_inference_server_image_uuid, oci_model_repository_image_name, 
                oci_model_repository_image_uuid, oci_prometheus_server_image_name, oci_prometheus_server_image_uuid, 
                oci_edge_ai_app_image_name, oci_edge_ai_app_image_uuid, triton_bundle_name, triton_bundle_uuid, 
                prometheus_bundle_name, prometheus_bundle_uuid, edgeaiapp_bundle_name, edgeaiapp_bundle_uuid)
                VALUES (:id, :name, :oci_triton_inference_server, :oci_model_repository, :oci_prometheus_server, :oci_edge_ai_app,
                :oci_triton_inference_server_image_name, :oci_triton_inference_server_image_uuid, :oci_model_repository_image_name, 
                :oci_model_repository_image_uuid, :oci_prometheus_server_image_name, :oci_prometheus_server_image_uuid, 
                :oci_edge_ai_app_image_name, :oci_edge_ai_app_image_uuid, :triton_bundle_name, :triton_bundle_uuid, 
                :prometheus_bundle_name, :prometheus_bundle_uuid, :edgeaiapp_bundle_name, :edgeaiapp_bundle_uuid)
            ''', {
                "id": profile_data['id'],
                "name": profile_data['profile_name'],
                "oci_triton_inference_server": profile_data['oci_triton_inference_server'],
                "oci_model_repository": profile_data['oci_model_repository'],
                "oci_prometheus_server": profile_data['oci_prometheus_server'],
                "oci_edge_ai_app": profile_data['oci_edge_ai_app'],
                "oci_triton_inference_server_image_name": profile_data['images']['oci_triton_inference_server']['image_name'],
                "oci_triton_inference_server_image_uuid": profile_data['images']['oci_triton_inference_server']['image_uuid'],
                "oci_model_repository_image_name": profile_data['images']['oci_model_repository']['image_name'],
                "oci_model_repository_image_uuid": profile_data['images']['oci_model_repository']['image_uuid'],
                "oci_prometheus_server_image_name": profile_data['images']['oci_prometheus_server']['image_name'],
                "oci_prometheus_server_image_uuid": profile_data['images']['oci_prometheus_server']['image_uuid'],
                "oci_edge_ai_app_image_name": profile_data['images']['oci_edge_ai_app']['image_name'],
                "oci_edge_ai_app_image_uuid": profile_data['images']['oci_edge_ai_app']['image_uuid'],
                "triton_bundle_name": profile_data['application_bundles']['triton']['bundle_name'],
                "triton_bundle_uuid": profile_data['application_bundles']['triton']['bundle_uuid'],
                "prometheus_bundle_name": profile_data['application_bundles']['prometheus']['bundle_name'],
                "prometheus_bundle_uuid": profile_data['application_bundles']['prometheus']['bundle_uuid'],
                "edgeaiapp_bundle_name": profile_data['application_bundles']['edgeaiapp']['bundle_name'],
                "edgeaiapp_bundle_uuid": profile_data['application_bundles']['edgeaiapp']['bundle_uuid']
            })

        return profile_data

    def get_profile(self, profile_name=None):
        with self.conn:
            if profile_name:
                cursor = self.conn.execute('SELECT * FROM profiles WHERE name = ?', (profile_name,))
                profile = cursor.fetchone()
                if profile:
                    return {
                        "id": profile[0],
                        "name": profile[1],
                        "oci_triton_inference_server": profile[2],
                        "oci_model_repository": profile[3],
                        "oci_prometheus_server": profile[4],
                        "oci_edge_ai_app": profile[5],
                        "images": {
                            "oci_triton_inference_server": {
                                "image_name": profile[6],
                                "image_uuid": profile[7]
                            },
                            "oci_model_repository": {
                                "image_name": profile[8],
                                "image_uuid": profile[9]
                            },
                            "oci_prometheus_server": {
                                "image_name": profile[10],
                                "image_uuid": profile[11]
                            },
                            "oci_edge_ai_app": {
                                "image_name": profile[12],
                                "image_uuid": profile[13]
                            }
                        },
                        "application_bundles": {
                            "triton": {
                                "bundle_name": profile[14],
                                "bundle_uuid": profile[15]
                            },
                            "prometheus": {
                                "bundle_name": profile[16],
                                "bundle_uuid": profile[17]
                            },
                            "edgeaiapp": {
                                "bundle_name": profile[18],
                                "bundle_uuid": profile[19]
                            }
                        }
                    }
            else:
                cursor = self.conn.execute('SELECT * FROM profiles')
                profiles = cursor.fetchall()
                return [
                    {
                        "id": profile[0],
                        "name": profile[1],
                        "oci_triton_inference_server": profile[2],
                        "oci_model_repository": profile[3],
                        "oci_prometheus_server": profile[4],
                        "oci_edge_ai_app": profile[5],
                        "images": {
                            "oci_triton_inference_server": {
                                "image_name": profile[6],
                                "image_uuid": profile[7]
                            },
                            "oci_model_repository": {
                                "image_name": profile[8],
                                "image_uuid": profile[9]
                            },
                            "oci_prometheus_server": {
                                "image_name": profile[10],
                                "image_uuid": profile[11]
                            },
                            "oci_edge_ai_app": {
                                "image_name": profile[12],
                                "image_uuid": profile[13]
                            }
                        },
                        "application_bundles": {
                            "triton": {
                                "bundle_name": profile[14],
                                "bundle_uuid": profile[15]
                            },
                            "prometheus": {
                                "bundle_name": profile[16],
                                "bundle_uuid": profile[17]
                            },
                            "edgeaiapp": {
                                "bundle_name": profile[18],
                                "bundle_uuid": profile[19]
                            }
                        }
                    }
                    for profile in profiles
                ]
        return None

    def create_profile_deployment(self, profile_name, device_tag):
        profile_deployment_id = str(uuid.uuid4())
        profile = self.get_profile(profile_name)
        devices = self.get_devices(tag=device_tag)
        print("Deploying {profile_name}: on the following devices:-")
        for device in devices:
            print("     ", device['name'])

        profile_deployment_data = {
            "profile_deployment_id": profile_deployment_id,
            "profile_id": profile["id"],
            "device_tag": device_tag,
            "devices": devices,
            "device_deployments": []
        }

        for device in devices:
            print("Creating app instances for device:", device['name'])
            print("Creating Triton instance...")
            triton_instance = create_app_instance(self.session, self.base_url, profile, device, "triton", self.token)
            print("Created Triton instance with name: {triton_instance['name'] and uuid: {triton_instance['uuid']}")
            print("Creating Edge AI App instance...")
            edge_ai_app_instance = create_app_instance(self.session, self.base_url, profile, device, "edgeaiapp", self.token)
            print("Created Edge AI App instance with name: {edge_ai_app_instance['name'] and uuid: {edge_ai_app_instance['uuid']}")
            print("Creating Prometheus instance...")
            prometheus_instance = create_app_instance(self.session, self.base_url, profile, device, "prometheus", self.token)
            print("Created Prometheus instance with name: {prometheus_instance['name'] and uuid: {prometheus_instance['uuid']}")

            device_deployment = {
                "device_id": device['id'],
                "device_name": device['name'],
                "triton_instance_name": triton_instance['name'],
                "triton_instance_uuid": triton_instance['uuid'],
                "edge_ai_app_instance_name": edge_ai_app_instance['name'],
                "edge_ai_app_instance_uuid": edge_ai_app_instance['uuid'],
                "prometheus_instance_name": prometheus_instance['name'],
                "prometheus_instance_uuid": prometheus_instance['uuid']
            }

            profile_deployment_data["device_deployments"].append(device_deployment)

        with self.conn:
            for device_deployment in profile_deployment_data["device_deployments"]:
                self.conn.execute('''
                    INSERT INTO profile_deployments (id, profile_deployment_id, profile_id, device_tag, devices, triton_instance_name, triton_instance_uuid, edge_ai_app_instance_name, edge_ai_app_instance_uuid, prometheus_instance_name, prometheus_instance_uuid)
                    VALUES (:id, :profile_deployment_id, :profile_id, :device_tag, :devices, :triton_instance_name, :triton_instance_uuid, :edge_ai_app_instance_name, :edge_ai_app_instance_uuid, :prometheus_instance_name, :prometheus_instance_uuid)
                ''', {
                    "id": str(uuid.uuid4()),
                    "profile_deployment_id": profile_deployment_data["profile_deployment_id"],
                    "profile_id": profile_deployment_data["profile_id"],
                    "device_tag": profile_deployment_data["device_tag"],
                    "devices": str(profile_deployment_data["devices"]),
                    "triton_instance_name": device_deployment["triton_instance_name"],
                    "triton_instance_uuid": device_deployment["triton_instance_uuid"],
                    "edge_ai_app_instance_name": device_deployment["edge_ai_app_instance_name"],
                    "edge_ai_app_instance_uuid": device_deployment["edge_ai_app_instance_uuid"],
                    "prometheus_instance_name": device_deployment["prometheus_instance_name"],
                    "prometheus_instance_uuid": device_deployment["prometheus_instance_uuid"]
                })

        return profile_deployment_data

    def get_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    def create_app_bundle(self, bundle_name: str, bundle_images: list) -> dict:
        return create_app_bundle(self.session, self.base_url, bundle_name, bundle_images, self.token)

    def delete_profile(self, profile_name):
        # Delete associated profile deployments
        profile = self.get_profile(profile_name)
        if not profile:
            return
        for bundle in profile['application_bundles'].values():
            print("Deleting bundle:", bundle['bundle_name'])
            delete_app_bundle(self.session, self.base_url, bundle['bundle_uuid'], self.token)
            print("Deleted bundle with name:", bundle['bundle_name'], "and uuid:", bundle['bundle_uuid'])

        for image in profile['images'].values():
            print("Deleting image:", image['image_name'])
            delete_image(self.session, self.base_url, image['image_uuid'], self.token)
            print("Deleted image with name:", image['image_name'], "and uuid:", image['image_uuid'])

        # Delete the profile
        with self.conn:
            self.conn.execute('DELETE FROM profiles WHERE name = ?', (profile_name,))
        print("Deleted profile:", profile_name)

    def delete_profile_deployment(self, profile_deployment_id):
        profile_deployment_data = self.get_profile_deployment(profile_deployment_id)

        if profile_deployment_data:
            for device_deployment in profile_deployment_data:
                print("Deleting Triton instance...")
                delete_app_instance(self.session, self.base_url, device_deployment['triton_instance_uuid'], self.token)
                print("Deleted Triton instance with name:", device_deployment['triton_instance_name'], "and uuid:", device_deployment['triton_instance_uuid'])
                print("Deleting Edge AI App instance...")
                delete_app_instance(self.session, self.base_url, device_deployment['edge_ai_app_instance_uuid'], self.token)
                print("Deleted Edge AI App instance with name:", device_deployment['edge_ai_app_instance_name'], "and uuid:", device_deployment['edge_ai_app_instance_uuid'])
                print("Deleting Prometheus instance...")
                delete_app_instance(self.session, self.base_url, device_deployment['prometheus_instance_uuid'], self.token)
                print("Deleted Prometheus instance with name:", device_deployment['prometheus_instance_name'], "and uuid:", device_deployment['prometheus_instance_uuid'])

            with self.conn:
                self.conn.execute('DELETE FROM profile_deployments WHERE profile_deployment_id = ?', (profile_deployment_id,))
            print("Deleted profile deployment with id:", profile_deployment_id)

    def get_profile_deployment(self, profile_deployment_id):
        with self.conn:
            cursor = self.conn.execute('SELECT * FROM profile_deployments WHERE profile_deployment_id = ?', (profile_deployment_id,))
            profile_deployments = cursor.fetchall()
            if profile_deployments:
                return [
                    {
                        "id": record[0],
                        "profile_deployment_id": record[1],
                        "profile_id": record[2],
                        "device_tag": record[3],
                        "devices": record[4],
                        "triton_instance_name": record[5],
                        "triton_instance_uuid": record[6],
                        "edge_ai_app_instance_name": record[7],
                        "edge_ai_app_instance_uuid": record[8],
                        "prometheus_instance_name": record[9],
                        "prometheus_instance_uuid": record[10]
                    }
                    for record in profile_deployments
                ]
            return None

# Example usage:
# zededa = ZededaController("https://zededa.example.com/api")
# profile_data = {
#     "profile_name": "example_profile",
#     "oci_triton_inference_server": "path/to/triton",
#     "oci_model_repository": "path/to/model/repository",
#     "oci_prometheus_server": "path/to/prometheus",
#     "oci_edge_ai_app": "path/to/edge/ai/app"
# }
# profile = zededa.create_profile(profile_data)
# all_profiles = zededa.get_profile()
# single_profile = zededa.get_profile("profile_id")
# updated_profile = zededa.update_profile("profile_id", profile_data)
# devices = zededa.get_devices(tag='"tag":"value"')
# profile_deployment = zededa.create_profile_deployment(profile['id'], '"tag":"value"')
