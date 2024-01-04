# application.py - Script to create main Flask website
#
# Date: 20210608
# Author(s): Philip

# Import Python dependencies
import os
import datetime

# Import external dependencies
import werkzeug
import stripe
from dotenv import load_dotenv
from shapely.geometry import Point
from sqlalchemy import text
from flask_session import Session
from flask import (
    Flask, session, render_template, request, 
    jsonify, redirect, url_for, flash, 
    make_response, abort, make_response
)

# Import local dependencies
import omnibus.passworder as pwd
from omnibus.queryc import SourceQuery, ElevationPointQuery, ElevationPointsQuery
from omnibus.config import source
from omnibus.database import db
from omnibus.query import load_json, inside_region, find_tile, open_image


# Configure session to use filesystem

app = Flask(__name__)
load_dotenv()

app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

if app.debug:
    # Test
    stripe.api_key = os.getenv('DEBUG_STRIPE_KEY')
    price_1 = os.getenv('DEBUG_STRIPE_PRICE_1')
    backurl = os.getenv('DEBUG_STRIPE_BACKURL')
else:
    # Live
    stripe.api_key = os.getenv('STRIPE_KEY')
    price_1 = os.getenv('STRIPE_PRICE_1')
    backurl = os.getenv('STRIPE_BACKURL')


# Check Configuration section for more details
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = "filesystem"
Session(app)

app.secret_key = os.getenv('FLASK_SECRET')

@app.route("/")
def index():
    if 'userid' in session:
        return render_template("index_profile.html")
    return render_template("index.html")


#--------------------------------------------------------------
# 1. Login functions
#--------------------------------------------------------------


@app.route("/user/login/")
def show_login():
    return render_template("user/login.html")

@app.route("/user/login/perform", methods=["POST"])
def do_login():
    email = request.form.get("email")
    pw1 = request.form.get("password")

    loguser = db.execute(text(
        "SELECT uid, name, pwdsalt, pwdkey FROM account WHERE email = :email"), 
        {"email": email}).first()
    db.remove()
    
    if not loguser:
        flash("Error: The provided email or password is not valid.")
        return redirect(url_for("show_login"))

    userid = loguser[0]
    name_msg = loguser[1]
    salt = loguser[2]
    key = loguser[3]

    if pwd.pwd_check(pw1, key, salt):
        session['userid'] = userid
        session['user_name'] = name_msg
        session['user_email'] = email
        #print(session)
        return redirect(url_for("show_account"))
    else:
        flash("Error: The provided email or password is not valid.")
        return redirect(url_for("show_login"))

@app.route("/user/signup/")
def show_signup():
    return render_template("user/signup.html")

@app.route("/user/signup/perform", methods=["POST"])
def do_signup():
    name = request.form.get("name") 
    email = request.form.get("email")
    pw1 = request.form.get("pw1")
    pw2 = request.form.get("pw2")

    salt = pwd.pwd_salt()
    key = pwd.pwd_hash(pw1, salt)
    utctime = str(datetime.datetime.utcnow())[:19]


    try:
        assert pwd.pwd_len(pw1)
        assert pwd.pwd_id(pw1, pw2)
    except AssertionError:
        #flash("Error: Weak or invalid password, please try again.")
        return redirect(url_for("show_signup"))

    emailno = db.execute(text(
        "SELECT * FROM account WHERE email = :var1"), 
        {"var1": email}).rowcount
    if emailno > 0:
        flash("Error: This email is already in use")
        return redirect(url_for("show_signup"))
    else:
        db.execute(text(
            "INSERT INTO account (name, email, pwdkey, pwdsalt, date_created) VALUES (:name, :email, :key, :salt, :datec)"), 
            {"name": name, "email": email, "key": key, "salt": salt, "datec": utctime })
        db.commit()
        db.remove()
   
    # Auto-create a Free plan account
    utest = db.execute(text("SELECT * FROM account WHERE email = :var1"), {"var1": email}).first()
    #print(utest)
    uid = utest[0]
    db.remove()

    # Create Stripe customer
    try:
        customer = stripe.Customer.create(
            name=name,
            email=email,
            description=f"Customer #{uid}",
        )
    except Exception:
        print("Email was not in email format")
        abort(500)

    db.execute(text("INSERT INTO payment (uid, current_plan, stripe_cust_id) VALUES (:var1, :var2, :var3)"), 
        {"var1": uid, "var2": "free", "var3": customer['id']})
    db.commit()
    db.remove()

    flash("Success: Your profile has been made!")
    return redirect(url_for("show_login"))

