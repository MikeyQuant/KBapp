from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import uuid
import traceback
import sys
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
app = Flask(__name__ )#, template_folder= os.path.abspath(r"C:\users\MIKEB\Desktop\Python\Fuhnance\KBtemplates"),static_folder=os.path.abspath(r"C:\users\MIKEB\Desktop\Python\Fuhnance\static"))
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

#print(pd.read_sql("select * from users;", engine))
#stripe.api_key = app.config['STRIPE_SECRET_KEY']
#BASE_URL = "http://192.168.1.153:5000/"
#BASE_URL = "http://141.133.97.79:5000/"
BASE_URL="http://10.0.0.160:5000/"
BASE_URL="http://192.168.68.143:5000/"
BASE_URL="http://54.198.186.121:8080/"



'''tables=["users","polls","answers"]
for x in tables:
    df=pd.read_sql(f"select * from {x};",engine)
    df.to_csv(f"{x}.csv")'''
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


def stoolify(s):
    cap=True
    ss=""
    for l in s:
        if cap:
            ss+=l.upper()
            cap=False
        elif l == " ":
            cap=True
            ss+=l
        else:
            ss+=l.lower()
    return ss


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
    #print(invalids)
    if len("".join(invalids)) == 0:

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(BASE_URL)

    else:
        html = [render_template("head.html", title="Sign Up")]
        html.append(render_template("SignUp.html", valids=invalids, user=new_user,
                                    c_password=request.form['c_password'], password=request.form['password']))
        return "\n".join(html)


@app.route("/LogOut", methods=["POST", "GET"])
def logout():

    logout_user()
    return redirect(BASE_URL)


@app.route("/LogIn", methods=["POST"])
def login():

    user = Users.query.filter_by(email=request.form["email"]).first()

    if user:
        if check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect(BASE_URL)
    else:
        user = Users.query.filter_by(user_name=request.form["email"]).first()

        if user:
            if check_password_hash(user.password, request.form["password"]):
                login_user(user)
                return redirect(BASE_URL)

    return redirect(BASE_URL)

@app.route("/filter/<filter>", methods=["POST", "GET"])
def filtered(filter):

    try:
        current_user.email
    except:
        return render_template("AnnonUser.html", BASE=BASE_URL).replace("insertmodalshere", render_template("loginModals.html", BASE=BASE_URL, forml=LoginForm(), forms=SignupForm()))

    uid = current_user.user_id
    user = pd.read_sql("select * from users where user_id = '{}';".format(uid), engine)
    is_mod = user['is_mod'][0]
    #print(is_mod==0,type(is_mod))
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
    html.append(render_template("nav.html",is_mod=is_mod, BASE=BASE_URL))
    html.append(render_template("main.html",is_mod=is_mod, BASE=BASE_URL, items=items))
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
    user=pd.read_sql("select * from users where user_id = '{}';".format(uid) , engine)
    is_mod=user['is_mod'][0]
    #print(is_mod)
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
    html.append(render_template("nav.html",is_mod=is_mod, BASE=BASE_URL))
    html.append(render_template("main.html",is_mod=is_mod, BASE=BASE_URL, items=items))
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
    pid=uuid.uuid1()
    engine.execute(
        "insert into mods (poll_id, question, num_ans, user_id,gucci) values ('{pid}','{question}', {num_ans}, '{current_user}',0) ;".format(pid=pid,current_user=current_user.user_id,question=question,num_ans=num_ans))

    uid = current_user.user_id
    user = pd.read_sql("select * from users where user_id = '{}';".format(uid), engine)
    is_mod = user['is_mod'][0]
    if is_mod == 1:
        return redirect(BASE_URL+"AddPoll/{}".format(pid))
    else:
        return redirect(BASE_URL)

@app.route("/AddPoll/<pid>",methods=["POST","GET"])

def add_poll(pid):
    poll=pd.read_sql("select * from mods where poll_id = '{}'".format(pid),engine)

    engine.execute("delete from mods where poll_id ='{}'".format(pid))

    engine.execute("insert into polls (poll_id, question, num_ans, user_id,p_date) values ('{pid}','{question}', {num_ans}, '{current_user}',CURDATE()) ;".format(pid=pid,current_user=poll['user_id'][0],question=poll['question'][0],num_ans=poll['num_ans'][0]))
    if poll['user_id'][0] == current_user.user_id:
        return redirect(BASE_URL)
    else:
        return redirect(BASE_URL+"Mods")
