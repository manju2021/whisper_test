from curses import longname
from email.mime import image
import pandas as pd
from email.policy import default
import optparse
from django.shortcuts import render
from flask import Flask, render_template,redirect,flash,url_for,request,session
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField,StringField,SelectField,FloatField,BooleanField,SelectMultipleField
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired
from flask_bootstrap import Bootstrap
from wtforms.fields.html5 import DateField
from flask_sqlalchemy import SQLAlchemy
from flask_paginate import Pagination, get_page_args
import pymysql
import datetime
import json
import demjson
from pprint import pprint
from concurrent.futures import ThreadPoolExecutor
import urllib.request 
from PIL import Image
from datetime import datetime,timedelta
from forms_new import *
from prowl_form import prowl
from pdmq_form1 import clinical_trial_form1
from grpc import StatusCode
from flask_mail import *  
from flask_session import Session
import uuid
from func import bothvisit_botheyes,lefteye_1fup,lefteye_2fup,righteye_1fup,righteye_2fup,botheyes_1fup,botheyes_2fup,lefteye_bothvisits,righteye_bothvisits
from kpop_func import bcva_pred,comp_pred,surnv_pred
import os
import pickle
from sqlalchemy.inspection import inspect
from database import db
from database_study import *

#from kpop_forms import *


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:India@2021@localhost/epro'

app.config.from_pyfile('config.py')
mail = Mail(app)  
Bootstrap(app)
db.init_app(app)
app.app_context().push()

Session(app)
app.permanent_session_lifetime = timedelta(minutes=60)

lasik_study_pending = lasik_study.query.filter( lasik_study.intervention_status=='PENDING').all()
lasik_study_followup = lasik_study.query.filter( lasik_study.intervention_status=='FOLLOWUP').all()
lasik_study_closed = lasik_study.query.filter( lasik_study.intervention_status=='CLOSED').all()
print(len(lasik_study_pending))


kpop_study_pending = kpop_registry.query.filter( kpop_registry.intervention_status=='Pending').all()
kpop_study_followup = kpop_registry.query.filter( kpop_registry.intervention_status=='FOLLOWUP').all()
kpop_study_closed = kpop_registry.query.filter( kpop_registry.intervention_status=='CLOSED').all()


def query_to_list(rset):
    result = []
    cols=[]
    for obj in rset:
        instance = inspect(obj)
        items = instance.attrs.items()
        result.append([x.value for _,x in items])
        cols=instance.attrs.keys()
    return cols, result

def querytodf(df):    
    names, data = query_to_list(df)
    df_test = pd.DataFrame.from_records(data, columns=names)
    return df_test

def get_studydata_pending(df,offset=0, per_page=50):
    return df[offset : offset + per_page]

def get_studydata_fup(df,offset=0, per_page=50):
    return df[offset : offset + per_page]

def get_studydata_closed(df,offset=0, per_page=50):
    return df[offset : offset + per_page]

  
###login
@app.route('/', methods=["GET","POST"])
@app.route('/index', methods=["GET","POST"])
def index(): 
    global emailid
    global lname
    global fname
    global org
    global otp_pwd
       
    form1 = userform()
    form2 =userform()
    if form1.is_submitted():
        session['emailid'] = form1.email.data        
        session['lname']=form1.lastname.data
        session['fname']=form1.firstname.data
        session['org']=form1.organization.data
        otp_pwd=str(uuid.uuid4())
        form1.actual_otp=otp_pwd
        print(session['emailid'])
        #sess_dict = { 'email': emailid, 'lname': lname, 'fname': fname, 'org': org, 'otp_pwd': otp_pwd}

        #with open('./static/sess_data.json', 'wb') as fp:
            #pickle.dump(sess_dict, fp)

        msg = Message('OTP',sender ='kcdiseaseprogression@gmail.com' , recipients = [session['emailid']])  
        msg.body = str(otp_pwd)  
        #print(form1)
        try:
            status=mail.send(msg)
            print(status)
        #print('hi you are here')
            return render_template("authpage_otp.html",form=form2,lname=session['lname'],fname=session['fname'],org=session['org'],email=session['emailid'],actual_pwd=otp_pwd)
        except:
            flash("Error in your email id, please update correct email id")
            return render_template("authpage.html",form1=form1)
    
    return render_template("authpage.html",form1=form1)

