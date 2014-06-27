<html>

<head>
	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
	<style type="text/css">
    ${css}

    img.logo {
    width: auto;
    height: 2cm;
    }

    /* gangam my style */
    section {
    margin-bottom: 2em;
    }

    .label {
    font-weight: bold;
    font-size: 1.4em;
    }

    .address {
        font-size: 1em;
    }
    .address tr td:first-child{
        color: #585858;
    }

/*    .list_table tbody {
        font-size: 2em !important;
    }
*/
    .align-left {
        text-align: left !important;
    }

    .align-right {
        text-align: right !important;
    }

    .no-border {
        border-style: none !important;
    }

    th {
        text-align: left;
    }

    tbody {
        vertical-align: text-top;
    }

    thead {
        border-top: 2pt solid black;
        border-bottom: 2pt solid black;
        background-color: #F8F8F8;
    }

    body {
        background-color: white;
    }

    </style>
</head>

<body>
%for inv in objects:
    <%
    setLang(inv.partner_id.lang)

    address = [
        inv.partner_id.city,
        inv.partner_id.street,
        inv.partner_id.street2,
        inv.partner_id.zip
    ]
    customer_address = []
    for item in address:
        if item:
            customer_address.append(item)
    customer_address = ', '.join(customer_address)
    %>
    %if inv.company_id.logo:
    <section>
     <img src='${"data:image/gif;base64," + inv.company_id.logo}' class='logo'/>
    </section>
    %endif

    <section>
        <div style='float: left'>
        	<span class='label'>${inv.partner_id.name}</span><br/>
            <span>${customer_address}</span>
        </div>
        <div style='float: right'>
            <span class='label'>Rēķins Nr. ${inv.number}</span><br/>
            <span style='float: right'>${inv.date_invoice}</span>
        </div>
        <div style='clear: both'>
    </section>
    <section>

    	<table class="address" width="100%">
    	    <tr>
        		<td>Saņēmēja rekvizīti:</td>
        		<td></td>
    	    </tr>
    	    <tr>
        		<td>Nosaukums:</td>
        		<td>${inv.partner_id.name}</td>
    	    </tr>
    	    <tr>
        		<td>PVN reģistrācijas Nr.:</td>
        		<td>${inv.partner_id.vat or ''}</td>
    	    </tr>
    	    <tr>
        		<td>Adrese:</td>
        		<td>${customer_address or ''}</td>
    	    </tr>
    	    <tr>
        		<td>Norēķinu konts:</td>
            %if inv.partner_id.bank_ids:
                %for b in inv.partner_id.bank_ids:
        		<td>${b.acc_number}, ${b.bank_name}</td>
            </tr>
            <tr>
            <td></td>
            %endfor
            %endif
    		<td></td>
    	    </tr>
            <tr>
                <td>&nbsp;</td>
                <td>&nbsp;</td>
            </tr>
    	    <tr>
        		<td>Apmaksas termiņš:</td>
        		<td>${inv.date_due or inv.date_invoice or ''}</td>
    	    </tr>
    	</table>
    </section>
    <section>
	<table class="list_table" width="100%">
	    <thead>
            <tr style='text-align:right'>
                <th>Nr.</th>
                <th class="description" width="45%">Nosaukums</th>
                <th>Mērv.</th>
                <th class='align-right'>Daudzums</th>
                <th class='align-right'>Cena, ${inv.currency_id.name}</th>
                <th class='align-right'>Summa, ${inv.currency_id.name}</th>
            </tr>
        </thead>

        <tbody>
        <% seq = 0 %>
        %for line in inv.invoice_line :
        <% seq += 1 %>
            <tr>
                <td class='align-left'>${seq}.</td>
                <td class='align-left'>${line.name}</td>
                <td>${line.uos_id.name or ''}</td>
                <td class='align-right'>${line.quantity}</td>
                <td class='align-right'>${formatLang(line.price_unit)}</td>
                <td class='align-right'>${formatLang(line.price_subtotal)}</td>
            </tr>
        %endfor
            <tr style='border-top: 2pt solid black'>
                <td colspan="2" class='align-left'>Kopā:</td>
                <td colspan="3" class='align-left'></td>
                <td class='numbers align-right'>${formatLang(inv.amount_untaxed)}</td>
            </tr>
            %if inv.tax_line:
            %for tax in inv.tax_line:
            <tr>
                <td colspan="2" style='align-left'>${tax.name}</td>
                <td colspan="3" style='align-right'></td>
                <td class='numbers align-right'>${formatLang(tax.amount)}</td>
            </tr>
            %endfor
            %endif
            %if not inv.tax_line:
            <tr>
                <td colspan="2" class='align-left no-border'>Nodokļi:</td>
                <td colspan="3" class='align-right no-border'></td>
                <td class='numbers align-right no-border '>${formatLang(inv.amount_tax)}</td>
            </tr>
            %endif
            <tr>
                <td colspan="2" class='align-left no-border label'><strong>Rēķina summa:</strong></td>
                <td colspan="3" class='align-right no-border'></td>
                <td class='numbers align-right label no-border '><b>${formatLang(inv.amount_total)}</b></td>
            </tr>
            <tr>
                <td colspan="6" class='align-right no-border no-border '>Summa vārdiem: ${helper.verbose_num_lv(inv.amount_total, inv.currency_id.name)}</td>
            </tr>
	    </tbody>
	</table>
    </section>

    <div>
	    <span style="color: #585858">Piegādātāja rekvizīti:</span><br/>
	    <span class='label'>${inv.company_id.name}</span><br/>
	    Vienotais reģistrācijas numurs: <strong>${inv.company_id.company_registry or '______________'}</strong><br/>PVN reģistrācijas Nr.: <strong>${inv.company_id.vat or '______________'}</strong><br/>
        <%
            company = inv.user_id.company_id
            address = [
                company.city,
                company.street,
                company.street2,
                company.zip
            ]

            company_address = []
            for item in address:
                if item:
                    company_address.append(item)
            company_address = ', '.join(company_address)
        %>
	    Adrese: ${company_address or ''}<br/>
	    Norēķinu konts:
	    %if inv.company_id.bank_ids:
		%for b in inv.company_id.bank_ids:
		    <strong>${b.acc_number}</strong>, ${b.bank_name}, bankas kods ${b.bank_bic}
		%endfor
	    %endif

	    <p>Apmaksai rēķina summa jāpārskaita uz šajā dokumentā minēto piegādātāja norēķinu kontu.<br/>Maksājuma mērķī lūdzam norādīt rēķina numuru.</p>

	    <p>Saskaņā ar Likuma "Par grāmatvedību" 7.1 pantu šis rēķins ir sagatavots elektroniski un ir derigs bez paraksta un zīmoga.</p>
	</table>

	<p style="page-break-after:always"></p>

	%endfor
</body>

</html>
