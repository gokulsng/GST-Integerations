
import frappe
import pdfkit
import os
import random
import requests
from frappe.auth import LoginManager
from frappe.core.doctype.user.user import generate_keys
from datetime import datetime,date
from frappe.utils import add_to_date, today
import json
import base64
from frappe.utils import add_days, flt, nowdate
from frappe.utils import now, today, nowdate, now_datetime
from erpnext.accounts.doctype.payment_entry.payment_entry import get_party_details
from erpnext import get_company_currency, get_default_company
from frappe.utils.pdf import get_pdf
from frappe.utils.jinja import render_template
from json import loads
from dateutil import  parser


@frappe.whitelist(allow_guest=True)
def get_token():
	url = "https://gsp.adaequare.com/gsp/authenticate?grant_type=token"
	payload={}
	doc = frappe.get_doc("GST API Settings")
#	frappe.errprint(doc)
	key = doc.secret_key
#	frappe.errprint(key)
	value = doc.secret_value
#	frappe.errprint(value)
	headers = {
	'gspappid': key,
	'gspappsecret': value
	}
	response = requests.request("POST", url, headers=headers, data=payload)
	str_ = json.loads(response.text)
#	frappe.errprint(str_['access_token'])
	return str_['access_token']


@frappe.whitelist(allow_guest=True)
def get_gst_details(gstin,adress_gstin_check,name):
	frappe.errprint(gstin)
	if(adress_gstin_check == 1):
		return
	url = 'https://gsp.adaequare.com/enriched/commonapi/search?action=TP&gstin=' + gstin
	token = get_token()
	payload={}
	headers = {
		'Content-Type': 'application/json',
		'Authorization': 'Bearer ' + token
	}
	response = requests.request("GET", url, headers=headers, data=payload)
	txt = json.loads(response.text)
	if(str(txt['success']) == 'false'):
		if(txt["message"]=="Invalid GSTIN / UID"):
			frappe.throw("Invalid GSTIN / UID")
		else:
			frappe.throw("Please Try After Sometime Error:"+txt["message"])
	elif(txt["message"]!="Search taxpayer is completed successfully"):
		frappe.throw("Please Try After Sometime Error:"+txt["message"])

	frappe.db.set_value("Customer",name,"tax_id",gstin)
	frappe.db.set_value("Customer",name,"alias",txt["result"]["tradeNam"])
	frappe.db.set_value("Customer",name,"adress_gstin_check",1)
	adress_doc=frappe.new_doc("Address")
	adress=""
	if(txt["result"]["pradr"]["addr"]["bno"]!=""):
		adress=txt["result"]["pradr"]["addr"]["bno"]+","
	if(txt["result"]["pradr"]["addr"]["flno"]!=""):
		adress=adress+txt["result"]["pradr"]["addr"]["flno"]+","
	if(txt["result"]["pradr"]["addr"]["bnm"]!=""):
		adress=adress+txt["result"]["pradr"]["addr"]["bnm"]+","
	adress1=""
	if(txt["result"]["pradr"]["addr"]["st"]!=""):
		adress=adress+txt["result"]["pradr"]["addr"]["st"]+","
	adress_doc.address_line1=adress
	if(txt["result"]["pradr"]["addr"]["loc"]!=""):
		adress1=adress1+txt["result"]["pradr"]["addr"]["loc"]
	adress_doc.address_line2=adress1
	if(txt["result"]["pradr"]["addr"]["dst"]!=""):
		adress_doc.city=txt["result"]["pradr"]["addr"]["dst"]
	adress_doc.pincode=txt["result"]["pradr"]["addr"]["pncd"]
	adress_doc.gstin=txt["result"]["gstin"]
	adress_doc.gst_state=txt["result"]["pradr"]["addr"]["stcd"]
	adress_doc.append("links",{"link_doctype":"Customer","link_name":name})
	adress_doc.save()

#	frappe.errprint(txt["result"])
#	frappe.errprint(txt["result"]["adadr"]["addr"])
	if txt["result"]["adadr"]:
		for row in txt["result"]["adadr"]:
			frappe.errprint(row)
			adress_doc=frappe.new_doc("Address")
			adres=""
			try:
				frappe.errprint(row["addr"]["bno"])
			except Exception:
				row["addr"]["bno"] = ""
			if(row["addr"]["bno"]!=""):
				adres=row["addr"]["bno"]+","
			if(row["addr"]["flno"]!=""):
				adres=adress+row["addr"]["flno"]+","
			if(row["addr"]["bnm"]!=""):
				adres=adress+row["addr"]["bnm"]+","
			adress1=""
			if(row["addr"]["st"]!=""):
				adres=adress+row["addr"]["st"]+","
			adress_doc.address_line1=adres
			if(row["addr"]["loc"]!=""):
				adress1=adress1+row["addr"]["loc"]
			adress_doc.address_line2=adress1
			if(row["addr"]["dst"]!=""):
				adress_doc.city=row["addr"]["dst"]
			adress_doc.pincode=row["addr"]["pncd"]
			adress_doc.gstin=txt["result"]["gstin"]
			adress_doc.gst_state=row["addr"]["stcd"]
			adress_doc.append("links",{"link_doctype":"Customer","link_name":name})
			adress_doc.save()
	frappe.db.commit()
	return 0