@app.route("/DeletePoll/<pid>",methods=["POST"])
def delete_poll(pid):
    engine.execute("delete from mods where poll_id ='{}'".format(pid))
    return redirect(BASE_URL + "Mods")

@app.route("/Flag/<pid>/<ans>", methods=["GET", "POST"])
def flag(pid, ans):
    uans = pd.read_sql("select * from uanswers where poll_id = '{pid}' and ans = '{ans}';".format(pid=pid, ans=ans),
                       engine)
    #print(uans)
    if uans['num_flags'][0] in [-1,-2]:
        return ""

    else:
        if uans['num_flags'][0] + 1 > 2:
            engine.execute(
                "update uanswers set gucci = 0 where poll_id = '{pid}' and ans = '{ans}';".format(pid=pid, ans=ans))

            engine.execute(
                "update uanswers set num_flags = num_flags + 1 where poll_id = '{pid}' and ans = '{ans}';".format(
                    pid=pid, ans=ans))
        else:
            engine.execute(
                "update uanswers set num_flags = num_flags + 1 where poll_id = '{pid}' and ans = '{ans}';".format(
                    pid=pid, ans=ans))
    return ""
@app.route("/Unflag/<pid>/<ans>",methods=["POST"])
def unflag(pid,ans):
    engine.execute("update uanswers set gucci = 1 , num_flags = -1 where poll_id = '{pid}' and ans = '{ans}';".format(pid=pid, ans=ans))
    return redirect(BASE_URL + "Mods")
@app.route("/PermaFlag/<pid>/<ans>",methods=["POST"])
def perma_flag(pid,ans):
    engine.execute("update uanswers set gucci = 0 , num_flags = -2 where poll_id = '{pid}' and ans = '{ans}';".format(pid=pid, ans=ans))
    return redirect(BASE_URL + "Mods")
@app.route("/Mods", methods=["POST", "GET"])
def moderator():
    try:
        current_user.email
    except:
        return render_template("AnnonUser.html", BASE=BASE_URL).replace("insertmodalshere",
                                                                        render_template("loginModals.html",
                                                                                        BASE=BASE_URL,
                                                                                        forml=LoginForm(),
                                                                                        forms=SignupForm()))

    uid = current_user.user_id
    user = pd.read_sql("select * from users where user_id = '{}';".format(uid), engine)
    is_mod = user['is_mod'][0]
    if is_mod == 0:
        return redirect(BASE_URL)
    questions=pd.read_sql("select * from mods where gucci != 1;",engine)
    q_items=[]
    for i,x in enumerate(questions['poll_id']):
        q_items.append({"question":questions['question'][i],"pid":x})
    q=pd.read_sql("select * from polls;",engine)
    flags=pd.read_sql("select * from uanswers where gucci = 0 and num_flags != -2 ;",engine).sort_values(by='num_flags',ascending=False).reset_index(drop=True)


    f_items=[]
    for i,x in enumerate(flags['poll_id']):
        f_items.append({"ans":flags['ans'][i],"question":q[q['poll_id']==x].reset_index(drop=True)['question'][0],"pid":x,"num_flags":flags['num_flags'][i]})
    html=[]
    html.append(render_template("head.html", title="View polls"))
    html.append(render_template("nav.html", is_mod=is_mod, BASE=BASE_URL))
    html.append(render_template("mods.html",f_items=f_items,q_items=q_items))
    return "\n".join(html)
