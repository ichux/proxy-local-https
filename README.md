## Proxy Local HTTPS
This project uses `uvicorn` to demonstrate:
- how to send a post request to `OpenSearch`
- use self generated certificate with it `uvicorn`
- send direct requests to `uvicorn` through `curl`
- proxy requests to `uvicorn` through `mitmproxy`
- how to use all generated pem/key files

## Assumptions made:
- You have your environment set up and in a virtual environment
- You have an OpenSearch node or cluster running on https://localhost:9200
- Minimum `Python` version: *3.10*
- Your port `18080` is accessible, else, replace it with `$RANDOM`
- If you replaced your port with `$RANDOM`, be sure to replace it with the real value when you see `18080`

## Set up
1. Activate your virtual environment
2. Do pip install -r requirements.txt
3. run 
```bash

mkdir -p ssl && rm -f joined.pem && \
    cd ssl && python -m trustme && \
    cat server.key server.pem > keycert.pem \
    && cd ..
```
4. Follow the processes listed below

```bash
# On one terminal run this
uvicorn --ssl-certfile ssl/keycert.pem app:app

# On another terminal run this for port 18080
mitmproxy --save-stream-file dumps/$(date +%Y%m%d.%H%M%S.%s.%Z).mitm \
    --listen-port 18080 \
    --console-layout vertical \
    --console-layout-headers \
    --set connection_strategy=lazy \
    --set console_focus_follow=true \
    --set console_palette=light \
    --set ssl_verify_upstream_trusted_ca=ssl/client.pem

# Or run this, on another terminal, for a random port. 
# And if you used this, change where you see 18080 
# to the system chosen random port number
mitmproxy --save-stream-file dumps/$(date +%Y%m%d.%H%M%S.%s.%Z).mitm \
    --listen-port $RANDOM \
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

## High concurrency: Local
```bash

# run this to spread to all the CPUs running on a PC
uvicorn --ssl-certfile ssl/keycert.pem \
    --workers $(echo `python3 -c "import os; print(os.cpu_count())"`) \
    app:app
```

## High concurrency: Production
```bash
pip install gunicorn

gunicorn --preload --certfile ssl/keycert.pem \
    app:app \
    -w $(echo `python3 -c "import os; print(os.cpu_count())"`) \
    -k uvicorn.workers.UvicornWorker
```

## Manual Testing
To test manually while the app is running, you can send a lot of requests with `curl`.

```bash

# without proxy
for i in {1..1000}; do \
    curl -XPOST --cacert ssl/client.pem \
    https://127.0.0.1:8000 \
    -d "{\"id\": $i, \"data\": $RANDOM}";
done

# with proxy
mitmproxy --save-stream-file dumps/$(date +%Y%m%d.%H%M%S.%s.%Z).mitm \
    --listen-port 18080 \
    --console-layout vertical \
    --console-layout-headers \
    --set connection_strategy=lazy \
    --set console_focus_follow=true \
    --set console_palette=light \
    --set ssl_verify_upstream_trusted_ca=ssl/client.pem

for i in {1..3}; do \
    curl -XPOST --insecure --proxy \
    http://127.0.0.1:18080 https://127.0.0.1:8000 \
    -d "{\"id\": $i, \"data\": $RANDOM}";
done

# generate errors to see how the logger works
for i in {1..3}; do \
    curl -XPOST --cacert ssl/client.pem \
    https://127.0.0.1:8000 \
    -d '{"id": $i, "data": $RANDOM}';
done
```
