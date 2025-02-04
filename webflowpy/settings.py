import os

"""API Access Token. Generated by Webflow under Dashboard > Project Settings > Integrations > API Access"""
token = os.environ.get("WEBFLOW_ACCESS_TOKEN", "")

"""max number of retries after 500 or 429 error """
retries = 3

"""{backoff factor} * (2 ^ ({number of total retries} - 1)) delay after unsuccessfull 500 or 429 requests"""
backoff_factor = 20
