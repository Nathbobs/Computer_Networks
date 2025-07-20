// Get all asset balances.

package main

import (
	"bytes"
	"crypto/hmac"
	"crypto/sha256"
	"crypto/sha512"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"time"
)

// Main function to get account balance and print the response.
func main() {
	resp, err := request(&Request{
		Method:      "POST",
		Path:        "/0/private/Balance",
		PublicKey:   "",
		PrivateKey:  "",
		Environment: "https://api.kraken.com",
	})
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	data, err := io.ReadAll(resp.Body)
	if err != nil {
		panic(err)
	}
	fmt.Printf("%s\n", data)

}

// Request struct defines the parameters for the API request.
type Request struct {
	Method      string
	Path        string
	Query       map[string]any
	Body        map[string]any
	PublicKey   string
	PrivateKey  string
	Environment string
}

// request function constructs and sends the HTTP request to the Kraken API.
func request(c *Request) (*http.Response, error) {
	url := c.Environment + c.Path
	var queryString string
	if len(c.Query) > 0 {
		queryValues, err := mapToURLValues(c.Query)
		if err != nil {
			return nil, fmt.Errorf("query to URL values: %s", err)
		}
		queryString = queryValues.Encode()
		url += "?" + queryString
	}
	var nonce any // Initialize nonce variable
	bodyMap := c.Body
	if len(c.PublicKey) > 0 {
		if bodyMap == nil {
			bodyMap = make(map[string]any)
		}
		var ok bool
		nonce, ok = bodyMap["nonce"]
		if !ok {
			nonce = getNonce()
			bodyMap["nonce"] = nonce
		}
	}
	headers := make(http.Header)
	var bodyReader io.Reader
	var bodyString string
	if len(bodyMap) > 0 {
		bodyBytes, err := json.Marshal(bodyMap)
		if err != nil {
			return nil, fmt.Errorf("json marshal: %s", err)
		}
		bodyString = string(bodyBytes)
		bodyReader = bytes.NewReader(bodyBytes)
		headers.Set("Content-Type", "application/json")
	}
	request, err := http.NewRequest(c.Method, url, bodyReader)
	if err != nil {
		return nil, fmt.Errorf("http new request: %s", err)
	}
	if len(c.PublicKey) > 0 {
		signature, err := getSignature(c.PrivateKey, queryString+bodyString, fmt.Sprint(nonce), c.Path)
		if err != nil {
			return nil, fmt.Errorf("get signature: %s", err)
		}
		headers.Set("API-Key", c.PublicKey)
		headers.Set("API-Sign", signature)
	}
	request.Header = headers
	return http.DefaultClient.Do(request)
}

// getNonce generates a nonce based on the current time in milliseconds.
func getNonce() string {
	return fmt.Sprint(time.Now().UnixMilli())
}

// getSignature computes the HMAC signature for the request using the private key, data, nonce, and path.
func getSignature(privateKey string, data string, nonce string, path string) (string, error) {
	message := sha256.New()
	message.Write([]byte(nonce + data))
	return sign(privateKey, []byte(path+string(message.Sum(nil))))
}

// sign computes the HMAC signature using the provided private key and message.
func sign(privateKey string, message []byte) (string, error) {
	key, err := base64.StdEncoding.DecodeString(privateKey)
	if err != nil {
		return "", err
	}
	hmacHash := hmac.New(sha512.New, key)
	hmacHash.Write(message)
	return base64.StdEncoding.EncodeToString(hmacHash.Sum(nil)), nil
}

// mapToURLValues converts a map of string keys to values of type any into url.Values.
func mapToURLValues(m map[string]any) (url.Values, error) {
	uv := make(url.Values)
	for k, v := range m {
		switch v := v.(type) {
		case []string:
			uv[k] = v
		case string:
			uv[k] = []string{v}
		default:
			j, err := json.Marshal(v)
			if err != nil {
				return nil, err
			}
			uv[k] = []string{string(j)}
		}
	}
	return uv, nil
}