@app.route('/validate',methods=["POST"])   
def validate():    
    #lname=request.form['lastname']
    #fname=request.form['firstname']
    #org=request.form['organization']
    #emailid=request.form['email']

    if request.form['actual_otp']== request.form['otp']: 
        #app.config["SESSION_PERMANENT"] = True
        return render_template("termsofuse.html",lastname=session['lname'],firstname=session['fname'],organization=session['org'],email=session['emailid'])  
    else:
        #session.clear()
        flash("Please enter the correct OTP sent to your email ID for verification")
        return render_template("otp_error.html") 

#@app.route('/termsofuse', methods=["GET","POST"])
#def termsofuse():
    #print("Inside terms of user",ver_email)
    #with open('./static/sess_data.json', 'rb') as fp:
    #lname=request.form.lastname
    #fname=request.form.firstname
    #org = request.form.org
    
    #if request.form.get('termsagree'):
     #   return redirect(url_for('home'))
    #else:
     #   flash("Please accept the terms of use to continue")
      #  return render_template("termsofuse.html",lastname=lname,firstname=fname,organization=org)
    
    #return render_template("termsofuse.html",lastname=data['lname'],firstname=data['fname'],organization=data['org'])
    
    #return redirect(url_for('index'))
def vst(resp):
    if resp["visit_number2"]==2:
        resp["visit_number2"]="Second Visit"
    else:
        resp["visit_number2"]="Third Visit"
    return resp

@app.route('/kcform', methods=['GET',"POST"])
def home():
    #print(lastname)
    if session['emailid']: 
        form = UploadFileForm()
        #with open('./static/sess_data.json', 'rb') as fp:
        #   data = pickle.load(fp)
        #if (data['email']):         
        if form.is_submitted():               
            if form.fupvisits.data=="3":
                if form.eye.data=="Both":            
                    response_list,filenames=bothvisit_botheyes(form,app)                
                    if response_list:
                        return render_template('botheyes_bothvisits.html',result_left_fp1=vst(response_list[0].json()),result_right_fp1=vst(response_list[1].json()),result_left_fp2=vst(response_list[2].json()),result_right_fp2=vst(response_list[3].json()),filename=filenames,ptid=form.PatientID.data)
                    else:
                        return render_template('error.html')
                elif form.eye.data=="OS-Oculus Sinister":
                    response_list,filenames=lefteye_bothvisits(form,app)                
                    if response_list:
                        return render_template('oneeye_bothvisits.html',result_left_fp1=vst(response_list[0].json()),result_right_fp1=vst(response_list[1].json()),filename=filenames,ptid=form.PatientID.data)
                    else:
                        return render_template('error.html')
                elif form.eye.data=="OD-Oculus Dextrus":
                    response_list,filenames=righteye_bothvisits(form,app)                
                    if response_list:
                        return render_template('oneeye_bothvisits.html',result_left_fp1=vst(response_list[0].json()),result_right_fp1=vst(response_list[1].json()),filename=filenames,ptid=form.PatientID.data)
                    else:
                        return render_template('error.html')     
                else:
                    return render_template('error.html')
            else:
                if form.eye.data=="OS-Oculus Sinister":                
                    response_list,filenames=lefteye_1fup(form,app)
                    if response_list:   
                        return render_template('common_display_1apicall.html',response_dict=vst(response_list.json()),filename=filenames,ptid=form.PatientID.data)
                    else:
                        return render_template('error.html')           
                elif form.eye.data=="OD-Oculus Dextrus":
                    response_list,filenames=righteye_1fup(form,app)
                    if response_list:
                        return render_template('common_display_1apicall.html',response_dict=vst(response_list.json()),filename=filenames,ptid=form.PatientID.data)
                    else:
                        return render_template('error.html')
                elif form.eye.data=="Both":
                    response_list,filenames=botheyes_1fup(form,app)                            
                    
                    if response_list:
                        return render_template('botheyes_1fupvisits.html',result_left_fp1=vst(response_list[0].json()),result_right_fp1=vst(response_list[1].json()),filename=filenames,ptid=form.PatientID.data)
                    else:
                        return render_template('error.html')
                else:
                    return render_template('error.html')
        else:
            return render_template('index.html', form=form)
    else:                  
        return "You are not logged in/your session timed out <br><a href = '/index'>" + "click here to log in</a>"
    