@app.route("/user/logout/perform", methods=["POST"])
def do_logout():
    session.clear()
    session.pop('_flashes', None)
    return redirect(url_for("index"))


#--------------------------------------------------------------
# 2. Profile
#--------------------------------------------------------------


@app.route("/user/profile/" )
def show_account():
    if 'userid' not in session:
        return redirect(url_for("show_login"))

    if 'note' not in session:
        return render_template("user/profile/account.html", user=session['user_name'], email=session['user_email'])
    else:
        message = session.pop('note')
        return render_template("user/profile/account.html", user=session['user_name'], email=session['user_email'], message=message)

@app.route("/user/profile/update/", methods=["POST"])
def do_account_edit():
    if 'userid' not in session:
        return redirect(url_for("show_login"))

    email = request.form.get('email')
    name = request.form.get('name')

    try:
        if name != session['user_name']:
            db.execute(text("UPDATE account SET name = :var1 WHERE uid = :var2"), {"var1": name, "var2": session['userid']})
            db.commit()
            db.remove()
            session['user_name'] = name

        if email != session['user_email']:
            db.execute(text("UPDATE account SET email = :var1 WHERE uid = :var2"), {"var1": email, "var2": session['userid']})
            db.commit()
            db.remove()
            session['user_email'] = email

        session['note'] = "Successful change"
        return redirect(url_for("show_account"))
    
    except Exception as e:
        print("Something went wrong: {e}")
        session['note'] = "Something went wrong"
        return redirect(url_for("show_account"))


@app.route("/user/profile/plan/")
def show_payment_plan():
    if 'userid' not in session:
        return redirect(url_for("show_login"))

    # Check if subscription is active, else change
    subid = db.execute(text("SELECT stripe_sub_id FROM payment WHERE uid = :var1"), {"var1": session['userid']}).first()
    db.remove()

    if not subid:
        abort(404)

    subid = subid[0]
    
    if subid != None and subid != "0":
        sub = None
        canceldate = None

        try:
            sub = stripe.Subscription.retrieve(subid)
            canceldate = datetime.datetime.utcfromtimestamp(sub['current_period_end']).strftime('%d %b %Y')
        except Exception as e:
            print(e)
            abort(404)

        currentdate = datetime.datetime.utcnow().timestamp()
        if currentdate <= (sub['current_period_end'] + 3600):
            plan = db.execute(text("SELECT current_plan FROM payment WHERE uid = :var1"), {"var1": session['userid']}).first()
            db.remove()
            
            if not plan:
                abort(404)
            return render_template("user/profile/plan.html", user=session['user_name'], planType=plan[0], cancel=canceldate)
        else:
            print("Status of sub:" + sub['status'])
            db.execute(text("UPDATE payment SET current_plan = :var0, stripe_sub_id = :var1, stripe_paid = :var2 WHERE uid = :var_uid"), 
                {"var0": "free", "var1": "0", "var2": "0", "var_uid": session['userid']})
            db.commit()
            db.remove()
            return redirect(url_for("show_payment_plan"))

    else:
        plan = db.execute(text("SELECT current_plan FROM payment WHERE uid = :var1"), {"var1": session['userid']}).first()
        db.remove()
        
        if not plan:
            abort(404)
        
        return render_template("user/profile/plan.html", user=session['user_name'], planType=plan[0], priceBasic=price_1)


