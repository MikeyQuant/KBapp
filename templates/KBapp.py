from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import uuid

import os
import plotly
import plotly.express as px
import json

#import stripe
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlalchemy as sql

from flask_bootstrap import Bootstrap
app = Flask(__name__)  # , template_folder= os.path.abspath(r"C:\users\MIKEB\Desktop\Python\Fuhnance\KBtemplates"),static_folder=os.path.abspath(r"C:\users\MIKEB\Desktop\Python\Fuhnance\static"))
app.config['SECRET_KEY'] = 'Skinnybelly22'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://admin:Skinnybelly22@database-3.c9rjcq3tvuan.us-east-1.rds.amazonaws.com:3306/kb'
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
#engine = connection.connect(host="database-3.c9rjcq3tvuan.us-east-1.rds.amazonaws.com", database = 'kb',user="admin", passwd="Skinnybelly22",use_pure=True)

engine = sql.create_engine(
    'mysql://admin:Skinnybelly22@database-3.c9rjcq3tvuan.us-east-1.rds.amazonaws.com:3306/kb')
print(pd.read_sql("select * from users;", engine))
#stripe.api_key = app.config['STRIPE_SECRET_KEY']
BASE_URL = "http://54.243.10.48:8080"


class Users(UserMixin, db.Model):
    user_id = db.Column(db.String(100), primary_key=True)
    user_name = db.Column(db.String(80))
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))
    c_password = db.Column(db.String(80))

    def validate(self, unames, emails, valids):
        punc = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''

        valids.append("")
        name = self.user_name
        for ele in name:
            if ele in punc:
                name = name.replace(ele, "")
        if len(name) != len(self.user_name):
            valids.append("Invalid Username, must not contain any punctuation")
        elif name in unames:
            valids.append("Username already exists.")
        else:
            valids.append("")
        return valids

    def get_id(self):
        return self.user_id

    def get_un(self):
        return self.u_name


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
                        InputRequired(), Length(min=4, max=100)])
    password = PasswordField('password', validators=[
                             InputRequired(), Length(min=8, max=80)])


class SignupForm(FlaskForm):
    user_name = StringField('User Name', validators=[
                            InputRequired(), Length(min=1, max=100)])
    email = StringField('Email', validators=[
                        InputRequired(), Length(min=4, max=100)])
    password = PasswordField('Password', validators=[
                             InputRequired(), Length(min=8, max=80)])
    c_password = PasswordField('Confirm Password', validators=[
                               InputRequired(), Length(min=8, max=80)])

    def validate(self):
        valids = []
        if self.password == self.c_password:
            return True

        else:
            return False




@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)


@app.route("/SignUp", methods=["POST"])
def signup():
    users = pd.read_sql("select * from users;", engine)
    unames = [x for x in pd.unique(users['user_name'])]
    emails = [x for x in pd.unique(users['email'])]
    hashed_password = generate_password_hash(
        request.form['password'], method='sha256')
    if request.form['password'] != request.form['c_password']:
        invalids = ["Passwords do not match!"]
    else:
        invalids = [""]
    new_user = Users(user_id=uuid.uuid1(
    ).hex, email=request.form['email'], user_name=request.form['user_name'], password=hashed_password, c_password=hashed_password)
    invalids = new_user.validate(unames, emails, invalids)[::-1]
    print(invalids)
    if len("".join(invalids)) == 0:

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(BASE_URL+"/")

    else:
        html = [render_template("head.html", title="Sign Up")]
        html.append(render_template("SignUp.html", valids=invalids, user=new_user,
                                    c_password=request.form['c_password'], password=request.form['password']))
        return "\n".join(html)


@app.route("/LogOut", methods=["POST", "GET"])
def logout():

    logout_user()
    return redirect(BASE_URL+"/")


@app.route("/LogIn", methods=["POST"])
def login():

    user = Users.query.filter_by(email=request.form["email"]).first()

    if user:
        if check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect(BASE_URL+"/")
    else:
        user = Users.query.filter_by(user_name=request.form["email"]).first()

        if user:
            if check_password_hash(user.password, request.form["password"]):
                login_user(user)
                return redirect(BASE_URL+"/")

    return redirect(BASE_URL+"/")


