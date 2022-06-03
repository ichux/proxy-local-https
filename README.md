## Assumptions made:
- You have your environment set up and in a virtual environment
- Minimum Python version: 3.10
- Your port `18080` is accessible, else, replace it with `$RANDOM`.
- If you replaced your port with `$RANDOM`, also be sure to replace it with the real value where you see `18080`.

## Set up
1. Activate your virtual environment
2. Do pip install -r requirements.txt
3. run `mkdir ssl && cd ssl && python -m trustme && cd ..`
4. run `cat ssl/server.key ssl/server.pem > ssl/joined.pem`
5. Follow the below listed processes

```bash
# On one terminal run this
uvicorn --ssl-certfile ssl/joined.pem app:app

# On another terminal run this
mitmproxy --save-stream-file dumps/$(date +%Y%m%d.%H%M%S.%s.%Z).mitm \
    --listen-port 18080 \
    --console-layout vertical \
    --console-layout-headers \
    --set connection_strategy=lazy \
    --set console_focus_follow=true \
    --set console_palette=light \
    --set ssl_verify_upstream_trusted_ca=ssl/client.pem
```

## URL calls
```bash
# hit the https server directly
curl --cacert ssl/client.pem  https://127.0.0.1:8000

# hit the https server through a proxy runnint at port 18080
# be sure to change 18080 to whatever value $RANDOM gave you, assuming you used that option!
curl --insecure --proxy http://127.0.0.1:18080  https://127.0.0.1:8000

# Python version of the above curl request
>> import requests
>> import urllib3
>> urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

>> response = requests.get("https://127.0.0.1:8000",
    proxies={"https": "http://127.0.0.1:18080"},
    verify=False
)

>> response.text
```