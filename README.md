# Valid_Proxy_Checker
 Valid Proxy Checker is a cross-platform software which is able to find out valid proxies from a list of .txt format of proxies. 
![image alt](https://github.com/Fouad-Showmik/Valid_Proxy_Checker/blob/a1e81722764e32e1bdd6bae7fa767daeb0558c06/UI.jpg)

The software tries to make a request to a test URL, using the proxy with a short timeout (timeout=5). If the request succeeds (status code == 200), the proxy is valid. If it fails (timeout, connection error, etc.), the proxy is invalid.