@frappe.whitelist(allow_guest=True)
def get_retrack_details(gstin,year):
#	retrack = frappe.db.get_value("GST Retrack",{"gstin":gstin},"name")
#	if retrack:
#		frappe.throw(("GST Retrack already created for GSTIN- {0} : {1}").format(gstin,retrack))
	date = year[0:6]+year[8:10]
#	frappe.errprint(date)
#	frappe.errprint(gstin)
	url = "https://gsp.adaequare.com/enriched/commonapi/returns?action=RETTRACK&gstin="+ gstin + "&fy=" + date
	frappe.errprint(date)
	payload={}
	token = get_token()
	headers = {
		'Content-Type': 'application/json',
		'Authorization': 'Bearer '+token
	}
	lis = []
	i = 0
	response = requests.request("GET", url, headers=headers, data=payload)
	frappe.errprint(response.text)
	resp = json.loads(response.text)
	frappe.errprint(resp)
	if resp["status"] == 200:
		items = resp["result"]["EFiledlist"]
#		frappe.errprint(items)
		if items:
			items.sort(key = lambda x:parser.parse(x['dof']))
#			frappe.errprint(items)
			for row in items:
#				frappe.errprint(row)
#				frappe.errprint(row["valid"])
				i+=1
				try:
					lis.append({
						"validity":row["valid"] if row["valid"] else "",
						"arn_number":row["arn"] if row["arn"] else "",
						"mode_of_filing":row["mof"] if row["mof"] else "",
						"date_of_filing":parser.parse(row['dof']) if row["dof"] else "",
						"return_type":row["rtntype"] if row["rtntype"] else "",
						"tax_period":datetime.strptime(row["ret_prd"],"%m%Y").strftime("%m-%Y") if row["ret_prd"] else "",
						"status":row["status"] if row["status"] else ""
					})

				except Exception:
					lis.append({
						"validity": "",
						"arn_number":row["arn"] if row["arn"] else "",
						"mode_of_filing":row["mof"] if row["mof"] else "",
						"date_of_filing":parser.parse(row['dof']) if row["dof"] else "",
						"return_type":row["rtntype"] if row["rtntype"] else "",
						"tax_period":datetime.strptime(row["ret_prd"],"%m%Y").strftime("%m-%Y") if row["ret_prd"] else "",
						"status":row["status"] if row["status"] else ""
					})
			frappe.errprint(lis)
			lis.sort(key=lambda l:l['date_of_filing'])
			return lis
		else:
			frappe.throw("No Details are there to show")
	else:
		frappe.throw("No Retrack items Found.Please enter Valid GST Year.")
	
@frappe.whitelist(allow_guest=True)
def get_customer_gstin(gstin,name,primary_address=None,secondary_adr=None):
#	frappe.errprint(gstin)
#	retrack = frappe.db.get_value("GST Retrack",{"gstin":gstin},"name")
#	if retrack:
#		frappe.throw(("GST Retrack already created for GSTIN- {0} : {1}").format(gstin,retrack))
	url = 'https://gsp.adaequare.com/enriched/commonapi/search?action=TP&gstin=' + gstin

	payload={}
	token = get_token()
	headers = {
		'Content-Type': 'application/json',
		'Authorization': 'Bearer ' + token
	}

	response = requests.request("GET", url, headers=headers, data=payload)
	txt = json.loads(response.text)
	if(str(txt['success']) == 'false'):
		if(txt["message"]=="Invalid GSTIN / UID"):
			frappe.throw("Invalid GSTIN / UID")
		else:
			frappe.throw("Please Try After Sometime Error:"+txt["message"])
	elif(txt["message"]!="Search taxpayer is completed successfully"):
		frappe.throw("Please Try After Sometime Error:"+txt["message"])

