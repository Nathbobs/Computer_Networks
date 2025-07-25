# Get all asset balances.

import http.client
import urllib.request
import urllib.parse
import hashlib
import hmac
import base64
import json
import time

#main function to place a sell request and print the response.

def main():
   response = request(
      method="POST",
      path="/0/private/Balance",
      public_key="",
      private_key="",
      environment="https://api.kraken.com",
   )
   print(response.read().decode())
#the full http request is made here with the method, path, query, body, public key, private key and environment.
#it also returns an HTTPResponse object that contains the server reply.
def request(method: str = "GET", path: str = "", query: dict | None = None, body: dict | None = None, public_key: str = "", private_key: str = "", environment: str = "") -> http.client.HTTPResponse:
   url = environment + path
   query_str = ""
   if query is not None and len(query) > 0:
      query_str = urllib.parse.urlencode(query)
      url += "?" + query_str
   nonce = ""
   if len(public_key) > 0:
      if body is None:
         body = {}
      nonce = body.get("nonce")
      if nonce is None:
         nonce = get_nonce()
         body["nonce"] = nonce
   headers = {}
   body_str = ""
   if body is not None and len(body) > 0:
      body_str = json.dumps(body)
      headers["Content-Type"] = "application/json"
   if len(public_key) > 0:
      headers["API-Key"] = public_key
      headers["API-Sign"] = get_signature(private_key, query_str+body_str, nonce, path)
   req = urllib.request.Request(
      method=method,
      url=url,
      data=body_str.encode(),
      headers=headers,
   )
   return urllib.request.urlopen(req)

def get_nonce() -> str:
   return str(int(time.time() * 1000)) #counts the time used for each API calls 


#this function generates a signature for the request and cross checks to prove that you are the owner of the private key.
def get_signature(private_key: str, data: str, nonce: str, path: str) -> str:
   return sign(
      private_key=private_key,
      message=path.encode() + hashlib.sha256(
            (nonce + data)
         .encode()
      ).digest()
   )
#secret key is decoded here and an API-Sign header is generated using HMAC-SHA512.
def sign(private_key: str, message: bytes) -> str:
   return base64.b64encode(
      hmac.new(
         key=base64.b64decode(private_key),
         msg=message,
         digestmod=hashlib.sha512,
      ).digest()
   ).decode()


if __name__ == "__main__":
   main()