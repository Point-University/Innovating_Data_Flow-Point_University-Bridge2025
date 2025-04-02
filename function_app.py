import logging
import azure.functions as func
from typing import Dict, Annotated
from pydantic import BaseModel, EmailStr, StringConstraints, Field, constr
from softdocs_crm import (
    create_parent_company,
    create_child_org,
    create_contact,
    create_deal
)

logging.basicConfig(
    level=logging.INFO,  # Log INFO and above
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Data validation model
class RequestData(BaseModel):
    Parent_Company_Name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    Company_ID: Annotated[int, Field(gt=0)]
    Child_Company: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    Org_POC_Name: Dict[str, constr(strip_whitespace=True, min_length=1)]
    Org_POC_Email: EmailStr
    Contract_Total: float
    Start_Date: Annotated[str, StringConstraints(strip_whitespace=True)]
    End_Date: Annotated[str, StringConstraints(strip_whitespace=True)]
    Term_in_years: Annotated[int, Field(gt=0)]

@app.function_name(name="Bridge2025")
@app.route(route="Bridge2025")
def main(req: func.HttpRequest) -> func.HttpResponse:
    logger.info('Processing HTTP request.')

    try:
        form_data = req.get_json()
        logger.info("Received data", extra={"data": form_data})

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