#	frappe.errprint(txt["result"])
#	frappe.db.set_value("Customer",name,"alias",txt["result"]["tradeNam"])
#	frappe.db.set_value("Customer",name,"adress_gstin_check",1)
	if txt["result"]:
		ad_doc = ""
		if txt['result']['pradr']:
			if not primary_address:
				ad_doc = frappe.new_doc("Address")
			#	if txt["result"]["pradr"]['addr']['bnm']:
			#		ad_doc.address_title = txt["result"]["pradr"]['addr']['bnm']
				adress=""
				if(txt["result"]["pradr"]["addr"]["bno"]!=""):
					adress=txt["result"]["pradr"]["addr"]["bno"]+","
				if(txt["result"]["pradr"]["addr"]["flno"]!=""):
					adress=adress+txt["result"]["pradr"]["addr"]["flno"]+","
				if(txt["result"]["pradr"]["addr"]["bnm"]!=""):
					adress=adress+txt["result"]["pradr"]["addr"]["bnm"]+","
				adress1=""
				if(txt["result"]["pradr"]["addr"]["st"]!=""):
					adress=adress+txt["result"]["pradr"]["addr"]["st"]+","
				ad_doc.address_line1=adress
				if(txt["result"]["pradr"]["addr"]["loc"]!=""):
					adress1=adress1+txt["result"]["pradr"]["addr"]["loc"]
				ad_doc.address_line2=adress1
				if(txt["result"]["pradr"]["addr"]["dst"]!=""):
					ad_doc.city=txt["result"]["pradr"]["addr"]["dst"]
				if(txt["result"]["pradr"]["addr"]["lt"]!=""):
					ad_doc.latitude=txt["result"]["pradr"]["addr"]["lt"]
				if(txt["result"]["pradr"]["addr"]["lg"]!=""):
					ad_doc.longitude=txt["result"]["pradr"]["addr"]["lg"]
				if(txt["result"]["pradr"]["addr"]["pncd"]!=""):
					ad_doc.pincode=txt["result"]["pradr"]["addr"]["pncd"]
				ad_doc.gstin=txt["result"]["gstin"]
				if(txt["result"]["pradr"]["addr"]["stcd"]!=""):
					ad_doc.state=txt["result"]["pradr"]["addr"]["stcd"]
				ad_doc.append("links",{"link_doctype":"Customer","link_name":name})
#				frappe.errprint(ad_doc)
				ad_doc.save()
				frappe.errprint(ad_doc.name)

		ad_doc2 = ""
		if txt["result"]["adadr"]:
			if not secondary_adr:
				ad_doc2 = frappe.new_doc("Address")
			#	if txt["result"]["pradr"]['addr']['bnm']:
			#		ad_doc.address_title = txt["result"]["pradr"]['addr']['bnm']
				for row in txt["result"]["adadr"]:
					adres=""
					adress = ""
					if(row["addr"]["bno"]!=""):
						adres=row["addr"]["bno"]+","
					if(row["addr"]["flno"]!=""):
						adres=adress+row["addr"]["flno"]+","
					if(row["addr"]["bnm"]!=""):
						adres=adress+row["addr"]["bnm"]+","
					adress1=""
					if(row["addr"]["st"]!=""):
						adres=adress+row["addr"]["st"]+","   
					ad_doc2.address_line1=adres
					if(row["addr"]["loc"]!=""):
						adress1=adress1+row["addr"]["loc"]
					ad_doc2.address_line2=adress1
					if(row["addr"]["dst"]!=""):
						ad_doc2.city=row["addr"]["dst"]
					if(row["addr"]["lg"]!=""):
						ad_doc2.longitude=row["addr"]["lg"]
					if(row["addr"]["lt"]!=""):
						ad_doc2.latitude=row["addr"]["lt"]
					if(row["addr"]["pncd"]!=""):
						ad_doc2.pincode=row["addr"]["pncd"]
					ad_doc2.gstin=txt["result"]["gstin"]
					if(row["addr"]["stcd"]!=""):
						ad_doc2.gst_state=row["addr"]["stcd"]
					ad_doc2.append("links",{"link_doctype":"Customer","link_name":name})
					ad_doc2.save()
					frappe.errprint(ad_doc2.name)

		adress=""
		addict = {}
		if txt["result"]["tradeNam"]:
			adress = txt["result"]["tradeNam"]+","+"\n"
		if(txt["result"]["pradr"]["addr"]["bno"]!=""):
			adress= adress+txt["result"]["pradr"]["addr"]["bno"]+","
		if(txt["result"]["pradr"]["addr"]["flno"]!=""):
			adress=adress+txt["result"]["pradr"]["addr"]["flno"]+","
		if(txt["result"]["pradr"]["addr"]["bnm"]!=""):
			adress=adress+txt["result"]["pradr"]["addr"]["bnm"]+","
		if(txt["result"]["pradr"]["addr"]["st"]!=""):
			adress=adress+txt["result"]["pradr"]["addr"]["st"]+","+"\n"
		if(txt["result"]["pradr"]["addr"]["loc"]!=""):
			adress = adress + txt["result"]["pradr"]["addr"]["loc"]+","+"\n"
		if(txt["result"]["pradr"]["addr"]["dst"]!=""):
			adress = adress + txt["result"]["pradr"]["addr"]["dst"]+","+"\n"
		adress = adress + txt["result"]["pradr"]["addr"]["stcd"]+"-"
		adress = adress + txt["result"]["pradr"]["addr"]["pncd"]+"."