@app.route("/user/profile/plan/cancel/", methods=['POST'])
def show_cancel_plan():
    if 'userid' not in session:
        return redirect(url_for("show_login"))


    subid = db.execute(text("SELECT stripe_sub_id FROM payment WHERE uid = :var1"), {"var1": session['userid']}).first()

    if not subid:
        abort(404)

    subid = subid[0]
    stripe.Subscription.modify(
        subid,
        cancel_at_period_end=True,
    )

    canceldate = datetime.datetime.utcfromtimestamp(stripe.Subscription.retrieve(subid)['current_period_end']).strftime('%d %b %Y')

    db.execute(text("UPDATE payment SET current_plan = :var1, stripe_paid = :var0 WHERE uid = :var_uid"), 
        {"var1": "basic_cancel", "var0": "cancel", "var_uid": session['userid']})
    db.commit()

    plan = db.execute(text("SELECT current_plan FROM payment WHERE uid = :var1"), {"var1": session['userid']}).first()[0]
    #db.execute("INSERT INTO payment (uid, current_plan) VALUES (:var1, :var2)", {"var1": uid, "var2": "free"})
    #db.commit()
    db.remove()

    return render_template("user/profile/plan.html", user=session['user_name'], planType=plan, cancel=canceldate, priceBasic=price_1)


