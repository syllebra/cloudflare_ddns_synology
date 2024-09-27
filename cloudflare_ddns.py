import json
import os
import requests
import socket
import os

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
        print(f"Error retrieving DNS record.")
        print(f"url={url}")
        print(f"headers={headers}")
        print(f"response.status_code={response.status_code}")
        print(json.dumps(json.loads(response.content), indent = 2))
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
        print(f"Error patching DNS record {record_id}")
        print(f"url={url}")
        print(f"headers={headers}")
        print(f"data={payload}")
        print(f"response.status_code={response.status_code}")
        print(json.dumps(json.loads(response.content), indent = 2))
    return response.content.decode('utf8')

if __name__ == "__main__":
    import sys

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

    print("Public IP:",public_ip)
    print("Comment Filter:",comment_filter)
    res = list_dns_records(zone_id, api_key,type="A",comment=comment_filter)
    data = json.loads(res)
    err=False
	
    if(data.get("success", False)):
        for r in data["result"]:
            print(f'{r["type"]} {r["name"]} > {r["content"]} ({r["comment"]})',end="")
            if(r["content"] != public_ip):
                print(f' => Patching with {public_ip}...',end="")
                up_res = json.loads(update_dns_record(zone_id, api_key,r["id"], content=public_ip))
                if data.get("success", False):
                    print("...Done")
                else:
                    print("...ERROR occured")
                    err = True
            else:
                print(" => Up to date.")
    else:
        exit(1)
    if(err):
        exit(1)
    exit(0)