#		adress = adress + txt["result"]["pradr"]["addr"]["stcd"]+","+"\n"
#		adress = adress + txt["result"]["gstin"]+","+"\n"
#		adress = adress + txt["result"]["pradr"]["addr"]["stcd"]+","+"\n"

		addict.update({"per_address":adress})


		if txt["result"]["adadr"]:
			for row in txt["result"]["adadr"]:
				adress1=""
				adress = ""
				if txt["result"]["tradeNam"]:
					adress1 = txt["result"]["tradeNam"]+","+"\n"
				if(row["addr"]["bno"]!=""):
					adress1= adress+row["addr"]["bno"]+","
				if(row["addr"]["flno"]!=""):
					adress1=adress1 + row["addr"]["flno"]+","
				if(row["addr"]["bnm"]!=""):
					adress1=adress1 + row["addr"]["bnm"]+","
				if(row["addr"]["st"]!=""):
					adress1=adress1 + row["addr"]["st"]+","+"\n"
				if(row["addr"]["loc"]!=""):
					adress1 = adress1 + row["addr"]["loc"]+","+"\n"
				if(row["addr"]["dst"]!=""):
					adress1 = adress1 + row["addr"]["dst"]+","+"\n"
				adress1 = adress1 + row["addr"]["stcd"]+"-"      
				adress1 = adress1 + row["addr"]["pncd"]+"."
				addict.update({"addres":adress1})

		if ad_doc:
			pri_addr = ad_doc.name
			addict.update({"pri_addr":pri_addr})
		if ad_doc2:
			sec_addr = ad_doc2.name
			addict.update({"sec_addr":sec_addr})
		if txt["result"]["tradeNam"]:
			trade_name = txt["result"]["tradeNam"]
			addict.update({"trade_name":trade_name})
		if txt["result"]["stjCd"]:
			state_code = txt["result"]["stjCd"]
			addict.update({"state_code":state_code})
		if txt["result"]["lgnm"]:
			legal_name_of_business = txt["result"]["lgnm"]
			addict.update({"lnob":legal_name_of_business})
		if txt["result"]["dty"]:
			taxpayer_type = txt["result"]["dty"]
			addict.update({"taxpayer_type":taxpayer_type})
		if txt["result"]["ctjCd"]:
			centre_jurisdiction_code = txt["result"]["ctjCd"]
			addict.update({"cjc":centre_jurisdiction_code})
		if txt["result"]["ctj"]:
			centre_jurisdiction = txt["result"]["ctj"]
			addict.update({"cj":centre_jurisdiction})
		if txt["result"]["ctb"]:
			constution_of_business = txt["result"]["ctb"]
			addict.update({"cob":constution_of_business})
		if txt["result"]["lstupdt"]:
			last_updated_date = txt["result"]["lstupdt"]
			addict.update({"lud":last_updated_date})
		if txt["result"]["rgdt"]:
			date_of_registration = txt["result"]["rgdt"]
			addict.update({"dor":date_of_registration})
		if txt["result"]["sts"]:
			gstin_status = txt["result"]["sts"]
			addict.update({"gst_status":gstin_status})
		if txt["result"]["stj"]:
			state_jurisdiction = txt["result"]["stj"]
			addict.update({"sj":state_jurisdiction})
		if txt["result"]["cxdt"]:
	#		frappe.errprint(txt["result"]["cxdt"])
			cancel_date = txt["result"]["cxdt"]
			addict.update({"cancel_date":cancel_date})
		if txt["result"]["nba"]:
			nature_of_business = ""
			for st in txt["result"]["nba"]:
				nature_of_business += st + "\n"
			nature_of_business = nature_of_business
			addict.update({"nob":nature_of_business})
	#	frappe.errprint(addict)
		return addict

	else:
		frappe.throw("Please enter Valid GSTIN or GSTIN not Registered")
