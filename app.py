import os
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, send_file
import io

# Explicitly define absolute paths to ensure compatibility on Render
template_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'templates')
static_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            # Get and sanitize inputs
            revenue = float(request.form["revenue"])
            growth_rate = min(max(float(request.form["growth_rate"]), 0), 1000) / 100
            gross_margin = min(max(float(request.form["gross_margin"]), 0), 100) / 100
            opex_percent = min(max(float(request.form["opex_percent"]), 0), 100) / 100
            capex = float(request.form["capex"])
            tax_rate = min(max(float(request.form["tax_rate"]), 0), 100) / 100
            discount_rate = min(max(float(request.form["discount_rate"]), 0), 100) / 100
            terminal_growth = min(max(float(request.form["terminal_growth"]), 0), 1000) / 100

            years = [2025, 2026, 2027, 2028, 2029]
            revenues, gross_profits, opex_list, ebit_list, taxes, net_incomes = [], [], [], [], [], []
            depreciation = capex * 0.25
            fcfs = []

            for i in range(5):
                revenue = revenue * (1 + growth_rate) if i > 0 else revenue
                gp = revenue * gross_margin
                opex = revenue * opex_percent
                ebit = gp - opex
                tax = ebit * tax_rate
                ni = ebit - tax
                fcf = ni + depreciation - capex

                revenues.append(revenue)
                gross_profits.append(gp)
                opex_list.append(opex)
                ebit_list.append(ebit)
                taxes.append(tax)
                net_incomes.append(ni)
                fcfs.append(fcf)

            income_df = pd.DataFrame({
                "Year": years,
                "Revenue": revenues,
                "Gross Profit": gross_profits,
                "Operating Expenses": opex_list,
                "EBIT": ebit_list,
                "Taxes": taxes,
                "Net Income": net_incomes
            })

            cashflow_df = pd.DataFrame({
                "Year": years,
                "Net Income": net_incomes,
                "Depreciation": [depreciation] * 5,
                "CapEx": [capex] * 5,
                "Free Cash Flow": fcfs
            })

            discounted_fcfs = [fcfs[i] / ((1 + discount_rate) ** (i + 1)) for i in range(5)]
            terminal_value = (fcfs[-1] * (1 + terminal_growth)) / (discount_rate - terminal_growth)
            discounted_terminal = terminal_value / ((1 + discount_rate) ** 5)
            firm_value = sum(discounted_fcfs) + discounted_terminal

            dcf_df = pd.DataFrame({
                "Year": years,
                "Free Cash Flow": fcfs,
                "Discounted FCF": discounted_fcfs
            })

            income_table = income_df.to_html(index=False, classes="table", float_format='{:,.2f}'.format)
            cashflow_table = cashflow_df.to_html(index=False, classes="table", float_format='{:,.2f}'.format)
            dcf_table = dcf_df.to_html(index=False, classes="table", float_format='{:,.2f}'.format)
            firm_value_fmt = f"${firm_value:,.2f}"

            if "download" in request.form:
                excel_file = io.BytesIO()
                with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                    income_df.to_excel(writer, index=False, sheet_name="Income Statement")
                    cashflow_df.to_excel(writer, index=False, sheet_name="Cash Flow")
                    dcf_df.to_excel(writer, index=False, sheet_name="DCF Summary")
                excel_file.seek(0)
                return send_file(
                    excel_file,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name='financial_model.xlsx'
                )

            return render_template("response.html",
                                   income_table=income_table,
                                   cashflow_table=cashflow_table,
                                   dcf_table=dcf_table,
                                   firm_value=firm_value_fmt,
                                   request=request)

        except Exception as e:
            return f"Error processing form: {e}"

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