@app.route("/SubmitPoll/<pid>", methods=["POST"])
def submit_poll(pid):
    try:
        current_user.email
    except:
        return render_template("AnnonUser.html", BASE=BASE_URL).replace("insertmodalshere", render_template("loginModals.html", BASE=BASE_URL, forml=LoginForm(), forms=SignupForm()))
    uans=pd.read_sql("select * from uanswers where poll_id = '{}'".format(pid),engine)

    uid = current_user.user_id
    # polls=pd.read_sql(f"select * from polls where poll_id = '{pid}';",engine)
    answers = []
    ins_str = "'{uid}', '{pid}', ".format(uid=uid,pid=pid)
    ans=[]
    for x in range(1, 6):
        try:
            if x == 5:
                a=request.form['{x}'.format(x=x)]
                while a[-1]==" ":
                    a=a[:-1]
                ins_str += "'" + stoolify(a) + "' "
                ans.append(stoolify(a))
            else:
                a = request.form['{x}'.format(x=x)]
                while a[-1] == " ":
                    a = a[:-1]
                ins_str += "'" + stoolify(a) + "', "
                ans.append(stoolify(a))
            aa=a.upper()
            aa=aa.replace("1","I",).replace("3","E")
            for l in """!()-[]{};:'"\,<>./?@#$%^&*_~ """:
                aa=aa.replace(l,"")
            #print(aa)
            bad_words=["NIG","FAG"]
            aaa=""
            ll=""
            for i,y in enumerate(aa):
                if ll==y:
                    pass

                else:
                    aaa += y
                    ll=y
            #print(aaa)
            for bad_word in bad_words:
                #print(bad_word in aaa, bad_word,aaa)
                if bad_word in aaa:
                   return redirect(BASE_URL+"LogOut")
        except:
            if x == 5:
                ins_str += "null"
            else:
                ins_str += "null, "
    ans_str=""
    prev_ans=uans["ans"].to_list()
    nnn=0
    aaa=[]
    for a in ans:
        if a in prev_ans or a in aaa:
            pass
        else:

            ans_str+="('{pid}', '{a}',0,1,0),".format(pid=pid,a=a)
            aaa.append(a)

            nnn+=1
    if nnn==0:
        pass
    elif nnn==1:
        engine.execute("insert into uanswers (poll_id, ans, score,gucci,num_flags) values {ans_str};".format(ans_str=ans_str[:-1]))
    else:
        engine.execute("insert into uanswers (poll_id, ans, score,gucci,num_flags) values {ans_str};".format(ans_str=ans_str[:-1]))

    engine.execute("insert into answers (user_id, poll_id, A1, A2, A3, A4, A5) values ({ins_str});".format(ins_str=ins_str))
    engine.execute("delete from answers where isnull(A1);")

    return redirect(BASE_URL)
@app.route("/uvote/<pid>/<ans>", methods=["POST"])
def uvote(pid,ans):
    engine.execute("update uanswers set score = score + 1 where poll_id = '{pid}' and ans = '{ans}';".format(pid=pid,ans=ans))
    return ""
@app.route("/dvote/<pid>/<ans>", methods=["POST"])
def dvote(pid,ans):
    engine.execute("update uanswers set score = score - 1 where poll_id = '{pid}' and ans = '{ans}';".format(pid=pid,ans=ans))
    return ""
