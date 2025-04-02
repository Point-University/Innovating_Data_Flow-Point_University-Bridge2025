import logging
import azure.functions as func
from typing import Dict, Annotated
from pydantic import BaseModel, EmailStr, StringConstraints, Field
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
    Org_POC_Name: Dict[Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]]
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

        # Validate input
        try:
            validated_data = RequestData(**form_data)
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return func.HttpResponse(f"Validation error: {e}", status_code=400)

        # Step 1: Create Parent Company
        try:
            parent_company = create_parent_company(validated_data.Parent_Company_Name, validated_data.Company_ID)
            logger.info(f"Parent company created: {parent_company}")
        except Exception as e:
            logger.error(f"Failed to create parent company: {e}")
            return func.HttpResponse(f"Error creating parent company: {e}", status_code=500)

        # Step 2: Create Child Organization
        try:
            create_child_org(validated_data.Child_Company, parent_company["id"])
            logger.info("Child organization created successfully")
        except Exception as e:
            logger.error(f"Failed to create child organization: {e}")
            return func.HttpResponse(f"Error creating child organization: {e}", status_code=500)

        # Step 3: Create Contact
        try:
            create_contact(
                validated_data.Org_POC_Name["first"],
                validated_data.Org_POC_Name["last"],
                validated_data.Org_POC_Email,
                validated_data.Parent_Company_Name,
                parent_company["id"]
            )
            logger.info("Contact created successfully")
        except Exception as e:
            logger.error(f"Failed to create contact: {e}")
            return func.HttpResponse(f"Error creating contact: {e}", status_code=500)

        # Step 4: Create Deal
        try:
            deal = create_deal(
                validated_data.Parent_Company_Name,
                validated_data.Contract_Total,
                validated_data.Start_Date,
                validated_data.End_Date,
                validated_data.Term_in_years,
                parent_company["id"]
            )
            logger.info(f"Deal {deal['id']} created successfully")
            return func.HttpResponse(f"Deal {deal['id']} created successfully", status_code=200)
        except Exception as e:
            logger.error(f"Failed to create deal: {e}")
            return func.HttpResponse(f"Error creating deal: {e}", status_code=500)

    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
