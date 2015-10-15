import os

#todo does this "debug" do anything?
debug = True

#Error & Event Log (uses python logging module)
error_log_format = '%(asctime)s HOFM %(name)s module:%(module)s line:%(lineno)s %(levelname)s "%(message)s"'
event_log_format = '%(asctime)s HOFM %(name)s module:%(module)s line:%(lineno)s %(levelname)s "%(message)s"'
error_log_path = "hofm_error.log"
event_log_path = "hofm_event.log"


#Web-server
web_server_is_cherrypy = True

#CherryPy web-server
cherrypy_host = '0.0.0.0'
cherrypy_port = 5001
cherrypy_autoreload = True
cherrypy_log_screen = True

#Flask web-server
flask_debug = True
flask_host = '0.0.0.0'
flask_port = 5001
flask_processes = 4


#Database Connection
##Connection for Dev normal
#print os.environ['HOFM_PASS']
connection_postgres = "host='" + os.environ['HOFM_HOST'] + \
                      "' port='" + os.environ['HOFM_PORT'] + \
                      "' dbname='" + os.environ['HOFM_DBNAME'] + \
                      "' user='" + os.environ['HOFM_USER'] +\
                      "' password='" + os.environ['HOFM_PASS'] + "'"
##Connection for Dev CentOS
#connection_postgres = "host='HH-HOFM-AP21.lnx.lr.net' port='5432' dbname='HOFM' user='postgres'  password='password'"



#Login
CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'
LDAPSRV = 'DITI.LR.NET'

LOGIN_URL = '/login'
LOGIN_REDIRECT_URL = '/index'



#?
#basedir = os.path.abspath(os.path.dirname(__file__))