@app.route("/viewPoll/<pid>", methods=["GET", "POST"])
def view_poll(pid):
    try:
        current_user.email
    except:
        return render_template("AnnonUser.html", BASE=BASE_URL).replace("insertmodalshere", render_template("loginModals.html", BASE=BASE_URL, forml=LoginForm(), forms=SignupForm()))

    uid = current_user.user_id
    user = pd.read_sql("select * from users where user_id = '{}';".format(uid), engine)
    is_mod = user['is_mod'][0]
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

    #print(u_ans_df)
    anss = ans
    ans = ans[ans["user_id"] != uid]
    #print(ans)
    u_ans = []
    if len(u_ans_df) >0:
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
        #print(mdf)
        for user in pd.unique(mdf["user_id"]):
            scores[user] = 0
            mdff = mdf[mdf["user_id"] == user].reset_index(drop=True)
            u3_ans=[]
            for i, answer in enumerate(u_ans):
                u3=mdff["A{i}".format(i=i+1)][0]
                if u3=="None":
                    print("NONE",u3)
                u3_ans.append(u3)
            if(u3 is None):
                print("NONE")
                continue
            #scores[user] += len(mdff)*10
            #print(mdff)
            for i, answer in enumerate(u_ans):

                #print(answer, u3_ans)
                #print(type(answer),type(u3_ans))
                if answer in u3_ans:
                    #print(answer)
                    scores[user] += (nn+1-i)*10
                if answer == u3_ans[i]:
                    scores[user]+= (nn+1-i)*20
        ndf = pd.DataFrame.from_dict(scores.items())
        print(ndf)
        try:
            ndf.columns = ["uid", "points"]
            ndf = ndf.sort_values(by="points", ascending=False).nlargest(
                5, "points").reset_index(drop=True)
            print(ndf)
            items = []
            for i, uid in enumerate(ndf['uid']):
                code = {}
                usersf = users[users["user_id"] == uid].reset_index(drop=True)
                #print(uid)
                ansf = ans[ans["user_id"] == uid].reset_index(drop=True)
                #print(ansf)
                u2_ans = []
                for x in range(1, nn + 1):
                    u2_ans.append(ansf["A{x}".format(x=x)][len(ansf) - 1])
                ua = []
                u2a = []
                ii = 0
                for u1, u2 in zip(u_ans, u2_ans):
                    #print(u2_ans, u_ans)
                    if u1 == u2:
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
                        ua.append("red")
                        u2a.append("red")

                code = {"uname": usersf['user_name'][0],
                        "twitter": usersf['twitter'][0],
                        "insta": usersf['instagram'][0],
                        "tik": usersf["tiktok"][0],
                        "points": ndf["points"][i],
                        "index": i + 1,

                        "u_resp": u_ans,
                        "col1": ua,
                        "col2": u2a,
                        "u2_resp": u2_ans}

                items.append(code)
            #print(items)
        except Exception as e:
            print(traceback.format_exc())
            print(sys.exc_info()[2])
            items=None
    else:
        items=None
    """ndf = ndf.sort_values(by="points", ascending=False).nlargest(
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

        items.append(code)"""

    chart_df = pd.DataFrame()
    d1 = []
    d2 = []
    for x in range(1, nn+1):

        [d1.append(y) for y in anss["A{x}".format(x=x)]]
        [d2.append(6-x) for y in anss["A{x}".format(x=x)]]


    df = pd.DataFrame([d1, d2]).transpose()
    df.columns = ["Ans", "Score"]
    count_df=df["Ans"].value_counts().reset_index()
    count_df.colums=["Ans","Count"]

    #print(count_df)
    """df.sort_values(by="Ans")

    #print(df)
    #print(df.groupby(['Ans'])["Score"].mean())
    score_df = df.groupby(['Ans'])["Score"].mean()

    score_df = pd.DataFrame(score_df).reset_index()
    print(score_df)
    score_df.columns = ["Answer", "Avg Score"]
    #print(score_df)
    score_df = score_df.sort_values(by="Answer", ascending=False).reset_index(drop=True)

    #print(score_df)

    values = df["Ans"].value_counts()
    value_counts = df['Ans'].value_counts(dropna=True, sort=True)
    df_val_counts = pd.DataFrame(value_counts)

    df_value_counts_reset = df_val_counts.reset_index()
    df_value_counts_reset.columns = ['Ans', 'count']
    #print(df_val_counts,values)
    print(df_value_counts_reset,score_df)
    score_df.sort_values(by="Answer")
    score_df["Vote Counts"]=df_value_counts_reset['count']
    grid=score_df.to_html()
    #print(grid)
    df_value_counts_reset.sort_values(by="Ans")
    fig = px.bar(df_value_counts_reset, x='Ans', y="count",
                 text="count", width=500, height=300)

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    fig2 = px.bar(score_df, x='Answer', y="Avg Score",
                  text="Avg Score", width=500, height=300)
    #print(grid)
    graphJSON2 = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)"""
    itemss={}
    votes={}
    vdf=pd.read_sql("select * from uanswers where poll_id = '{}';".format(pid),engine)
    naughty=vdf[vdf['gucci']==0]['ans'].to_list()
    for vote,ans in zip(vdf['score'],vdf["ans"]):
        votes[ans]=vote
    aaa=[]
    for i,ans in enumerate(count_df["index"]):
        #print(score_df)
        try:
            if ans not in aaa and ans not in naughty:
                itemss[ans]=[count_df["Ans"][i],votes[ans]]
                aaa.append(ans)
        except:
            if ans not in aaa and ans not in naughty:
                engine.execute("insert into uanswers (poll_id, ans, score,gucci,num_flags) values ('{pid}', '{ans}',0,1,0);".format(pid=pid,ans=ans))
                itemss[ans]=[count_df["Ans"][i],0]
                aaa.append(ans)
    html = [render_template("head.html", title="View Rankings")]
    html.append(render_template("nav.html", BASE=BASE_URL,is_mod=is_mod))
    html.append(render_template('viewPoll.html',itemss=itemss, question=question, param=param,
                                items=items,BASE=BASE_URL,pid=pid))
    html = "\n".join(html)
    html = html.replace("insertmodalshere", render_template(
        'viewPollModals.html', items=items))

    return html



    """for x in range(1, 6):
        d2.append(x*(6-i)*len for y in anss[anss[f"A{x}"].isin(df_value_counts_reset["Ans"])][])]

    print(d1)
    df = pd.DataFrame([d1]).transpose()"""


@app.route("/Account", methods=["GET", "POST"])
def account():
    uid = current_user.user_id


    user = pd.read_sql(
        "select * from users where user_id = '{}'".format(uid), engine)
    is_mod = user['is_mod'][0]
    u = {}
    for col in user:
        u[col] = user[col][0]
    html = [render_template("head.html", title="Account"),
            render_template("nav.html",is_mod=is_mod ,BASE=BASE_URL)]
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

    return redirect(BASE_URL+"Account")


if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0",port=8080)
