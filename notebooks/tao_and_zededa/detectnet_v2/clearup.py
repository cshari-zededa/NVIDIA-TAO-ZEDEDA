#!/usr/bin/env python3

from zededa_controller import ZededaController

def test_zededa_controller():
    zededa = ZededaController()

    # Test create_profile_deployment
    delete_response = zededa.delete_profile("nvidia_triton_profile")
    if delete_response is not None:
        print("Delete Profile Response:", delete_response)

if __name__ == "__main__":
    test_zededa_controller()
