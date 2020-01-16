#!/usr/bin/env python3
from flask import Flask, request, redirect, session, render_template, url_for, flash, send_file
import os
import uuid
from datetime import datetime
from subprocess import Popen, PIPE, CalledProcessError, TimeoutExpired
import re
import socket

application = Flask(__name__)

### Configuration ###
checkCmd = "testssl.sh/testssl.sh"
checkArgs = ["-D"]#["--quiet"]
resultDir = "htmlResult"
sessionId = str(uuid.uuid1())
resultHTMLName = sessionId + ".html"
checkTimeout = 1500 #25mins
rendererCmd = "aha"
rendererArgs = ["-n"]
rendererTimeout = 30
protocols = ["ftp"]
reHost = re.compile("^[a-zA-Z0-9_][a-zA-Z0-9_\-]+(\.[a-zA-Z0-9_\-]+)*$")
preflightRequest = True
preflightTimeout = 10
application.debug = False
application.secret_key = 'dhi'
#####################

@application.route("/", methods=['GET', 'POST', 'DOWNLOAD'])
def main():
    if request.method == 'GET':                         # Main Page
        return render_template("main.html")
    elif request.method == 'POST':                      # Perform Test
        ok = True
        host = request.form['hostName']
        if not reHost.match(host):
            flash("Invalid Host!")
            ok = False

        try:
            port = int(request.form['portNo'])
            if not (port >= 0 and port <= 65535):
                flash("Invalid port!")
                ok = False
        except:
            flash("Hmm.. Smart Move!")
            ok = False

        if ok and preflightRequest:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(preflightTimeout)
                s.connect((host, port))
                s.close()
            except:
                flash("Connection failed!")
                ok = False

        if not ok:
            return redirect(url_for('main'))

        args = [checkCmd]
        args += checkArgs
        args.append(host + ":" + str(port))

        output = b""
        try:
            session['itsNeeded'] = sessionId
            check = Popen(args, stdout=PIPE, stderr=PIPE)
            output, err = check.communicate(timeout=checkTimeout)
            if check.returncode != 0:
                output = err
                flash("Scan failed!")
        except TimeoutExpired as e:
            flash("Scan timed out!")
            check.terminate()

        html = "<pre>" + str(output, 'utf-8') + "</pre>"
        try:
            renderer = Popen([rendererCmd], stdin=PIPE, stdout=PIPE, stderr=PIPE)
            html, err = renderer.communicate(input=output, timeout=rendererTimeout)
            if renderer.returncode != 0:
                html = "<pre>" + str(err, 'utf-8') + "</pre>"
                flash("AHA failed!")
        except TimeoutExpired as e:
            flash("AHA timed out!")
            renderer.terminate()

        ###Download###
        try:
            timeStamp = datetime.now()
            resultHTMLName = sessionId + ".html"
            resultFile = open(resultDir + "/" + resultHTMLName, mode = 'w')
            teststring1 = "<!DOCTYPE html><html><head><title>TLSWebScanner - Scan Result</title><link rel='stylesheet' href='https://stackpath.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css'></head><body style='margin: 0 15px'><div class='navbar-left logo' style='margin: 20px 20px'><img src='https://www.nielsen.com/wp-content/themes/nielsen-base/dist/images/n-tab@2x.png' height='38px' /></div><div class='navbar-left'><h2 class='brand brand-name navbar-left'>TLSWebScanner - Scan Result</h2></div><div class='container pt-3'></div><div style='margin: 0 10px'>"
            teststring2 = str(html.decode('utf-8'))
            teststring3 = "</div></body></html>"
            resultFile.write( teststring1 + teststring2 + teststring3 )
            resultFile.close()
            #resultFileLocation = "/" + resultDir + resultHTMLName
        except:
            pass

        return render_template("scanres.html", result=str(html, 'utf-8'))

@application.route('/download/')
def download():
    forThis = session.get('itsNeeded', None)
    return send_file('/var/www/html/d_dev/testsslsh/htmlResult/' + forThis + '.html', as_attachment=True)

if __name__ == "__main__":
    application.run()