@app.route('/logout')
def logout():   
    session["lname"] = None
    session["fname"] = None
    session["emailid"] = None
    session["org"] = None
    return "You are logged out successfully!! <br><a base href = /index>" + "click here to log in</a>"

@app.route('/library')
def library():
    if session['emailid']:
        return render_template('lvpei_marketplace.html')
    else:
        return "You are not logged in/your session timed out <br><a href = '/index'>" + "click here to log in</a>"
     

def pred_logmar(datapoint):
    if datapoint == 4.0:
        return ["Very Poor","1.3 - 3"]
    elif datapoint == 3.0:
        return ["Poor","1.0 - 1.2"]
    elif datapoint == 2.0:
        return ["Good","0.5 - 0.9"]
    else:
        return ["Very Good","0.0 - 0.4"]

def pred_logmar_range(datapoint):
    if datapoint == 4.0:
        return [1.3,3]
    elif datapoint == 3.0:
        return [1.0,1.2]
    elif datapoint == 2.0:
        return [0.5,0.9]
    else:
        return [0.0,0.4]

def pred_compliance(datapoint):
    if datapoint==1.0:
        return "Yes"
    else:
        return "No"

@app.route('/kpopform',methods=["GET","POST"])
def kpopform():
    if session['emailid']:
        form=kpopinputform_new()
        if form.is_submitted():        
            bcvaoutput=bcva_pred(form,session)
            print(bcvaoutput)
            fupoutput=comp_pred(form,session)        
            print(fupoutput)
            survivaloutput= surnv_pred(form,session)
            predicted_logmar= pred_logmar(bcvaoutput['BCVA_state_pred'])
            predicted_compliance=  pred_compliance(fupoutput['compliance_pred'])
            ##Chart data update
            surv_prediction_dict = survivaloutput
            surv_prediction_dict1 = surv_prediction_dict["Outputs"]
            surv_prediction_dict2 = demjson.decode(surv_prediction_dict1)
            surv_pred_output_dict = surv_prediction_dict2["y_axis"]
            y=list(surv_pred_output_dict.values())
            surv_pred_output_dict_x = surv_prediction_dict2["x_axis"]
            x=list(surv_pred_output_dict_x.values())
            ###BCVA
            #x_bcvachart,y_bcvachart=bcva_chart_update(bcvaoutput,form.postopstage.data)  
            preopbcva=pred_logmar_range(bcvaoutput['pre_op_BCVA_state'])
            lastrecordedbcva=pred_logmar_range(bcvaoutput['last_recorded_bcva'])
            predictedbcva=pred_logmar_range(bcvaoutput['BCVA_state_pred'])
            bcva_chart_list=preopbcva+lastrecordedbcva+predictedbcva

            return render_template('kpop_results1.html',dict1=bcvaoutput,dict2=fupoutput,dict3=survivaloutput,pred_stage=form.postopstage.data,myform=form,logmar=predicted_logmar,comp_result=predicted_compliance,x_value=x,y_value=y,bcvachartdata=bcva_chart_list)
        else:        
            return render_template('kpopform_new.html',form=form) 
    else:                    
        return "You are not logged in/your session timed out <br><a href = '/index'>" + "click here to log in</a>"
       
        
@app.route('/prowlform')
def prowlform():
	form=prowl()
	#print(preopconditions)
	return render_template('prowl.html',form=form)

@app.route('/pdmqform1')
def pdmqform1():
	form=clinical_trial_form1()
	#print(preopconditions)
	return render_template('pdmqform1.html',form=form)

