#!/usr/bin/env python3

from zededa_controller import ZededaController
import json

def test_zededa_controller():
    zededa = ZededaController()
    
    #Create Edge AI Application profile
    profile_data = {
        "profile_name": "nvidia_triton_profile",
        "oci_triton_inference_server": "csharizededa/tritonserver:6.0",
        "oci_model_repository": "csharizededa/ngcmodels:1.0",
        "oci_prometheus_server": "csharizededa/zprometheus:1.0",
        "oci_edge_ai_app": "csharizededa/edgeapp:1.0"
    }
    profile = zededa.create_profile(profile_data)
    print("Created Profile:", json.dumps(profile, indent=4, sort_keys=True))
    
    # Test get_profile
    all_profiles = zededa.get_profile()
    #print("All Profiles:", all_profiles)
    
    # Test get_devices
    devices = zededa.get_devices(tag='"edgeDeviceGroup":"jetsons"')
    #print("Devices:", devices)

    # Test create_profile_deployment
    profile_deployment = zededa.create_profile_deployment("nvidia_triton_profile", '"edgeDeviceGroup":"jetsons"')
    print("Profile Deployment:", json.dumps(profile_deployment, indent=4, sort_keys=True))
    

    # Test delete_profile_deployment
    #delete_response = zededa.delete_profile_deployment(profile_deployment_id=profile_deployment['profile_deployment_id'])
    #print("Deleted Profile Deployment")
    
    # Test delete_profile
    #delete_response = zededa.delete_profile("nvidia_triton_profile")
    #print("Deleted Profile")

if __name__ == "__main__":
    test_zededa_controller()
