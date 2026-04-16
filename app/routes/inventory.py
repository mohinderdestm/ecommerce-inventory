from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.inventory_schema import InventoryCreate
from app.repositories.inventory_repository import InventoryRepository
from app.services.inventory_service import InventoryService
from app.core.database import get_db
from app.core.dependencies import required_roles

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.post("/move")
async def move_inventory(
    payload: InventoryCreate,
    db=Depends(get_db),
    user=Depends(required_roles(["admin", "inventory_manager"]))
):
    service = InventoryService(InventoryRepository(db))

    # ✅ Basic validation
    if payload.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be greater than 0"
        )

    try:
        result = await service.move_stock(payload, user)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory not found or insufficient stock"
            )

        return {
            "message": "Stock moved successfully",
            "data": result
        }

    except HTTPException:
        # ✅ re-raise known HTTP errors
        raise

    except ValueError as e:
        # ✅ business logic errors from service
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        #  unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong: {str(e)}"
        )
        
@router.get("/history")
async def get_inventory_history(
    db=Depends(get_db),
    user=Depends(required_roles(["admin", "inventory_manager"]))
):
    movements = db["inventory_movements"]

    data = await movements.find().sort("timestamp", -1).to_list(100)

    result = []
    for m in data:
        result.append({
            "product_name": m.get("product_name"),
            "warehouse_name": m.get("warehouse_name"),
            "movement_type": m.get("movement_type"),
            "quantity": m.get("quantity"),
            "remarks": m.get("remarks"),
            "timestamp": m.get("timestamp")
        })

    return result
   
