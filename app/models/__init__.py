"""Import every model so Base.metadata is complete for Alembic autogenerate."""
from app.auth.models import AuditLog, Role, SystemUser  # noqa: F401
from app.models.assessment import TaxAssessment, TaxPayment  # noqa: F401
from app.models.clearance import ProvincialSoilDepletionTaxClearance  # noqa: F401
from app.models.enforcement import PenaltyOrAdministrativeSanction, Violation  # noqa: F401
from app.models.mining import (  # noqa: F401
    ExtractionRecord,
    ExtractionSite,
    Mineral,
    MiningOperation,
    MiningOperationType,
    PermitAuthority,
    mining_operation_extraction_site,
    mining_operation_mineral,
)
from app.models.monitoring import (  # noqa: F401
    AnnualCollectionReport,
    BooksExaminationRecord,
    NationalAgency,
    NationalAgencyDocument,
    ProvincialMonitoringRecord,
    ProvincialOffice,
)
from app.models.remedy import RemedyType, TaxpayerRemedy  # noqa: F401
from app.models.shipment import DocumentType, Shipment, ShipmentDocument  # noqa: F401
from app.models.tax_return import ReturnShipment, SoilDepletionTaxReturn  # noqa: F401
from app.models.taxpayer import Taxpayer  # noqa: F401
