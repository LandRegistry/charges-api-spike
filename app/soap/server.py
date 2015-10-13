from pysimplesoap.server import SoapDispatcher, SOAPHandler
from http.server import HTTPServer
import requests


def get_cases(request):
    case_endpoint = "http://0.0.0.0:9070/case"
    return requests.get(case_endpoint).json()


dispatcher = SoapDispatcher(
    'my_dispatcher',
    location="http://0.0.0.0:8008/",
    action='http://0.0.0.0:8008/',
    namespace="http://example.com/sample.wsdl", prefix="ns0",
    trace=True,
    ns=True)

# register the user function
dispatcher.register_function('get_cases', get_cases,
                             returns={'Cases': str})

print("Starting server...")
httpd = HTTPServer(("", 8008), SOAPHandler)
httpd.dispatcher = dispatcher
httpd.serve_forever()
