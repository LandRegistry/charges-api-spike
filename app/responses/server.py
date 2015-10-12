from flask import jsonify, request
from lxml import etree


def register_routes(blueprint):
    @blueprint.route('/response-types', methods=['GET'])
    def get_response():

        if request.headers['Content-Type'] == 'application/json':

            result = {
                "response": "JSON",
            }

            return jsonify(result)

        elif request.headers['Content-Type'] == 'text/xml':
            xhtml = etree.Element("{http://www.w3.org/1999/xhtml}html")
            response = etree.SubElement(xhtml,
                                        "{http://www.w3.org/1999/xhtml}body")
            response.text = "XML"

            return(etree.tostring(xhtml, pretty_print=True))
        else:
            return "415 Unsupported Media Type"
