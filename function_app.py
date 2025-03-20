import logging
import azure.functions as func
from softdocs_crm import (
    create_parent_company,
    create_child_org,
    create_contact,
    create_deal
)

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="Bridge2025")
def Bridge2025(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing HTTP request.')

    try:
        form_data = req.get_json()

        parent_company = create_parent_company(form_data["Parent Company Name"], form_data["Company ID"])
        create_child_org(form_data['Child Company'], parent_company['id'])
        create_contact(
            form_data['Org POC Name']['first'],
            form_data['Org POC Name']['last'],
            form_data['Org POC Email'],
            form_data['Parent Company Name'],
            parent_company['id']
        )
        deal = create_deal(
            form_data['Parent Company Name'],
            form_data['Contract Total'],
            form_data['Start Date'],
            form_data['End Date'],
            form_data['Term (in years)'],
            parent_company['id']
        )

        return func.HttpResponse(f"Deal {deal['id']} created successfully", status_code=200)

    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