@app.route('/kpopstudy')
def kpopstudy():
    page, per_page,offset = get_page_args(page_parameter='page',per_page_parameter='per_page',)
    
    #INCLUDE THESE COLUMN IN THE STUDY KPOP LIST : 1. SURGERY-DATE - 2. LAST FOLLOWUP VISIT, 3. NEXT FOLLOWUP VISIT, 4. PHONE NUMBER, 5. EMAIL, 6. ADDRESS,7. PAYING/NON PAYING,8. LAST CONTACT MADE
    kpop_study_pending = kpop_registry.query.filter( kpop_registry.intervention_status=='PENDING').all()
    kpop_study_followup = kpop_registry.query.filter( kpop_registry.intervention_status=='FOLLOWUP').all()
    kpop_study_closed = kpop_registry.query.filter( kpop_registry.intervention_status=='CLOSED').all()
    
    #df_test=querytodf(ins_data)
    #pending_card=card_update(df_test)

    #df_test1=querytodf(ins_data_followup)
    #pending_card1=card_update(df_test1)

    #df_test2=querytodf(ins_data_closed)
    #pending_card2=card_update(df_test2)

    total = len(kpop_study_pending)
    total_fup=len(kpop_study_followup)
    total_closed=len(kpop_study_closed)    

    print(total,total_fup,total_closed)
    pagination_studydata = get_studydata_pending(kpop_study_pending,offset=offset, per_page=10)
    pagination = Pagination(page=page, per_page=15, total=total,css_framework='bootstrap4')

    pagination_studydata_fup = get_studydata_fup(kpop_study_followup,offset=offset, per_page=10)
    pagination_fup = Pagination(page=page, per_page=15, total=total_fup,css_framework='bootstrap4')

    pagination_studydata_closed = get_studydata_closed(kpop_study_closed,offset=offset, per_page=10)
    pagination_closed = Pagination(page=page, per_page=15, total=total_closed,css_framework='bootstrap4')

    return render_template('kpop_registry.html', studydata_pending=pagination_studydata, studydatafup=pagination_studydata_fup,studydataclosed=pagination_studydata_closed,page=page, per_page=15, pagination=pagination,pagination_fup=pagination_fup,pagination_closed=pagination_closed) 

@app.route('/kpopepro')
def kpopepro():

    page, per_page,offset = get_page_args(page_parameter='page',per_page_parameter='per_page',)
    
    #INCLUDE THESE COLUMN IN THE STUDY KPOP LIST : 1. SURGERY-DATE - 2. LAST FOLLOWUP VISIT, 3. NEXT FOLLOWUP VISIT, 4. PHONE NUMBER, 5. EMAIL, 6. ADDRESS,7. PAYING/NON PAYING,8. LAST CONTACT MADE
    kpop_study_pending = kpop_registry.query.filter( kpop_registry.intervention_status=='PENDING').all()
    kpop_study_followup = kpop_registry.query.filter( kpop_registry.intervention_status=='FOLLOWUP').all()
    kpop_study_closed = kpop_registry.query.filter( kpop_registry.intervention_status=='CLOSED').all()
    
    #df_test=querytodf(ins_data)
    #pending_card=card_update(df_test)

    #df_test1=querytodf(ins_data_followup)
    #pending_card1=card_update(df_test1)

    #df_test2=querytodf(ins_data_closed)
    #pending_card2=card_update(df_test2)

    total = len(kpop_study_pending)
    total_fup=len(kpop_study_followup)
    total_closed=len(kpop_study_closed)    

    print(total,total_fup,total_closed)
    pagination_studydata = get_studydata_pending(kpop_study_pending,offset=offset, per_page=10)
    pagination = Pagination(page=page, per_page=15, total=total,css_framework='bootstrap4')

    pagination_studydata_fup = get_studydata_fup(kpop_study_followup,offset=offset, per_page=10)
    pagination_fup = Pagination(page=page, per_page=15, total=total_fup,css_framework='bootstrap4')

    pagination_studydata_closed = get_studydata_closed(kpop_study_closed,offset=offset, per_page=10)
    pagination_closed = Pagination(page=page, per_page=15, total=total_closed,css_framework='bootstrap4')

    form=newepro_form()
    return render_template('vertical_navbar.html', studydata_pending=pagination_studydata, studydatafup=pagination_studydata_fup,studydataclosed=pagination_studydata_closed,page=page, per_page=15, pagination=pagination,pagination_fup=pagination_fup,pagination_closed=pagination_closed,form=form) 

