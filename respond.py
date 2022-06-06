from mitmproxy import http


def request(flow: http.HTTPFlow) -> None:
    # `run with the following`
    # mitmproxy --no-server --rfile dumps/$(date +%Y%m%d.%H%M%S.%s.%Z).mitm
    flow.response = http.Response.make(201)