@app.route('/payment/checkout/', methods=['POST'])
def do_checkout():
    price = request.form.get('priceId')
    #domain_url = os.getenv('DOMAIN')

    #print(domain_url)

    cust = db.execute(text("SELECT stripe_cust_id FROM payment WHERE uid = :var1"), {"var1": session['userid']}).first()
    db.remove()

    if not cust:
        abort(500)

    cust = cust[0]
    try:
        # Create new Checkout Session for the order
        # Other optional params include:
        # [billing_address_collection] - to display billing address details on the page
        # [customer] - if you have an existing Stripe Customer ID
        # [customer_email] - lets you prefill the email input in the form
        # [automatic_tax] - to automatically calculate sales tax, VAT and GST in the checkout page
        # For full details see https://stripe.com/docs/api/checkout/sessions/create

        # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
        checkout_session = stripe.checkout.Session.create(
            success_url=backurl + '/payment/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=f'{backurl}/payment/cancel',
            mode='subscription',
            customer=cust,
            # automatic_tax={'enabled': True},
            payment_method_types=[
                "card",
            ],
            line_items=[{
                'price': price,
                'quantity': 1
            }],
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return jsonify({'error': {'message': str(e)}}), 400


@app.route("/payment/success")
def checkout_success():

    #print(request.args)
    info = stripe.checkout.Session.retrieve(request.args.get('session_id'))
    subid = info['subscription']
    sub = stripe.Subscription.retrieve(subid)

    db.execute(text("UPDATE payment SET current_plan = :var0, stripe_sub_id = :var1, stripe_paid = :var2 WHERE uid = :var_uid"), 
        {"var0": "basic", "var1": subid, "var2": sub['status'], "var_uid": session['userid']})
    db.commit()
    db.remove()

    return render_template("user/profile/success.html", user=session['user_name'])


@app.route("/payment/cancel/")
def checkout_cancel():
    if 'userid' not in session:
        return redirect(url_for("show_login"))

    return render_template("user/profile/cancel.html", user=session['user_name'])


@app.route("/user/profile/history")
def show_payment_history():
    if 'userid' not in session:
        return redirect(url_for("show_login"))

    cust = db.execute(text("SELECT stripe_cust_id FROM payment WHERE uid = :var1"), {"var1": session['userid']}).first()
    db.remove()
    
    if not cust:
        abort(404)

    cust = cust[0]
    invoices = stripe.Invoice.list(customer=cust)

    data = []
    for i in invoices['data']:
        name = stripe.Product.retrieve(i['lines']['data'][0]['plan']['product'])['name']
        date = datetime.datetime.utcfromtimestamp(i['status_transitions']['paid_at']).strftime('%d %b %Y')
        data.append([ date, name, "€{0:.2f}".format(float(i['total']) / 100), i['status']])

    return render_template("user/profile/history.html", user=session['user_name'], data=data)


@app.route("/user/profile/usage/")
def show_api_usage():
    if 'userid' not in session:
        return redirect(url_for("show_login"))

    return render_template("user/profile/usage.html", user=session['user_name'])


@app.route("/user/profile/keys/")
def show_api_keys():
    if 'userid' not in session:
        return redirect(url_for("show_login"))

    keylist = db.execute(text("SELECT * FROM apikey WHERE uid = :var1"), {"var1": session["userid"]}).all()
    db.remove()
    return render_template("user/profile/keys.html", user=session['user_name'], keylist=keylist)


@app.route("/user/profile/keys/create/", methods=["POST"])
def do_keygen():
    if 'userid' not in session:
        return redirect(url_for("show_login"))

    uid = session['userid']
    name = request.form.get("keyname")
    date_created = str(datetime.datetime.utcnow())[:19]
    date_modified = str(datetime.datetime.utcnow())[:19]
    scope = ""

    prefix = pwd.api_key(7)
    suffix = pwd.api_key(32)
    hashed_suffix = pwd.pwd_hash(suffix)

    apikey = f"{prefix}.{suffix}"
    final_key = f"{prefix}.{hashed_suffix}"

    #print(final_key)

    db.execute(text("INSERT INTO apikey (uid, name, apikey, date_created, date_modified, scope) " +
        "VALUES (:var1, :var2, :var3, :var4, :var5, :var6)"), 
        { "var1": uid, "var2": name, "var3": final_key, "var4": date_created, "var5": date_modified, "var6": scope})
    db.commit()
    keylist = db.execute(text("SELECT * FROM apikey WHERE uid = :var1"), {"var1": session["userid"]}).all()
    db.remove()
    return render_template("user/profile/keys.html", user=session['user_name'], keylist=keylist, onekey=apikey)


@app.route("/user/profile/keys/delete/<keydel>/", methods=["POST"])
def do_keydel(keydel):
    if 'userid' not in session:
        return redirect(url_for("show_login"))

    #print(keydel)
    db.execute(text("DELETE FROM apikey WHERE uid = :var1 AND name = :var2"), {"var1": session['userid'], "var2": keydel})
    db.commit()
    db.remove()
    return redirect(url_for('show_api_keys'))


@app.route("/documentation/")
def show_docs():
    if 'userid' not in session:
        return render_template("docs.html", logged=False)
    
    return render_template("docs.html", logged=True)



@app.errorhandler(404)
def not_found(e):
    """Page not found."""
    print(e)
    return make_response(
        render_template("404.html"),
        404
     )

# Sample API ENDPOINTS
# 127.0.0.1:5000/api/v1/elevation/points?via=160237,416055|153002,436102|250023,554031&key=ASFD
# 127.0.0.1:5000/api/v1/elevation/points?via=160237,416055|153002,436102|250023,554031&key=kOUdTgM.iCJDgNOGwuXY7bg6TSrnb9hHZOAyryRv
# "demapi.com/api/v1/elevation/point?via=160000,418750&key=ASDFASDF&dataset=ahn_dsm_5m&crs=wgs84"
#     via
#     crs (wgs84 / rd)
#     key
#     dataset
# "demapi.com/api/v1/elevation/points?rd=160000,418750|"
# "demapi.com/api/v1/elevation/line?rd="

# "demapi.com/api/v1/sources?"
#     location
#     key


# "demapi.com/api/v1/health"
# "demapi.com/api/v1/status?id="
#     id
#     key

# "?rd=x,y"
# "?dataset=NLD_DSM"
# "?key=SADFADSF"

# dataset
# via
# crs
# key
# id


@app.route("/api/v1/elevation/<string:feature>")
def elevation(feature):
    if feature == "point": 
        point_query = ElevationPointQuery(request.args)
        point_query.process()
        return jsonify(point_query.response)
    elif feature == "points":
        points_query = ElevationPointsQuery(request.args)
        points_query.process()
        return jsonify(points_query.response)
    elif feature == "line":
        reply["status"] = "UNKNOWN_ERROR"
        reply["messages"] = "API endpoint not yet implemented"
        return jsonify(reply)
    elif feature == "polygon":
        reply["status"] = "UNKNOWN_ERROR"
        reply["messages"] = "API endpoint not yet implemented"
        return jsonify(reply)
    else:
        return render_template('404.html'), 404
    #return "<h1> " + feature + " " + str(request.args) + " " + str(request.__dict__) +  " </h1><p></p>"


@app.route("/api/v1/sources")
def sources():
    source_query = SourceQuery(request.args)
    source_query.process()
    return jsonify(source_query.response)