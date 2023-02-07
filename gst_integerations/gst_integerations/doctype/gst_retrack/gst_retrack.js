// Copyright (c) 2023, Dhinesh and contributors
// For license information, please see license.txt

frappe.ui.form.on('GST Retrack', {
	// refresh: function(frm) {

	// }
	get_customer_details: function(frm) {
		frappe.call({
			method: "gst_integerations.api.get_customer_gstin",
			args: {
				gstin:frm.doc.gstin,
				name:frm.doc.customer,
				primary_address: frm.doc.primary_address,
				secondary_adr: frm.doc.secondary_address
			},
			callback: function(r) {
				console.log(r.message)
				console.log(r.message['per_address'])
			//	var doclist = frappe.model.sync(r.message);
			//	frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
				if(r.message['per_address'])
					frm.doc.permanent_address = String(r.message['per_address'])
				if(r.message['pri_addr'])
					frm.doc.primary_address = r.message['pri_addr']
				if(r.message['sec_addr'])
					frm.doc.secondary_address = r.message['sec_addr']
				if(r.message['addres'])
					frm.doc.address = String(r.message['addres'])
				if(r.message['trade_name'])
					frm.doc.trade_name = r.message['trade_name']
				if(r.message['cj'])
                                        frm.doc.centre_jurisdiction = r.message['cj']
				if(r.message['cjc'])
                                        frm.doc.centre_jurisdiction_code = r.message['cjc']
				if(r.message['cob'])
                                        frm.doc.constution_of_business = r.message['cob']
				if(r.message['dor'])
                                        frm.doc.date_of_registration = r.message['dor']
				if(r.message['gst_status'])
                                        frm.doc.gstin_status = r.message['gst_status']
				if(r.message['lnob'])
                                        frm.doc.legal_name_of_business = r.message['lnob']
				if(r.message['lud'])
                                        frm.doc.last_updated_date = r.message['lud']
				if(r.message['sj'])
                                        frm.doc.state_jurisdiction = r.message['sj']
				if(r.message['state_code'])
                                        frm.doc.state_code = r.message['state_code']
				if(r.message['nob'])
                                        frm.doc.nature_of_business = String(r.message['nob'])
				if(r.message['cancel_date'])
                                        frm.doc.date_of_cancellation = String(r.message['cancel_date'])
				if(r.message['taxpayer_type'])
                                        frm.doc.taxpayer_type = r.message['taxpayer_type']
				frm.refresh_fields('taxpayer_type','nature_of_business','state_code','state_jurisdiction','last_updated_date','legal_name_of_business','gstin_status','date_of_registration','constution_of_business','centre_jurisdiction_code','centre_jurisdiction','trade_name','address','permanent_address','date_of_cancellation');
			}
		});
	}
});


frappe.ui.form.on('Year', {
	get_retrack_items: function(frm,cdt,cdn) {
		console.log("1")
		debugger;
		var ch = 0;
		const row = locals[cdt][cdn];
		if (frm.doc.retrack_items)
		{
			console.log(frm.doc.retrack_items)
			console.log(frm.doc.retrack_items[0].fiscal_year)
			for (var i=0; i<frm.doc.retrack_items.length;i++)
			{
				if(row.year == frm.doc.retrack_items[i].fiscal_year)
				{
					frappe.throw("Data Already fetched For this Fiscal Year");
					ch = 1;
				}
			}
		}
		if(ch == 0 || !frm.doc.retrack_items)
		{
			frappe.call({
				method: "gst_integerations.api.get_retrack_details",
				args: {
					gstin:frm.doc.gstin,
					year:row.year
				},
				callback: function(r) {
					r.message.forEach(function(element) {
						var c = frm.add_child("retrack_items");
						c.fiscal_year = row.year;
						c.arn_number = element.arn_number;
						c.date_of_filing = element.date_of_filing;
						c.status = element.status;
						c.validity = element.validity;
						c.mode_of_filing = element.mode_of_filing;
						c.return_type = element.return_type;
						c.tax_period = element.tax_period;
						row.status = "Fetched Details";
					});
					refresh_field("retrack_items");
					console.log(frm.doc.retrack_items)
				}
			});
		}
	}
});