@app.route("/filter/<filter>", methods=["POST", "GET"])
def filtered(filter):

    try:
        current_user.email
    except:
        return render_template("AnnonUser.html", BASE=BASE_URL).replace("insertmodalshere", render_template("loginModals.html", BASE=BASE_URL, forml=LoginForm(), forms=SignupForm()))

    uid = current_user.user_id
    if filter[1] == "a":
        sort = "asc"
    else:
        sort = "desc"
    if filter[0] == "d":
        filt = "p_date"
    else:
        filt = "num_resp"
    polls = pd.read_sql('select polls.poll_id, polls.question,polls.num_ans,polls.user_id,polls.p_date, count(num_ans) as num_resp from polls inner join answers on polls.poll_id = answers.poll_id group by polls.poll_id order by {filt} {sort};'.format(filt=filt,sort=sort), engine)


#    user=pd.read_sql(f"select * from users where user_id = '{uid}';")
    # u={}
    # for col in user:
    # u[f'{col}']=user[col][0]

    ans = pd.read_sql('select * from answers;', engine)
    u_ans = ans[ans['user_id'] == uid].reset_index(drop=True)
    items = []
    for i, x in enumerate(polls["poll_id"]):
        if x in u_ans["poll_id"].to_list():
            taken = True
            ntaken = False
        else:
            ntaken = True
            taken = False
        total_ans = len(ans[ans["poll_id"] == x])
        numans = [y for y in range(1, polls["num_ans"][i]+1)]
        items.append({"question": polls["question"][i], "p_date": polls["p_date"][i], "total_ans": total_ans,
                      "taken": taken, "ntaken": ntaken, "pid": x, "num_ans": numans, "index": i})
    html = []
    html.append(render_template("head.html", title="View polls"))
    html.append(render_template("nav.html"))
    html.append(render_template("main.html", BASE=BASE_URL, items=items))
    html = "\n".join(html).replace("insertmodalshere", render_template(
        "pollModals.html", BASE=BASE_URL, items=items))
    return html


@app.route("/", methods=["POST", "GET"])
def home():

    try:
        current_user.email
    except:
        return render_template("AnnonUser.html", BASE=BASE_URL).replace("insertmodalshere", render_template("loginModals.html", BASE=BASE_URL, forml=LoginForm(), forms=SignupForm()))

    uid = current_user.user_id
    polls = pd.read_sql("select * from polls order by p_date desc;", engine)
#    user=pd.read_sql("select * from users where user_id = '{uid}';".format(uid=uid))
    # u={}
    # for col in user:
    # u[f'{col}']=user[col][0]

    ans = pd.read_sql("select * from answers;", engine)
    u_ans = ans[ans['user_id'] == uid].reset_index(drop=True)
    items = []
    for i, x in enumerate(polls["poll_id"]):
        if x in u_ans["poll_id"].to_list():
            taken = True
            ntaken = False
        else:
            ntaken = True
            taken = False
        total_ans = len(ans[ans["poll_id"] == x])
        numans = [y for y in range(1, polls["num_ans"][i]+1)]
        items.append({"question": polls["question"][i], "p_date": polls["p_date"][i], "total_ans": total_ans,
                      "taken": taken, "ntaken": ntaken, "pid": x, "num_ans": numans, "index": i})
    html = []
    html.append(render_template("head.html", title="View polls"))
    html.append(render_template("nav.html"))
    html.append(render_template("main.html", BASE=BASE_URL, items=items))
    html = "\n".join(html).replace("insertmodalshere", render_template(
        "pollModals.html", BASE=BASE_URL, items=items))
    return html


@app.route("/CreatePoll", methods=["POST"])
def create_poll():
    try:
        current_user.email
    except:
        return render_template("AnnonUser.html", BASE=BASE_URL).replace("insertmodalshere", render_template("loginModals.html", BASE=BASE_URL, forml=LoginForm(), forms=SignupForm()))

    uid = current_user.user_id
    question = request.form["question"]
    num_ans = int(request.form["num_ans"])
    engine.execute(
        "insert into polls (poll_id, question, num_ans, user_id, p_date) values ('{uid}','{question}', {num_ans}, '{current_user}', CURDATE()) ;".format(uid=uuid.uuid1(),current_user=current_user.user_id,question=question,num_ans=num_ans))
    return redirect(BASE_URL+"/")


