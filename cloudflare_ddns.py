from enum import Enum
import json
import os
import requests
import socket
import os

import logging


SUCCESS = 'good'               # Update successfully
NO_HOSTNAME = 'nohost'         # The hostname specified does not exist in this user account
HOSTNAME_INCORRECT = 'notfqdn' # The hostname specified is not a fully-qualified domain name
AUTH_FAILED = 'badauth'        # Authenticate failed
DDNS_FAILED = '911'            # There is a problem or scheduled maintenance on provider side
BAD_HTTP_REQUEST = 'badagent'  # HTTP method/parameters is not permitted
BAD_PARAMS = 'badparam'        # Bad params

def get_ip() -> str:
    """
    get the ip address of whoever executes the script
    """
    #ip = requests.get('https://api.ipify.org').content.decode('utf8')
    ip = requests.get('https://checkip.amazonaws.com').text.strip()
    #ip = requests.get('http://myip.dnsomatic.com').text.strip()
    return ip

def list_dns_records(zone_id, api_key, **kwargs):
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    query_params = "&".join([f"{k}={v}"  for k,v in kwargs.items()])
    if(query_params != ""):
        url = f"{url}?{query_params}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logging.error(f"Error retrieving DNS record.")
        logging.error(f"url={url}")
        logging.error(f"headers={headers}")
        logging.error(f"response.status_code={response.status_code}")
        logging.error(json.dumps(json.loads(response.content), indent = 2))
    return response.content.decode('utf8')

def update_dns_record(zone_id, api_key, record_id, **kwargs):
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = json.dumps(kwargs)
    response = requests.patch(url, headers=headers, data=payload)
    if response.status_code != 200:
        logging.error(f"Error patching DNS record {record_id}")
        logging.error(f"url={url}")
        logging.error(f"headers={headers}")
        logging.error(f"data={payload}")
        logging.error(f"response.status_code={response.status_code}")
        logging.error(json.dumps(json.loads(response.content), indent = 2))
    return response.content.decode('utf8')

if __name__ == "__main__":
    import sys

    # Set logger
    logging.getLogger().handlers.clear()
    fileHandler = logging.FileHandler(__file__.replace(".py",".log"))
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    fileHandler.setFormatter(logFormatter)
    logging.getLogger().addHandler(fileHandler)
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    #logging.getLogger().addHandler(consoleHandler) #only word printed on console must be exit status

    logging.getLogger().setLevel(logging.INFO)

    # Synology passes 5 arguments in order:
    # 0 - not in use
    # 1 - username => zone_id
    # 2 - password => Cloudflare API token
    # 3 - hostname => Comment filter
    # 4 - IPv4     => Synology provided IPv4

    zone_id=sys.argv[1] if len(sys.argv)>1 else os.getenv("CLOUDFLARE_ZONE_ID")
    api_key=sys.argv[2] if len(sys.argv)>2 else os.getenv("CLOUDFLARE_API_KEY")
    comment_filter = sys.argv[3] if len(sys.argv)>3 else "BxDDNS"
    public_ip = sys.argv[4] if len(sys.argv)>4 else get_ip()

    logging.info(f"Public IP: {public_ip}")
    logging.info(f"Comment Filter:{comment_filter}")
    res = list_dns_records(zone_id, api_key,type="A",comment=comment_filter)
    data = json.loads(res)
    err=False
	
    if(data.get("success", False)):
        for r in data["result"]:
            log = f'{r["type"]} {r["name"]} > {r["content"]} ({r["comment"]})'
            if(r["content"] != public_ip):
                log += f' => Patching with {public_ip}...'
                up_res = json.loads(update_dns_record(zone_id, api_key,r["id"], content=public_ip))
                if data.get("success", False):
                    log += "...Done"
                else:
                    log += "...ERROR occured"
                    err = True
            else:
                log += " => Up to date."
            logging.info(log)
    else:
        if("errors" in data and len(data["errors"]) >0 and "code" in data["errors"][0]):
            errcode = data["errors"][0]["code"]
            if( errcode == 7003):
                print(BAD_HTTP_REQUEST)
            elif(errcode  == 10000):
                print(AUTH_FAILED)
        else:
            print(AUTH_FAILED)
        exit(1)
        
    if(err):
        print(DDNS_FAILED)
        exit(1)
    print(SUCCESS)
    exit(0)