@app.route('/newregistry')
def newregistry():
    form=newregistry_form()
    return render_template("newregistry_form.html",form=form)

@app.route('/newquest')
def newquest():
    form=newquestnr_form()
    return render_template("newquest_form.html",form=form)


@app.route('/newepro')
def newepro():
    form=newepro_form()
    return render_template("new_epro.html",form=form)

@app.route('/prowlstudy')
def prowlstudy():
    page, per_page,offset = get_page_args(page_parameter='page',per_page_parameter='per_page',)
    
    #INCLUDE THESE COLUMN IN THE STUDY KPOP LIST : 1. SURGERY-DATE - 2. LAST FOLLOWUP VISIT, 3. NEXT FOLLOWUP VISIT, 4. PHONE NUMBER, 5. EMAIL, 6. ADDRESS,7. PAYING/NON PAYING,8. LAST CONTACT MADE
    lasik_study_pending = lasik_study.query.filter( lasik_study.intervention_status=='PENDING').all()
    lasik_study_followup = lasik_study.query.filter( lasik_study.intervention_status=='FOLLOWUP').all()
    lasik_study_closed = lasik_study.query.filter( lasik_study.intervention_status=='CLOSED').all()
    
    #df_test=querytodf(ins_data)
    #pending_card=card_update(df_test)

    #df_test1=querytodf(ins_data_followup)
    #pending_card1=card_update(df_test1)

    #df_test2=querytodf(ins_data_closed)
    #pending_card2=card_update(df_test2)

    total = len(lasik_study_pending)
    total_fup=len(lasik_study_followup)
    total_closed=len(lasik_study_closed)    
    
    print(total,total_fup,total_closed)
    pagination_studydata = get_studydata_pending(offset=offset, per_page=10)
    pagination = Pagination(page=page, per_page=10, total=total,css_framework='bootstrap4')

    pagination_studydata_fup = get_studydata_fup(offset=offset, per_page=10)
    pagination_fup = Pagination(page=page, per_page=10, total=total_fup,css_framework='bootstrap4')

    pagination_studydata_closed = get_studydata_closed(offset=offset, per_page=10)
    pagination_closed = Pagination(page=page, per_page=10, total=total_closed,css_framework='bootstrap4')

    return render_template('prowl_study_list.html', studydata_pending=pagination_studydata, studydatafup=pagination_studydata_fup,studydataclosed=pagination_studydata_closed,page=page, per_page=10, pagination=pagination,pagination_fup=pagination_fup,pagination_closed=pagination_closed) 

@app.route('/prowlquestnr/<ID>',methods=["GET","POST"]) 
def prowlquestnr(ID):
    #query_data=kpop_study_pending.query.filter(kpop_registry.ID==ID).all()
    query_data = kpop_registry.query.filter(kpop_registry.intervention_status=='PENDING').all()

    #print(query_data)
    #int_history = intervention_history.query.filter(intervention_history.GROUP_NO==ID).all()
    #pricing_details=insgroup_pricing_details.query.filter(insgroup_pricing_details.GROUP_NO==ID).all()
    #risk_data=risk_factors.query.filter(risk_factors.GROUP_NO==ID).all()
    form=prowl()
    
        #db.session.commit()
        #flash('form is successfully submitted','success')
            #return render_template("success.html")
        #return redirect(url_for('outreach',ID = form.Group_No.data))
        #
    return render_template("epro_prowl.html",ID_test=query_data,form=form)

@app.route('/kpop_redirect')
def kpop_redirect():
    return redirect(url_for('kpopform'))

if __name__ == '__main__':
    app.run(debug=True) 