@app.route("/SubmitPoll/<pid>", methods=["POST"])
def submit_poll(pid):
    try:
        current_user.email
    except:
        return render_template("AnnonUser.html", BASE=BASE_URL).replace("insertmodalshere", render_template("loginModals.html", BASE=BASE_URL, forml=LoginForm(), forms=SignupForm()))

    uid = current_user.user_id
    # polls=pd.read_sql(f"select * from polls where poll_id = '{pid}';",engine)
    answers = []
    ins_str = "'{uid}', '{pid}', ".format(uid=uid,pid=pid)
    for x in range(1, 6):
        try:
            if x == 5:
                ins_str += "'" + request.form['{x}'.format(x=x)].upper() + "' "
            else:
                ins_str += "'" + request.form['{x}'.format(x=x)].upper() + "', "

        except:
            if x == 5:
                ins_str += "null"
            else:
                ins_str += "null, "

    engine.execute("insert into answers (user_id, poll_id, A1, A2, A3, A4, A5) values ({ins_str});".format(ins_str=ins_str))
    return redirect(BASE_URL+"/viewPoll/"+pid)


@app.route("/viewPoll/<pid>", methods=["GET", "POST"])
def view_poll(pid):
    try:
        current_user.email
    except:
        return render_template("AnnonUser.html", BASE=BASE_URL).replace("insertmodalshere", render_template("loginModals.html", BASE=BASE_URL, forml=LoginForm(), forms=SignupForm()))

    uid = current_user.user_id
    # dont show if user hasnt taken poll
    # top 5 matches:
    # build a function to fuzzy match inputs
    # global graph by count
    # global graph by ranking
    # friend match index
    # pole_similatrity scorer
    # sort table of unique answers and total answers
    ans = pd.read_sql("Select * from answers where poll_id ='{pid}';".format(pid=pid), engine)
    users = pd.read_sql("Select * from users;", engine)
    polls = pd.read_sql("Select * from polls where poll_id ='{pid}';".format(pid=pid), engine)
    question = polls["question"][0]
    param = polls["param"][0]
    nn = polls["num_ans"][0]
    uid = current_user.user_id
    u_ans_df = ans[ans["user_id"] == uid].reset_index(drop=True)
    print(u_ans_df)
    anss = ans
    ans = ans[ans["user_id"] != uid]
    print(ans)
    u_ans = []
    for x in range(1, nn+1):

        u_ans.append(u_ans_df["A{x}".format(x=x)][len(u_ans_df)-1])
    mdf = pd.DataFrame()
    scores = {}
    # for i, answer in enumerate(u_ans):
    for x in range(1, nn+1):
        if mdf.empty:
            dff = ans[ans["A{x}".format(x=x)].isin(u_ans)]

            mdf = dff
        else:
            dff = ans[ans["A{x}".format(x=x)].isin(u_ans)]
            mdf = pd.concat([mdf, dff])
    print(mdf)
    for user in pd.unique(mdf["user_id"]):
        scores[user] = 0
        mdff = mdf[mdf["user_id"] == user].reset_index(drop=True)

        scores[user] += len(mdff)*10
        # print(mdff)
        for i, answer in enumerate(u_ans):
            # print(answer, mdff[f"A{i + 1}"])
            if answer in mdff["A{i}".format(i=i+1)].to_list():
                # print(answer, mdff["A{i}".format(i=i+1)])
                scores[user] += (nn+1-i)*10
    ndf = pd.DataFrame.from_dict(scores.items())
    try:
        ndf.columns = ["uid", "points"]
    except:
        return render_template("noMatches.html", red=BASE_URL+"/", title="Refresh Page")
    ndf = ndf.sort_values(by="points", ascending=False).nlargest(
        5, "points").reset_index(drop=True)
    print(ndf)
    items = []
    for i, uid in enumerate(ndf['uid']):
        code = {}
        usersf = users[users["user_id"] == uid].reset_index(drop=True)
        print(uid)
        ansf = ans[ans["user_id"] == uid].reset_index(drop=True)
        print(ansf)
        u2_ans = []
        for x in range(1, nn+1):
            u2_ans.append(ansf["A{x}".format(x=x)][len(ansf)-1])
        ua = []
        u2a = []
        ii = 0
        for u1, u2 in zip(u_ans, u2_ans):
            print(u2_ans, u_ans)
            if u1 == u2:
                u1 = "<p style=\"background-color:green;\">"+u1 + "</p>"
                u2 = "<p style=\"background-color:green;\">"+u2 + "</p>"
                ua.append("Green")
                u2a.append("Green")

                continue
            elif u1 in u2_ans or u2 in u_ans:
                if u1 in u2_ans:
                    u1 = "yellow"
                else:
                    u1 = "red"
                if u2 in u_ans:
                    u2 = "yellow"
                else:
                    u2 = "red"
                ua.append(u1)

                u2a.append(u2)
                continue
            else:
                u1 = "<p style=\"background-color:red;\">"+u1+"</p>"
                u2 = "<p style=\"background-color:red;\">"+u2+"</p>"
                ua.append("red")
                u2a.append("red")

        code = {"uname": usersf['user_name'][0],
                "twitter": usersf['twitter'][0],
                "insta": usersf['instagram'][0],
                "tik": usersf["tiktok"][0],
                "points": ndf["points"][i],
                "index": i+1,

                "u_resp": u_ans,
                "col1": ua,
                "col2": u2a,
                "u2_resp": u2_ans}

        items.append(code)

    chart_df = pd.DataFrame()
    d1 = []
    d2 = []
    for x in range(1, nn+1):

        [d1.append(y) for y in anss["A{x}".format(x=x)]]
        [d2.append(6-x) for y in anss["A{x}".format(x=x)]]

    print(d2, d1)
    df = pd.DataFrame([d1, d2]).transpose()
    df.columns = ["Ans", "Score"]

    print(df)
    print(df.groupby(['Ans'])["Score"].mean())
    score_df = df.groupby(['Ans'])["Score"].mean()
    score_df = pd.DataFrame(score_df).reset_index()
    score_df.columns = ["Answer", "Avg Score"]
    print(score_df)
    score_df = score_df.sort_values(by="Avg Score", ascending=False)

    print(score_df)
    values = df["Ans"].value_counts()
    value_counts = df['Ans'].value_counts(dropna=True, sort=True)
    df_val_counts = pd.DataFrame(value_counts)

    df_value_counts_reset = df_val_counts.reset_index()
    df_value_counts_reset.columns = ['Ans', 'count']
    # print(df_val_counts,values)

    fig = px.bar(df_value_counts_reset, x='Ans', y="count",
                 text="count", width=500, height=300)

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    fig2 = px.bar(score_df, x='Answer', y="Avg Score",
                  text="Avg Score", width=500, height=300)

    graphJSON2 = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)
    html = []
    html = [render_template("head.html", title="View Rankings")]
    html.append(render_template("nav.html", BASE=BASE_URL))
    html.append(render_template('viewPoll.html', question=question, param=param,
                                items=items, graphJSON=graphJSON, avgScoreChart=graphJSON2))
    html = "\n".join(html)
    html = html.replace("insertmodalshere", render_template(
        'viewPollModals.html', items=items))

    return html
    d2 = []

    """for x in range(1, 6):
        d2.append(x*(6-i)*len for y in anss[anss[f"A{x}"].isin(df_value_counts_reset["Ans"])][])]

    print(d1)
    df = pd.DataFrame([d1]).transpose()"""


@app.route("/Account", methods=["GET", "POST"])
def account():
    uid = current_user.user_id
    user = pd.read_sql(
        "select * from users where user_id = '{}'".format(uid), engine)
    u = {}
    for col in user:
        u[col] = user[col][0]
    html = [render_template("head.html", title="Account"),
            render_template("nav.html", BASE=BASE_URL)]
    html.append(render_template("account.html", user=u, BASE=BASE_URL))
    return "\n".join(html)


@app.route("/editAccount", methods=["POST"])
def edit_account():
    uid = current_user.user_id
    user = pd.read_sql(
        "select * from users where user_id = '{}'".format(uid), engine)
    u = {}
    for col in user:
        if col in ["email", "twitter", "instagram", "tiktok"]:
            try:
                old = user[col][0]
                new = request.form[col]
                if old != new and len(new) > 0:
                    engine.execute("update users set {col} = '{new}' where user_id = '{uid}';".format(col=col,new=new,uid=uid))
            except:

                continue

    return redirect(BASE_URL+"/Account")


if __name__ == '__main__':
    app.run(debug=False, host="172.31.89.128", port=8080)
