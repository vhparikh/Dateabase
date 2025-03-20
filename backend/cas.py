from flask import Flask, redirect, request, session, url_for
from cas import CASClient
import os

app = Flask(__name__)

# Use environment variable for secret key in production
app.secret_key = os.environ.get("SECRET_KEY", "super_secure_key")  

# Tell python-cas how to find Princeton's CAS:
cas_client = CASClient(
    version=3,
    server_url="https://fed.princeton.edu/cas/",
    service_url="http://localhost:5050/login?next=%2Fprofile"
)

@app.route("/")
def home():
    """ Main page that requires CAS authentication """
    if "netid" not in session:
        return redirect(url_for("login"))
    return f"Welcome, {session['netid']}! <br><a href='/logout'>Logout</a>"

@app.route("/login")
def login():
    """ Redirect to CAS login & validate user """
    ticket = request.args.get("ticket")

    # If no ticket, we haven't gone to CAS yet
    if not ticket:
        login_url = cas_client.get_login_url()
        print("Redirecting to CAS login URL:", login_url)
        return redirect(login_url)

    # Verify the ticket from CAS
    netid, attributes, pgtiou = cas_client.verify_ticket(ticket)
    if netid:
        session["netid"] = netid
        return redirect(url_for("home"))

    return "CAS authentication failed. Please try again."

@app.route("/logout")
def logout():
    """ Logs out user from both CAS and local session """
    session.pop("netid", None)
    logout_url = cas_client.get_logout_url()
    print("Redirecting to CAS logout URL:", logout_url)
    return redirect(logout_url)

if __name__ == "__main__":
    app.run(host="localhost", port=5050, debug=True)